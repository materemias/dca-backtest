import multiprocessing
import random
from functools import partial
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import streamlit as st

from dca_core import compute_dca_metrics, resample_price_data


def generate_random_date_ranges(df: pd.DataFrame, periodicity: str, num_tests: int) -> List[Tuple[pd.Timestamp, pd.Timestamp]]:
    """Generate random date ranges for testing."""
    min_periods = {"Daily": 365, "Weekly": 52, "Monthly": 12}[periodicity]
    dates = df["date"].tolist()

    if len(dates) < min_periods + 1:
        st.warning("Not enough data to generate date ranges.")
        return []

    max_start_idx = len(dates) - min_periods - 1
    unique_ranges = set()

    # Try to generate requested number of unique ranges
    attempts = num_tests * 3
    while len(unique_ranges) < num_tests and attempts > 0:
        start_idx = random.randint(0, max_start_idx)
        min_end_idx = start_idx + min_periods

        if min_end_idx < len(dates):
            end_idx = random.randint(min_end_idx, len(dates) - 1)
            unique_ranges.add((dates[start_idx], dates[end_idx]))

        attempts -= 1

    if len(unique_ranges) < num_tests:
        st.warning(f"Generated {len(unique_ranges)} of {num_tests} requested ranges")

    return list(unique_ranges)


def run_single_test(date_range: Tuple[pd.Timestamp, pd.Timestamp], rdf: pd.DataFrame, initial_investment: float, periodic_investment: float) -> Dict:
    """Run a single random test against an already-resampled price frame."""
    start, end = date_range
    sl = rdf[(rdf["date"] >= start) & (rdf["date"] <= end)]
    metrics = compute_dca_metrics(sl["date"].values, sl["Close"].values, initial_investment, periodic_investment, want_snapshots=False)

    return metrics | {"start_date": start.strftime("%Y-%m-%d"), "end_date": end.strftime("%Y-%m-%d")}


def run_randomized_tests(asset_data: Dict[str, pd.DataFrame], params: Dict, num_tests: int) -> Dict[str, Dict]:
    """Run multiple random date range tests in parallel."""
    # Resample each asset once; the random ranges are picked from this same grid, so each
    # test is just a slice of the pre-resampled series (no per-test resample).
    resampled = {asset: resample_price_data(df, params["periodicity"]).dropna(subset=["Close"]) for asset, df in asset_data.items()}
    random_ranges = generate_random_date_ranges(next(iter(resampled.values())), params["periodicity"], num_tests)
    if not random_ranges:
        return {}

    initial, periodic = params["initial_investment"], params["periodic_investment"]
    chunksize = max(1, len(random_ranges) // (multiprocessing.cpu_count() * 4))

    results = {}
    with multiprocessing.Pool() as pool:
        for asset, rdf in resampled.items():
            worker = partial(run_single_test, rdf=rdf, initial_investment=initial, periodic_investment=periodic)
            metrics = pool.map(worker, random_ranges, chunksize=chunksize)

            # Report the median (robust central tendency across heterogeneous horizons),
            # plus a 5-95% range for the key return/risk metrics, and keep all runs.
            metric_keys = [k for k in metrics[0] if k not in ("start_date", "end_date")]
            agg = {k: round(float(np.median([m[k] for m in metrics])), 2) for k in metric_keys}
            percentiles = {k: [round(float(np.percentile([m[k] for m in metrics], p)), 2) for p in (5, 95)] for k in ("percentage_gain", "buy_hold_gain", "value_drawdown")}
            results[asset] = agg | {"percentiles": percentiles, "all_runs": metrics}

    return results
