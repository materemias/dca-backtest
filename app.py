import pandas as pd
import streamlit as st
import yfinance as yf

from chart_creators import create_comparison_charts, create_price_chart
from data_fetcher import fetch_historical_data
from dca_analysis import run_randomized_tests
from dca_core import calculate_multi_asset_dca
from ui_controls import create_ui


def get_asset_display_name(asset: str) -> str:
    """Get formatted display name for an asset."""
    try:
        info = yf.Ticker(asset).info
        return f"{info.get('longName', asset)} ({asset})"
    except:
        return asset


def display_metrics_grid(metrics: dict, prefix: str = ""):
    """Display metrics in a grid layout."""
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric(f"{prefix}Final Investment", f"${metrics['final_investment']:,.2f}")
        st.metric(f"{prefix}Final Value", f"${metrics['final_value']:,.2f}")
    with col2:
        st.metric(f"{prefix}Absolute Gain", f"${metrics['absolute_gain']:,.2f}")
        st.metric(f"{prefix}Total Units", f"{metrics['total_units']:,.2f}")
    with col3:
        st.metric(f"{prefix}Price Max DD", f"{metrics['price_drawdown']:,.2f}%")
        st.metric(f"{prefix}Value Max DD", f"{metrics['value_drawdown']:,.2f}%")
    with col4:
        st.metric(f"{prefix}DCA % Gain", f"{metrics['percentage_gain']:,.2f}%")
        st.metric(f"{prefix}DCA Monthly Gain", f"{metrics['monthly_gain']:,.2f}%")
    with col5:
        st.metric(f"{prefix}B&H % Gain", f"{metrics['buy_hold_gain']:,.2f}%")
        st.metric(f"{prefix}B&H Monthly", f"{metrics['buy_hold_monthly']:,.2f}%")


def display_detailed_results(results: dict):
    """Display detailed metrics for each asset."""
    st.header("Detailed Results")
    sorted_results = sorted(results.items(), key=lambda x: x[1]["final_value"], reverse=True)
    
    for asset, metrics in sorted_results:
        with st.expander(get_asset_display_name(asset), expanded=True):
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
    st.header("Random Test Results (Averages)")
    sorted_results = sorted(random_results.items(), key=lambda x: x[1]["final_value"], reverse=True)
    
    for asset, metrics in sorted_results:
        with st.expander(get_asset_display_name(asset), expanded=True):
            display_metrics_grid(metrics, prefix="Avg ")
            
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
    asset_data = {
        asset: fetch_historical_data(asset, params["start_date"])
        for asset in params["selected_assets"]
    }
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
