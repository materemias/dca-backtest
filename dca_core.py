from datetime import date
from typing import Dict

import numpy as np
import pandas as pd


def resample_price_data(df: pd.DataFrame, periodicity: str) -> pd.DataFrame:
    """Resample price data according to investment frequency."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")

    freq_map = {"Daily": "B", "Weekly": "W", "Monthly": "ME"}  # "B" = business days, skip weekends
    df["Close"] = df["Close"].ffill()

    resampled = df.resample(freq_map[periodicity]).agg({"Close": "last", "Volume": "sum"}).reset_index()

    return resampled.ffill()


def _compound_rate_pct(final_value: float, initial_value: float, days_elapsed: float, period_days: float) -> float:
    """Compounded return per `period_days`-long period, as a percentage."""
    if initial_value == 0 or days_elapsed == 0:
        return 0.0
    return round(((final_value / initial_value) ** (period_days / days_elapsed) - 1) * 100, 2)


def calculate_monthly_gain(final_value: float, initial_value: float, days_elapsed: float) -> float:
    """Compounded monthly return percentage (CAGR-style; correct for a lump sum)."""
    return _compound_rate_pct(final_value, initial_value, days_elapsed, 30.44)


def calculate_annual_gain(final_value: float, initial_value: float, days_elapsed: float) -> float:
    """Compounded annual return percentage (CAGR; correct for a lump sum)."""
    return _compound_rate_pct(final_value, initial_value, days_elapsed, 365.0)


def xirr(cashflows, dates, days_in_year: float = 365.0) -> float:
    """Annualized money-weighted return (IRR) for dated cashflows; 0.0 if unsolvable.

    Unlike a lump-sum CAGR this respects *when* each DCA contribution was made, so it
    does not pretend late contributions had the full horizon to compound.
    Solved by bisection (npv is monotonic in rate for an outflows-then-inflow schedule).
    """
    cf = np.asarray(cashflows, dtype=float)
    if (cf >= 0).all() or (cf <= 0).all():
        return 0.0  # need both an outflow and an inflow to have a return

    d = np.asarray(dates, dtype="datetime64[D]")
    years = (d - d[0]).astype("timedelta64[D]").astype(float) / days_in_year

    def npv(rate: float) -> float:
        return float((cf / (1.0 + rate) ** years).sum())

    low, high = -0.9999, 1000.0
    f_low, f_high = npv(low), npv(high)
    if f_low * f_high > 0:  # no sign change inside the bracket -> give up
        return 0.0
    mid = low
    for _ in range(200):
        mid = (low + high) / 2.0
        f_mid = npv(mid)
        if abs(f_mid) < 1e-7:
            break
        if f_low * f_mid < 0:
            high = mid
        else:
            low, f_low = mid, f_mid
    return mid


def _annual_to_monthly_pct(annual_rate: float) -> float:
    """Convert an annualized rate to an equivalent compounded monthly percentage."""
    return round(((1.0 + annual_rate) ** (1.0 / 12.0) - 1.0) * 100.0, 2)


def _max_drawdown_pct(series: np.ndarray) -> float:
    """Maximum drawdown percentage of a value series (vectorized)."""
    if len(series) == 0:
        return 0.0
    running_max = np.maximum.accumulate(series)
    with np.errstate(divide="ignore", invalid="ignore"):
        drawdown = np.where(running_max > 0, (series - running_max) / running_max * 100.0, 0.0)
    return abs(round(float(drawdown.min()), 2))


_EMPTY_METRICS = {
    "final_investment": 0,
    "final_value": 0,
    "absolute_gain": 0,
    "percentage_gain": 0,
    "monthly_gain": 0,
    "annual_gain": 0,
    "total_units": 0,
    "price_drawdown": 0,
    "value_drawdown": 0,
    "buy_hold_gain": 0,
    "buy_hold_monthly": 0,
    "buy_hold_annual": 0,
}


def compute_dca_metrics(dates: np.ndarray, prices: np.ndarray, initial_investment: float, periodic_investment: float, want_snapshots: bool = True) -> Dict:
    """Vectorized DCA metrics for an already-resampled (date, price) series.

    `dates`/`prices` are arrays of equal length; the caller is responsible for slicing
    them to the desired window. Kept separate from resampling so a Monte Carlo sweep can
    resample once and reuse the grid across thousands of windows.
    """
    if len(prices) == 0:
        return dict(_EMPTY_METRICS, snapshots=pd.DataFrame()) if want_snapshots else dict(_EMPTY_METRICS)

    # Contribution per period: initial at t0, periodic thereafter.
    contributions = np.full(len(prices), float(periodic_investment))
    contributions[0] = float(initial_investment)

    investments = np.cumsum(contributions)          # cumulative invested
    units = np.cumsum(contributions / prices)        # cumulative units held
    values = units * prices

    final_investment = float(investments[-1])
    final_value = float(values[-1])
    days_elapsed = (pd.Timestamp(dates[-1]) - pd.Timestamp(dates[0])).days

    buy_hold_value = (final_investment / prices[0]) * prices[-1]

    # DCA monthly gain via money-weighted return (XIRR): outflow per contribution,
    # terminal value as the final inflow. B&H is a single lump sum, so its CAGR is
    # already money-weighted and calculate_monthly_gain stays correct there.
    cashflows = -contributions.copy()
    cashflows[-1] += final_value
    annual_rate = xirr(cashflows, dates)  # money-weighted (XIRR), annualized

    metrics = {
        "final_investment": round(final_investment, 2),
        "final_value": round(final_value, 2),
        "absolute_gain": round(final_value - final_investment, 2),
        "percentage_gain": round((final_value / final_investment - 1) * 100, 2) if final_investment else 0.0,
        "monthly_gain": _annual_to_monthly_pct(annual_rate),
        "annual_gain": round(annual_rate * 100, 2),
        "total_units": round(float(units[-1]), 6),
        "price_drawdown": _max_drawdown_pct(prices),
        "value_drawdown": _max_drawdown_pct(values),
        "buy_hold_gain": round((buy_hold_value / final_investment - 1) * 100, 2) if final_investment else 0.0,
        "buy_hold_monthly": calculate_monthly_gain(buy_hold_value, final_investment, days_elapsed),
        "buy_hold_annual": calculate_annual_gain(buy_hold_value, final_investment, days_elapsed),
    }
    if want_snapshots:
        metrics["snapshots"] = pd.DataFrame({"date": dates, "total_investment": investments, "total_value": values, "total_units": units, "price": prices})
    return metrics


def calculate_dca_metrics(df: pd.DataFrame, initial_investment: float, periodic_investment: float, periodicity: str, end_date: date, start_date: date = None) -> Dict:
    """Calculate DCA investment metrics from raw daily price data."""
    mask = df["date"] <= end_date
    if start_date is not None:
        mask &= df["date"] >= start_date
    df = resample_price_data(df[mask], periodicity).dropna(subset=["Close"])
    return compute_dca_metrics(df["date"].values, df["Close"].values, initial_investment, periodic_investment)


def calculate_multi_asset_dca(asset_data: Dict[str, pd.DataFrame], params: Dict) -> Dict[str, Dict]:
    """Calculate DCA metrics for multiple assets."""
    return {asset: calculate_dca_metrics(df, params["initial_investment"], params["periodic_investment"], params["periodicity"], params["end_date"]) for asset, df in asset_data.items()}
