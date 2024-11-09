from typing import Dict
from datetime import date, timedelta
import random

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


def calculate_price_drawdown(df: pd.DataFrame) -> float:
    """Calculate the maximum drawdown percentage from peak price."""
    if df.empty:
        return 0.0
        
    # Calculate running maximum
    running_max = df['Close'].expanding().max()
    # Calculate drawdown percentage
    drawdown = ((df['Close'] - running_max) / running_max) * 100
    # Get the maximum drawdown
    max_drawdown = drawdown.min()
    
    return round(abs(max_drawdown), 2)

def calculate_value_drawdown(snapshots: pd.DataFrame) -> float:
    """Calculate the maximum drawdown percentage from peak portfolio value."""
    if snapshots.empty:
        return 0.0
        
    # Calculate running maximum of total_value
    running_max = snapshots['total_value'].expanding().max()
    # Calculate drawdown percentage
    drawdown = ((snapshots['total_value'] - running_max) / running_max) * 100
    # Get the maximum drawdown
    max_drawdown = drawdown.min()
    
    return round(abs(max_drawdown), 2)

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
            "price_drawdown": 0,
            "value_drawdown": 0,
            "buy_hold_gain": 0,
            "buy_hold_monthly": 0,
            "snapshots": pd.DataFrame(columns=["date", "total_investment", "total_value", "total_units", "price"]),
        }

    # Calculate total investment
    final_investment = initial_investment + (periodic_investment * (num_periods - 1))

    # Calculate buy & hold metrics
    total_investment_amount = final_investment
    initial_price = resampled_df["Close"].iloc[0]
    final_price = resampled_df["Close"].iloc[-1]
    buy_hold_units = total_investment_amount / initial_price
    buy_hold_value = buy_hold_units * final_price
    buy_hold_gain = ((buy_hold_value / total_investment_amount) - 1) * 100
    
    # Calculate buy & hold monthly gain
    months_elapsed = (resampled_df["date"].iloc[-1] - resampled_df["date"].iloc[0]).days / 30.44
    buy_hold_monthly = (((buy_hold_value / total_investment_amount) ** (1 / months_elapsed)) - 1) * 100

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

    # Create snapshots dataframe
    snapshots = pd.DataFrame({
        "date": resampled_df["date"], 
        "total_investment": investment_snapshots, 
        "total_value": value_snapshots, 
        "total_units": cumulative_units, 
        "price": resampled_df["Close"]
    })

    # Calculate final metrics
    final_value = value_snapshots[-1]
    absolute_gain = final_value - final_investment
    percentage_gain = (absolute_gain / final_investment) * 100

    # Calculate average monthly gain
    months_elapsed = (resampled_df["date"].iloc[-1] - resampled_df["date"].iloc[0]).days / 30.44
    monthly_gain = (((final_value / final_investment) ** (1 / months_elapsed)) - 1) * 100

    # Calculate both types of drawdown
    price_drawdown = calculate_price_drawdown(df)
    value_drawdown = calculate_value_drawdown(snapshots)

    return {
        "final_investment": round(final_investment, 2),
        "final_value": round(final_value, 2),
        "absolute_gain": round(absolute_gain, 2),
        "percentage_gain": round(percentage_gain, 2),
        "monthly_gain": round(monthly_gain, 2),
        "total_units": round(cumulative_units[-1], 6),
        "price_drawdown": price_drawdown,  # Price drawdown
        "value_drawdown": value_drawdown,  # Portfolio value drawdown
        "buy_hold_gain": round(buy_hold_gain, 2),
        "buy_hold_monthly": round(buy_hold_monthly, 2),
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

def run_randomized_tests(asset_data: Dict[str, pd.DataFrame], params: Dict, num_tests: int) -> Dict[str, Dict]:
    """Run multiple random date range tests and return average metrics"""
    start_date = params["start_date"]
    end_date = params["end_date"]
    min_period = timedelta(days=365)  # Minimum 1 year period
    total_period = end_date - start_date
    
    results_by_asset = {}
    
    for asset, df in asset_data.items():
        all_metrics = []
        
        for test_num in range(num_tests):
            # Generate random start and end dates
            test_period = random.uniform(365, (total_period.days - 1))
            random_start_offset = random.uniform(0, total_period.days - test_period)
            
            test_start = start_date + timedelta(days=random_start_offset)
            test_end = test_start + timedelta(days=test_period)
            
            # Create test parameters
            test_params = params.copy()
            test_params["start_date"] = test_start
            test_params["end_date"] = test_end
            
            # Calculate metrics for this test
            metrics = calculate_dca_metrics(df, params["initial_investment"], 
                                         params["periodic_investment"], 
                                         params["periodicity"],
                                         test_end)
            
            # Add test number and dates to metrics
            metrics_for_table = {
                "test_num": test_num + 1,
                "start_date": test_start.strftime("%Y-%m-%d"),
                "end_date": test_end.strftime("%Y-%m-%d"),
                "final_investment": metrics["final_investment"],
                "final_value": metrics["final_value"],
                "absolute_gain": metrics["absolute_gain"],
                "percentage_gain": metrics["percentage_gain"],
                "monthly_gain": metrics["monthly_gain"],
                "price_drawdown": metrics["price_drawdown"],
                "value_drawdown": metrics["value_drawdown"],
                "buy_hold_gain": metrics["buy_hold_gain"],
                "buy_hold_monthly": metrics["buy_hold_monthly"]
            }
            all_metrics.append(metrics_for_table)
        
        # Calculate averages
        avg_metrics = {
            "final_investment": sum(m["final_investment"] for m in all_metrics) / num_tests,
            "final_value": sum(m["final_value"] for m in all_metrics) / num_tests,
            "absolute_gain": sum(m["absolute_gain"] for m in all_metrics) / num_tests,
            "percentage_gain": sum(m["percentage_gain"] for m in all_metrics) / num_tests,
            "monthly_gain": sum(m["monthly_gain"] for m in all_metrics) / num_tests,
            "price_drawdown": sum(m["price_drawdown"] for m in all_metrics) / num_tests,
            "value_drawdown": sum(m["value_drawdown"] for m in all_metrics) / num_tests,
            "buy_hold_gain": sum(m["buy_hold_gain"] for m in all_metrics) / num_tests,
            "buy_hold_monthly": sum(m["buy_hold_monthly"] for m in all_metrics) / num_tests,
            "all_runs": all_metrics  # Store all individual runs
        }
        
        results_by_asset[asset] = avg_metrics
    
    return results_by_asset
