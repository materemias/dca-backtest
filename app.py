import pandas as pd
import streamlit as st

from chart_creators import create_comparison_charts, create_price_chart
from data_fetcher import fetch_historical_data
from dca_analysis import run_randomized_tests
from dca_core import calculate_multi_asset_dca
from ui_controls import create_ui
from ui_core import get_ticker_info


# (label, key, format, help). Order also drives the column layout (2 metrics per column),
# so DCA/B&H pairs are placed adjacently to share a column.
_NOT_COMPARABLE = (
    " ⚠ Not directly comparable to the matching DCA/B&H figure: Buy & Hold keeps the full sum "
    "invested the whole period while DCA's capital ramps up. Use the Annualized (money-weighted) "
    "rows for a fair, capital-intensity-adjusted comparison."
)
METRIC_SPECS = [
    ("Final Investment", "final_investment", "${:,.2f}", "Total cash contributed by the end date (initial investment plus every periodic buy)."),
    ("Total Units", "total_units", "{:,.2f}", "Total units (shares/coins) accumulated across all purchases."),
    ("Final Value", "final_value", "${:,.2f}", "Market value of all accumulated units at the end date."),
    ("Absolute Gain", "absolute_gain", "${:,.2f}", "Final Value minus Final Investment — profit or loss in dollars."),
    ("Price Max DD", "price_drawdown", "{:,.2f}%", "Largest peak-to-trough drop in the asset's price over the period (max drawdown)."),
    ("Value Max DD", "value_drawdown", "{:,.2f}%", "Largest peak-to-trough drop in your portfolio value over the period (max drawdown)."),
    ("DCA % Gain", "percentage_gain", "{:,.2f}%", "Total return on contributed capital: Final Value / Final Investment − 1." + _NOT_COMPARABLE),
    ("B&H % Gain", "buy_hold_gain", "{:,.2f}%", "Total return if the same total capital were invested as a lump sum at the start (Buy & Hold)." + _NOT_COMPARABLE),
    ("DCA Annualized", "annual_gain", "{:,.2f}%", "Money-weighted annual return (XIRR) — adjusts for how much capital was invested and when. This is the fair comparison vs B&H Annualized, regardless of differing capital intensity."),
    ("B&H Annualized", "buy_hold_annual", "{:,.2f}%", "Annualized return of a lump sum invested at the start (CAGR = its money-weighted return). Compare against DCA Annualized for a capital-intensity-fair result."),
    ("DCA Monthly", "monthly_gain", "{:,.2f}%", "DCA money-weighted return expressed per month (same basis as DCA Annualized)."),
    ("B&H Monthly", "buy_hold_monthly", "{:,.2f}%", "Buy & Hold return expressed per month (same basis as B&H Annualized)."),
]

# Rate/risk metrics are horizon-normalized, so a per-metric median across random windows is
# meaningful. Dollar metrics depend on window length, so they're excluded from the random view.
RATE_RISK_KEYS = {"price_drawdown", "value_drawdown", "percentage_gain", "buy_hold_gain", "annual_gain", "buy_hold_annual", "monthly_gain", "buy_hold_monthly"}


def display_metrics_grid(metrics: dict, prefix: str = "", keys: set = None, percentiles: dict = None):
    """Display metrics in a grid layout, optionally restricted to `keys`.

    If `percentiles` is given, show each metric's 5-95% range as a small caption beneath it.
    """
    specs = [s for s in METRIC_SPECS if keys is None or s[1] in keys]
    cols = st.columns((len(specs) + 1) // 2)
    for i, (label, key, fmt, help_text) in enumerate(specs):
        with cols[i // 2]:
            st.metric(f"{prefix}{label}", fmt.format(metrics[key]), help=help_text)
            if percentiles and key in percentiles:
                lo, hi = percentiles[key]
                st.caption(f"5–95%: {fmt.format(lo)} – {fmt.format(hi)}")


def display_detailed_results(results: dict):
    """Display detailed metrics for each asset."""
    st.header("Detailed Results")
    sorted_results = sorted(results.items(), key=lambda x: x[1]["final_value"], reverse=True)

    for asset, metrics in sorted_results:
        with st.expander(get_ticker_info(asset), expanded=True):
            display_metrics_grid(metrics)


def format_runs_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Format the runs dataframe for display."""
    # Reorder columns
    date_cols = ["start_date", "end_date"]
    other_cols = [col for col in df.columns if col not in date_cols]
    df = df[date_cols + other_cols]

    # Round and format
    df = df.round(2)
    for col in df.columns:
        if col in ["final_investment", "final_value", "absolute_gain"]:
            df[col] = df[col].apply(lambda x: f"${x:,.2f}")
        elif col not in date_cols:
            df[col] = df[col].apply(lambda x: f"{x}%")

    return df.sort_values(by=date_cols)


def display_random_test_results(random_results: dict, params: dict):
    """Display results from randomized tests."""
    st.header("Random Test Results (Medians)")
    st.caption(
        "Each value is the median of that metric across all random runs (the 5–95% band shows its spread) — "
        "a per-metric summary, **not** a single backtest, so the columns won't reconcile to one run. "
        "Dollar figures are omitted here because they scale with each window's length; see Detailed Results for those."
    )
    sorted_results = sorted(random_results.items(), key=lambda x: x[1]["annual_gain"], reverse=True)

    for asset, metrics in sorted_results:
        with st.expander(get_ticker_info(asset), expanded=True):
            display_metrics_grid(metrics, prefix="Median ", keys=RATE_RISK_KEYS, percentiles=metrics.get("percentiles"))

            if params["show_individual_runs"] and "all_runs" in metrics:
                st.markdown("#### Individual Test Runs")
                df = pd.DataFrame(metrics["all_runs"])
                df = format_runs_dataframe(df)
                st.dataframe(df)


def main():
    """Main application function."""
    st.set_page_config(page_title="DCA Calculator", page_icon="📈", layout="wide")
    params = create_ui()

    if not params["selected_assets"]:
        return

    # Get data and calculate results
    asset_data = {asset: fetch_historical_data(asset, params["start_date"]) for asset in params["selected_assets"]}
    results = calculate_multi_asset_dca(asset_data, params)

    # Display charts
    for fig in create_comparison_charts(asset_data, results, params):
        st.plotly_chart(fig, use_container_width=True)
    st.plotly_chart(create_price_chart(asset_data, params), use_container_width=True)

    # Display results
    display_detailed_results(results)

    if params.get("run_random_tests"):
        with st.spinner(f'Running {params["num_tests"]} random tests...'):
            random_results = run_randomized_tests(asset_data, params, params["num_tests"])
            display_random_test_results(random_results, params)


if __name__ == "__main__":
    main()
