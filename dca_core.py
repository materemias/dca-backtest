from datetime import date
from typing import Dict

import pandas as pd


def resample_price_data(df: pd.DataFrame, periodicity: str) -> pd.DataFrame:
    """Resample price data according to investment frequency"""
    # Convert date column to datetime if it's not already
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # Set index and resample
    df = df.set_index("date")
    freq_map = {"Daily": "D", "Weekly": "W", "Monthly": "ME"}

    # First forward fill any gaps in the original data
    df["Close"] = df["Close"].ffill()

    # Resample with last value for Close and sum for Volume
    resampled = (
        df.resample(freq_map[periodicity])
        .agg(
            {
                "Close": "last",  # Take last value in period
                "Volume": "sum",
            }
        )
        .reset_index()
    )

    # Forward fill any remaining nulls after resampling
    resampled["Close"] = resampled["Close"].ffill()

    return resampled


def _calculate_monthly_gain(final_value: float, initial_value: float, days_elapsed: float) -> float:
    """Helper to calculate monthly gain percentage"""
    months = days_elapsed / 30.44
    return round((((final_value / initial_value) ** (1 / months)) - 1) * 100, 2)


def _calculate_drawdown(series: pd.Series) -> float:
    """Generic drawdown calculator"""
    if series.empty:
        return 0.0
    running_max = series.expanding().max()
    drawdown = ((series - running_max) / running_max) * 100
    return round(abs(drawdown.min()), 2)


def calculate_price_drawdown(df: pd.DataFrame) -> float:
    return _calculate_drawdown(df["Close"])


def calculate_value_drawdown(snapshots: pd.DataFrame) -> float:
    return _calculate_drawdown(snapshots["total_value"])


def calculate_dca_metrics(df: pd.DataFrame, initial_investment: float, periodic_investment: float, periodicity: str, end_date: date) -> Dict:
    """Calculate DCA investment metrics"""
    df = df[df["date"] <= end_date].copy()
    resampled_df = resample_price_data(df, periodicity).dropna(subset=["Close"])

    if resampled_df.empty:
        return {
            k: 0
            for k in ["final_investment", "final_value", "absolute_gain", "percentage_gain", "monthly_gain", "total_units", "price_drawdown", "value_drawdown", "buy_hold_gain", "buy_hold_monthly"]
        } | {"snapshots": pd.DataFrame()}

    # Basic calculations
    num_periods = len(resampled_df)
    prices = resampled_df["Close"]
    final_investment = initial_investment + (periodic_investment * (num_periods - 1))

    # Calculate units and values
    units = [initial_investment / prices.iloc[0]]
    investments = [initial_investment]
    for price in prices.iloc[1:]:
        investments.append(investments[-1] + periodic_investment)
        units.append(units[-1] + periodic_investment / price)
    values = [u * p for u, p in zip(units, prices)]

    # Create snapshots
    snapshots = pd.DataFrame({"date": resampled_df["date"], "total_investment": investments, "total_value": values, "total_units": units, "price": prices})

    # Calculate gains
    days_elapsed = (resampled_df["date"].iloc[-1] - resampled_df["date"].iloc[0]).days
    buy_hold_units = final_investment / prices.iloc[0]
    buy_hold_value = buy_hold_units * prices.iloc[-1]

    return {
        "final_investment": round(final_investment, 2),
        "final_value": round(values[-1], 2),
        "absolute_gain": round(values[-1] - final_investment, 2),
        "percentage_gain": round(((values[-1] / final_investment) - 1) * 100, 2),
        "monthly_gain": _calculate_monthly_gain(values[-1], final_investment, days_elapsed),
        "total_units": round(units[-1], 6),
        "price_drawdown": calculate_price_drawdown(df),
        "value_drawdown": calculate_value_drawdown(snapshots),
        "buy_hold_gain": round(((buy_hold_value / final_investment) - 1) * 100, 2),
        "buy_hold_monthly": _calculate_monthly_gain(buy_hold_value, final_investment, days_elapsed),
        "snapshots": snapshots,
    }


def calculate_multi_asset_dca(asset_data: Dict[str, pd.DataFrame], params: Dict) -> Dict[str, Dict]:
    """Calculate DCA metrics for multiple assets"""
    results = {}

    for asset, df in asset_data.items():
        results[asset] = calculate_dca_metrics(df, params["initial_investment"], params["periodic_investment"], params["periodicity"], params["end_date"])

    return results
