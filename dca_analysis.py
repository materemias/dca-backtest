import multiprocessing
import random
from datetime import timedelta
from functools import partial
from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st

from dca_core import calculate_dca_metrics, resample_price_data


def run_single_random_test(date_range: Tuple[pd.Timestamp, pd.Timestamp], df: pd.DataFrame, params: Dict) -> Dict:
    """Run a single random test with given date range"""
    test_params = params.copy()
    test_params["start_date"] = date_range[0].date()  # Convert to date object
    test_params["end_date"] = date_range[1].date()    # Convert to date object
    
    metrics = calculate_dca_metrics(df, params["initial_investment"], 
                                  params["periodic_investment"], 
                                  params["periodicity"], 
                                  test_params["end_date"])  # Now using date object
    
    return {
        "start_date": date_range[0].strftime("%Y-%m-%d"),
        "end_date": date_range[1].strftime("%Y-%m-%d"),
        "final_investment": metrics["final_investment"],
        "final_value": metrics["final_value"],
        "absolute_gain": metrics["absolute_gain"],
        "total_units": metrics["total_units"],
        "percentage_gain": metrics["percentage_gain"],
        "monthly_gain": metrics["monthly_gain"],
        "price_drawdown": metrics["price_drawdown"],
        "value_drawdown": metrics["value_drawdown"],
        "buy_hold_gain": metrics["buy_hold_gain"],
        "buy_hold_monthly": metrics["buy_hold_monthly"],
    }


def generate_random_date_ranges(asset_data: Dict[str, pd.DataFrame], params: Dict, num_tests: int) -> List[Tuple[pd.Timestamp, pd.Timestamp]]:
    """
    Generate random date ranges using exact investment dates based on frequency.
    Only picks valid investment dates (e.g., month-end for monthly frequency).
    """
    # Get first asset's data and resample it to get valid investment dates
    sample_df = next(iter(asset_data.values()))
    resampled_df = resample_price_data(sample_df, params["periodicity"])
    
    # Get list of valid investment dates
    investment_dates = resampled_df["date"].tolist()
    
    # Minimum periods for 1 year based on frequency
    min_periods = {
        "Daily": 365,
        "Weekly": 52,
        "Monthly": 12
    }[params["periodicity"]]
    
    unique_ranges = set()
    attempts = 0
    max_attempts = len(investment_dates) * 2  # Reasonable limit for attempts
    
    while len(unique_ranges) < num_tests and attempts < max_attempts:
        # Ensure enough remaining periods for minimum length
        max_start_idx = len(investment_dates) - min_periods
        if max_start_idx < 1:
            break
            
        # Pick random start date from valid investment dates
        start_idx = random.randint(0, max_start_idx)
        start_date = investment_dates[start_idx]
        
        # Pick random end date ensuring minimum period length
        min_end_idx = start_idx + min_periods
        if min_end_idx >= len(investment_dates):
            break
            
        end_idx = random.randint(min_end_idx, len(investment_dates) - 1)
        end_date = investment_dates[end_idx]
        
        # Add range if unique
        date_range = (start_date, end_date)
        if date_range not in unique_ranges:
            unique_ranges.add(date_range)
        
        attempts += 1
        
        # If we can't find more unique combinations, stop
        if attempts >= max_attempts:
            break
    
    if len(unique_ranges) < num_tests:
        st.warning(f"Could only generate {len(unique_ranges)} unique test ranges (requested {num_tests})")
    
    return list(unique_ranges)


def run_randomized_tests(asset_data: Dict[str, pd.DataFrame], params: Dict, num_tests: int) -> Dict[str, Dict]:
    """Run multiple random date range tests in parallel and return average metrics"""
    results_by_asset = {}
    
    # Generate random date ranges
    random_ranges = generate_random_date_ranges(asset_data, params, num_tests)
    
    # Get number of CPU cores
    num_cores = multiprocessing.cpu_count()
    
    for asset, df in asset_data.items():
        # Create pool of workers
        with multiprocessing.Pool(num_cores) as pool:
            # Create partial function with fixed df and params arguments
            test_func = partial(run_single_random_test, df=df, params=params)
            # Run tests in parallel
            all_metrics = pool.map(test_func, random_ranges)
        
        # Calculate averages
        avg_metrics = {
            "final_investment": sum(m["final_investment"] for m in all_metrics) / num_tests,
            "final_value": sum(m["final_value"] for m in all_metrics) / num_tests,
            "absolute_gain": sum(m["absolute_gain"] for m in all_metrics) / num_tests,
            "total_units": sum(m["total_units"] for m in all_metrics) / num_tests,
            "percentage_gain": sum(m["percentage_gain"] for m in all_metrics) / num_tests,
            "monthly_gain": sum(m["monthly_gain"] for m in all_metrics) / num_tests,
            "price_drawdown": sum(m["price_drawdown"] for m in all_metrics) / num_tests,
            "value_drawdown": sum(m["value_drawdown"] for m in all_metrics) / num_tests,
            "buy_hold_gain": sum(m["buy_hold_gain"] for m in all_metrics) / num_tests,
            "buy_hold_monthly": sum(m["buy_hold_monthly"] for m in all_metrics) / num_tests,
            "all_runs": all_metrics,
        }
        
        results_by_asset[asset] = avg_metrics
    
    return results_by_asset
