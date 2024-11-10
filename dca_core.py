from datetime import date
from typing import Dict

import pandas as pd

def resample_price_data(df: pd.DataFrame, periodicity: str) -> pd.DataFrame:
    """Resample price data according to investment frequency."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    
    freq_map = {"Daily": "D", "Weekly": "W", "Monthly": "ME"}
    df["Close"] = df["Close"].ffill()
    
    resampled = (df.resample(freq_map[periodicity])
                 .agg({"Close": "last", "Volume": "sum"})
                 .reset_index())
    
    return resampled.ffill()

def calculate_monthly_gain(final_value: float, initial_value: float, days_elapsed: float) -> float:
    """Calculate monthly gain percentage."""
    months = days_elapsed / 30.44
    return round((((final_value / initial_value) ** (1 / months)) - 1) * 100, 2)

def calculate_drawdown(series: pd.Series) -> float:
    """Calculate maximum drawdown percentage."""
    if series.empty:
        return 0.0
    running_max = series.expanding().max()
    drawdown = ((series - running_max) / running_max) * 100
    return abs(round(drawdown.min(), 2))

def calculate_dca_metrics(df: pd.DataFrame, initial_investment: float, 
                        periodic_investment: float, periodicity: str, 
                        end_date: date) -> Dict:
    """Calculate DCA investment metrics."""
    df = resample_price_data(df[df["date"] <= end_date], periodicity).dropna(subset=["Close"])
    
    if df.empty:
        empty_metrics = {
            "final_investment": 0, "final_value": 0, "absolute_gain": 0,
            "percentage_gain": 0, "monthly_gain": 0, "total_units": 0,
            "price_drawdown": 0, "value_drawdown": 0, "buy_hold_gain": 0,
            "buy_hold_monthly": 0, "snapshots": pd.DataFrame()
        }
        return empty_metrics

    num_periods = len(df)
    prices = df["Close"].values
    investments = [initial_investment] + [initial_investment + periodic_investment * i 
                                        for i in range(1, num_periods)]
    
    # Calculate units and values
    units = [initial_investment / prices[0]]
    for price, _ in zip(prices[1:], range(1, num_periods)):
        units.append(units[-1] + periodic_investment / price)
    
    values = [u * p for u, p in zip(units, prices)]
    
    # Create snapshots DataFrame
    snapshots = pd.DataFrame({
        "date": df["date"],
        "total_investment": investments,
        "total_value": values,
        "total_units": units,
        "price": prices
    })
    
    # Calculate metrics
    final_investment = investments[-1]
    final_value = values[-1]
    days_elapsed = (df["date"].iloc[-1] - df["date"].iloc[0]).days
    
    buy_hold_units = final_investment / prices[0]
    buy_hold_value = buy_hold_units * prices[-1]
    
    return {
        "final_investment": round(final_investment, 2),
        "final_value": round(final_value, 2),
        "absolute_gain": round(final_value - final_investment, 2),
        "percentage_gain": round(((final_value / final_investment) - 1) * 100, 2),
        "monthly_gain": calculate_monthly_gain(final_value, final_investment, days_elapsed),
        "total_units": round(units[-1], 6),
        "price_drawdown": calculate_drawdown(df["Close"]),
        "value_drawdown": calculate_drawdown(snapshots["total_value"]),
        "buy_hold_gain": round(((buy_hold_value / final_investment) - 1) * 100, 2),
        "buy_hold_monthly": calculate_monthly_gain(buy_hold_value, final_investment, days_elapsed),
        "snapshots": snapshots,
    }

def calculate_multi_asset_dca(asset_data: Dict[str, pd.DataFrame], params: Dict) -> Dict[str, Dict]:
    """Calculate DCA metrics for multiple assets."""
    return {
        asset: calculate_dca_metrics(
            df, params["initial_investment"], 
            params["periodic_investment"], 
            params["periodicity"], 
            params["end_date"]
        )
        for asset, df in asset_data.items()
    }
