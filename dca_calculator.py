from typing import Dict
from datetime import date

import pandas as pd


def resample_price_data(df: pd.DataFrame, periodicity: str) -> pd.DataFrame:
    """Resample price data according to investment frequency"""
    # Convert date column to datetime if it's not already
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # Set index and resample
    df = df.set_index("date")
    freq_map = {"Daily": "D", "Weekly": "W", "Monthly": "ME"}

    return df.resample(freq_map[periodicity]).agg({"Close": "last", "Volume": "sum"}).reset_index()


def calculate_dca_metrics(df: pd.DataFrame, initial_investment: float, periodic_investment: float, periodicity: str, end_date: date) -> Dict:
    """Calculate DCA investment metrics"""

    # Filter data up to end_date first
    df = df[df["date"] <= end_date].copy()

    # Resample data according to investment frequency
    resampled_df = resample_price_data(df, periodicity)
    
    # Remove rows with NaN prices
    resampled_df = resampled_df.dropna(subset=['Close'])

    # Calculate number of periods
    num_periods = len(resampled_df)
    
    if num_periods == 0:
        return {
            "final_investment": 0,
            "final_value": 0,
            "absolute_gain": 0,
            "percentage_gain": 0,
            "monthly_gain": 0,
            "total_units": 0,
            "snapshots": pd.DataFrame(columns=["date", "total_investment", "total_value", "total_units", "price"]),
        }

    # Calculate total investment
    final_investment = initial_investment + (periodic_investment * (num_periods - 1))

    # Initialize lists to track investments and values over time
    investment_snapshots = []
    value_snapshots = []
    cumulative_units = []
    running_investment = initial_investment

    # Calculate initial purchase
    initial_units = initial_investment / resampled_df["Close"].iloc[0]
    cumulative_units.append(initial_units)
    investment_snapshots.append(running_investment)
    value_snapshots.append(initial_units * resampled_df["Close"].iloc[0])

    # Calculate periodic purchases
    for i, price in enumerate(resampled_df["Close"].iloc[1:], 1):
        running_investment += periodic_investment
        new_units = periodic_investment / price
        total_units_so_far = cumulative_units[-1] + new_units

        cumulative_units.append(total_units_so_far)
        investment_snapshots.append(running_investment)
        value_snapshots.append(total_units_so_far * price)

    # Calculate final metrics
    final_value = value_snapshots[-1]
    absolute_gain = final_value - final_investment
    percentage_gain = (absolute_gain / final_investment) * 100

    # Calculate average monthly gain
    months_elapsed = (resampled_df["date"].iloc[-1] - resampled_df["date"].iloc[0]).days / 30.44
    monthly_gain = (((final_value / final_investment) ** (1 / months_elapsed)) - 1) * 100

    # Create snapshots dataframe
    snapshots = pd.DataFrame({
        "date": resampled_df["date"], 
        "total_investment": investment_snapshots, 
        "total_value": value_snapshots, 
        "total_units": cumulative_units, 
        "price": resampled_df["Close"]
    })

    return {
        "final_investment": round(final_investment, 2),
        "final_value": round(final_value, 2),
        "absolute_gain": round(absolute_gain, 2),
        "percentage_gain": round(percentage_gain, 2),
        "monthly_gain": round(monthly_gain, 2),
        "total_units": round(cumulative_units[-1], 6),
        "snapshots": snapshots,
    }


def calculate_multi_asset_dca(asset_data: Dict[str, pd.DataFrame], params: Dict) -> Dict[str, Dict]:
    """Calculate DCA metrics for multiple assets"""
    results = {}

    for asset, df in asset_data.items():
        results[asset] = calculate_dca_metrics(
            df, 
            params["initial_investment"], 
            params["periodic_investment"], 
            params["periodicity"],
            params["end_date"]
        )

    return results
