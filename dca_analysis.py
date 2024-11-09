import random
import multiprocessing
from datetime import timedelta
from functools import partial
from typing import Dict

import pandas as pd

from dca_core import calculate_dca_metrics


def run_single_test(test_num: int, asset_data: pd.DataFrame, params: Dict) -> Dict:
    """Run a single random test"""
    start_date = params["start_date"]
    end_date = params["end_date"]
    total_period = end_date - start_date
    
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
    metrics = calculate_dca_metrics(asset_data, params["initial_investment"], 
                                  params["periodic_investment"], params["periodicity"], 
                                  test_end)

    # Return metrics for table
    return {
        "test_num": test_num + 1,
        "start_date": test_start.strftime("%Y-%m-%d"),
        "end_date": test_end.strftime("%Y-%m-%d"),
        "final_investment": metrics["final_investment"],
        "final_value": metrics["final_value"],
        "absolute_gain": metrics["absolute_gain"],
        "total_units": metrics["total_units"],
        "percentage_gain": metrics["percentage_gain"],
        "monthly_gain": metrics["monthly_gain"],
        "price_drawdown": metrics["price_drawdown"],
        "value_drawdown": metrics["value_drawdown"],
        "buy_hold_gain": metrics["buy_hold_gain"],
        "buy_hold_monthly": metrics["buy_hold_monthly"]
    }


def run_randomized_tests(asset_data: Dict[str, pd.DataFrame], params: Dict, num_tests: int) -> Dict[str, Dict]:
    """Run multiple random date range tests in parallel and return average metrics"""
    results_by_asset = {}
    
    # Get number of CPU cores
    num_cores = multiprocessing.cpu_count()
    
    for asset, df in asset_data.items():
        # Create pool of workers
        with multiprocessing.Pool(num_cores) as pool:
            # Create partial function with fixed arguments
            test_func = partial(run_single_test, asset_data=df, params=params)
            
            # Run tests in parallel
            all_metrics = pool.map(test_func, range(num_tests))

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
            "all_runs": all_metrics
        }

        results_by_asset[asset] = avg_metrics

    return results_by_asset
