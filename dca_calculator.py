from typing import Dict
import pandas as pd


def resample_price_data(df: pd.DataFrame, periodicity: str) -> pd.DataFrame:
    """Resample price data according to investment frequency"""
    df = df.set_index("date")
    freq_map = {"Daily": "D", "Weekly": "W", "Monthly": "ME"}
    
    return df.resample(freq_map[periodicity]).agg({
        "Close": "last",
        "Volume": "sum"
    }).reset_index()


def calculate_dca_metrics(df: pd.DataFrame, initial_investment: float, periodic_investment: float, periodicity: str) -> Dict:
    """Calculate DCA investment metrics"""

    # Resample data according to investment frequency
    resampled_df = resample_price_data(df, periodicity)

    # Calculate number of periods
    num_periods = len(resampled_df)

    # Calculate total investment
    total_investment = initial_investment + (periodic_investment * (num_periods - 1))

    # Calculate units bought at each period
    initial_units = initial_investment / resampled_df["Close"].iloc[0]
    periodic_units = [periodic_investment / price for price in resampled_df["Close"].iloc[1:]]
    total_units = initial_units + sum(periodic_units)

    # Calculate final value
    final_price = resampled_df["Close"].iloc[-1]
    final_value = total_units * final_price

    # Calculate gains
    absolute_gain = final_value - total_investment
    percentage_gain = (absolute_gain / total_investment) * 100

    # Calculate average monthly gain
    months_elapsed = (resampled_df["date"].iloc[-1] - resampled_df["date"].iloc[0]).days / 30.44  # Average days per month
    monthly_gain = (((final_value / total_investment) ** (1 / months_elapsed)) - 1) * 100

    return {
        "total_investment": round(total_investment, 2),
        "final_value": round(final_value, 2),
        "absolute_gain": round(absolute_gain, 2),
        "percentage_gain": round(percentage_gain, 2),
        "monthly_gain": round(monthly_gain, 2),
        "total_units": round(total_units, 6),
    }


def calculate_multi_asset_dca(asset_data: Dict[str, pd.DataFrame], params: Dict) -> Dict[str, Dict]:
    """Calculate DCA metrics for multiple assets"""
    results = {}

    for asset, df in asset_data.items():
        results[asset] = calculate_dca_metrics(df, params["initial_investment"], params["periodic_investment"], params["periodicity"])

    return results
