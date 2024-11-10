import multiprocessing
import random
from functools import partial
from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st

from dca_core import calculate_dca_metrics, resample_price_data


def generate_random_date_ranges(asset_data: Dict[str, pd.DataFrame], params: Dict, num_tests: int) -> List[Tuple[pd.Timestamp, pd.Timestamp]]:
    """Generate random date ranges using valid investment dates"""
    df = resample_price_data(next(iter(asset_data.values())), params["periodicity"])
    dates = df["date"].tolist()
    min_periods = {"Daily": 365, "Weekly": 52, "Monthly": 12}[params["periodicity"]]

    if len(dates) < min_periods + 1:
        st.warning("Not enough data to generate date ranges.")
        return []

    max_start_idx = len(dates) - min_periods - 1
    unique_ranges = set()

    for _ in range(num_tests * 3):  # Max attempts
        if len(unique_ranges) >= num_tests:
            break

        start_idx = random.randint(0, max_start_idx)
        min_end_idx = start_idx + min_periods

        if min_end_idx < len(dates):
            end_idx = random.randint(min_end_idx, len(dates) - 1)
            unique_ranges.add((dates[start_idx], dates[end_idx]))

    if len(unique_ranges) < num_tests:
        st.warning(f"Generated {len(unique_ranges)} of {num_tests} requested ranges")
    return list(unique_ranges)


def run_single_random_test(date_range: Tuple[pd.Timestamp, pd.Timestamp], df: pd.DataFrame, params: Dict) -> Dict:
    """Run a single random test"""
    metrics = calculate_dca_metrics(df, params["initial_investment"], params["periodic_investment"], params["periodicity"], date_range[1].date())

    return {k: metrics[k] for k in metrics if k != "snapshots"} | {
        "start_date": date_range[0].strftime("%Y-%m-%d"),
        "end_date": date_range[1].strftime("%Y-%m-%d"),
    }


def run_randomized_tests(asset_data: Dict[str, pd.DataFrame], params: Dict, num_tests: int) -> Dict[str, Dict]:
    """Run multiple random date range tests in parallel"""
    random_ranges = generate_random_date_ranges(asset_data, params, num_tests)
    if not random_ranges:
        return {}

    results = {}
    with multiprocessing.Pool() as pool:
        for asset, df in asset_data.items():
            metrics = pool.map(partial(run_single_random_test, df=df, params=params), random_ranges)

            results[asset] = {k: sum(m[k] for m in metrics) / len(metrics) for k in metrics[0] if k not in ("start_date", "end_date")} | {"all_runs": metrics}

    return results
