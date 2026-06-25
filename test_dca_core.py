"""Self-check for DCA core math. Run: python test_dca_core.py (or pytest)."""
from datetime import date

import pandas as pd

from dca_core import calculate_dca_metrics, calculate_monthly_gain, compute_dca_metrics, resample_price_data, xirr


def _daily(start: str, end: str, price: float = 100.0) -> pd.DataFrame:
    days = pd.bdate_range(start, end)  # business days only
    return pd.DataFrame({"date": [d.date() for d in days], "Close": price, "Volume": 1})


def test_business_day_resample_skips_weekends():
    # 10 business days spanning a weekend -> no Sat/Sun rows, count preserved
    df = pd.DataFrame({"date": [d.date() for d in pd.bdate_range("2022-01-03", periods=10)], "Close": range(100, 110), "Volume": 1})
    out = resample_price_data(df, "Daily")
    assert len(out) == 10, f"expected 10 business days, got {len(out)}"
    assert not any(out["date"].dt.dayofweek >= 5), "weekend rows leaked into Daily resample"


def test_flat_price_zero_gain():
    # Constant price: value always equals money invested -> zero gain
    m = calculate_dca_metrics(_daily("2022-01-01", "2022-06-30"), 100, 100, "Monthly", date(2022, 6, 30))
    assert m["final_value"] == m["final_investment"]
    assert m["percentage_gain"] == 0.0
    assert m["absolute_gain"] == 0.0


def test_start_date_filters_periods():
    # Same data, later start -> fewer contributions -> smaller final_investment
    df = _daily("2022-01-01", "2022-06-30")
    full = calculate_dca_metrics(df, 100, 100, "Monthly", date(2022, 6, 30))
    cut = calculate_dca_metrics(df, 100, 100, "Monthly", date(2022, 6, 30), start_date=date(2022, 4, 1))
    assert cut["final_investment"] < full["final_investment"], "start_date did not trim periods"


def test_zero_investment_no_crash():
    m = calculate_dca_metrics(_daily("2022-01-01", "2022-06-30"), 0, 0, "Monthly", date(2022, 6, 30))
    assert m["percentage_gain"] == 0.0
    assert m["buy_hold_gain"] == 0.0
    assert m["monthly_gain"] == 0.0


def test_monthly_gain_guards():
    assert calculate_monthly_gain(100, 0, 30) == 0.0   # zero base
    assert calculate_monthly_gain(100, 100, 0) == 0.0  # zero elapsed


def test_xirr_lump_sum_matches_cagr():
    # 100 -> 121 over ~2 years is ~10% annual
    rate = xirr([-100, 121], [date(2020, 1, 1), date(2022, 1, 1)])
    assert abs(rate - 0.10) < 2e-3, rate
    # No inflow -> undefined -> 0.0
    assert xirr([-100, -50], [date(2020, 1, 1), date(2021, 1, 1)]) == 0.0


def test_compute_matches_full_calc_on_grid_aligned_window():
    # The fast Monte Carlo path (resample once, slice grid, compute_dca_metrics) must
    # match the original filter-then-resample path for a grid-aligned window.
    days = pd.bdate_range("2018-01-01", "2023-12-31")
    px = [100 + i * 0.05 for i in range(len(days))]
    df = pd.DataFrame({"date": [d.date() for d in days], "Close": px, "Volume": 1})

    grid = resample_price_data(df, "Monthly").dropna(subset=["Close"])
    start, end = grid["date"].iloc[6], grid["date"].iloc[-1]  # grid-aligned bounds
    sl = grid[(grid["date"] >= start) & (grid["date"] <= end)]
    fast = compute_dca_metrics(sl["date"].values, sl["Close"].values, 100, 100, want_snapshots=False)
    full = calculate_dca_metrics(df, 100, 100, "Monthly", end.date(), start_date=start.date())

    for k in ("final_investment", "final_value", "percentage_gain", "monthly_gain", "buy_hold_gain", "value_drawdown"):
        assert fast[k] == full[k], f"{k}: fast={fast[k]} full={full[k]}"


def test_dca_monthly_positive_on_uptrend():
    days = pd.bdate_range("2021-01-01", "2022-12-31")
    df = pd.DataFrame({"date": [d.date() for d in days], "Close": [100 + i * 0.1 for i in range(len(days))], "Volume": 1})
    m = calculate_dca_metrics(df, 100, 100, "Monthly", date(2022, 12, 31))
    assert m["percentage_gain"] > 0
    assert m["monthly_gain"] > 0
    assert m["annual_gain"] > 0
    # Annual money-weighted rate should compound (roughly) to the monthly one.
    assert abs((1 + m["annual_gain"] / 100) ** (1 / 12) - 1 - m["monthly_gain"] / 100) < 1e-3


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("all passed")
