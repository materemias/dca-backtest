import pandas as pd
import streamlit as st
import yfinance as yf

from chart_creators import create_comparison_charts, create_price_chart
from data_fetcher import fetch_historical_data
from dca_analysis import run_randomized_tests
from dca_core import calculate_multi_asset_dca
from ui_controls import create_ui


def display_detailed_results(results, color_map):
    """Display detailed metrics for each asset."""
    st.header("Detailed Results")

    # Convert results to a list of tuples (asset, metrics) sorted by final_value
    sorted_results = sorted(results.items(), key=lambda x: x[1]["final_value"], reverse=True)

    # Display results in sorted order
    for asset, metrics in sorted_results:
        try:
            info = yf.Ticker(asset).info
            display_name = f"{info.get('longName', asset)} ({asset})"
        except:
            display_name = asset

        # Create the expander with the colored title
        with st.expander(display_name, expanded=True):
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Final Investment", f"${metrics['final_investment']:,.2f}")
                st.metric("Final Value", f"${metrics['final_value']:,.2f}")
            with col2:
                st.metric("Absolute Gain", f"${metrics['absolute_gain']:,.2f}")
                st.metric("Total Units", f"{metrics['total_units']:,.2f}")
            with col3:
                st.metric("Price Max Drawdown", f"{metrics['price_drawdown']:,.2f}%")
                st.metric("Value Max Drawdown", f"{metrics['value_drawdown']:,.2f}%")
            with col4:
                st.metric("DCA % Gain", f"{metrics['percentage_gain']:,.2f}%")
                st.metric("DCA Monthly Gain", f"{metrics['monthly_gain']:,.2f}%")
            with col5:
                st.metric("Buy & Hold % Gain", f"{metrics['buy_hold_gain']:,.2f}%")
                st.metric("B&H Monthly Gain", f"{metrics['buy_hold_monthly']:,.2f}%")


def display_random_test_results(random_results, params):
    """Display results from randomized tests."""
    st.header("Random Test Results (Averages)")

    # Convert results to a list of tuples (asset, metrics) sorted by final_value
    sorted_results = sorted(random_results.items(), key=lambda x: x[1]["final_value"], reverse=True)

    # Display results in sorted order
    for asset, metrics in sorted_results:
        try:
            info = yf.Ticker(asset).info
            display_name = f"{info.get('longName', asset)} ({asset})"
        except:
            display_name = asset

        with st.expander(display_name, expanded=True):
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Avg Final Investment", f"${metrics['final_investment']:,.2f}")
                st.metric("Avg Final Value", f"${metrics['final_value']:,.2f}")
            with col2:
                st.metric("Avg Absolute Gain", f"${metrics['absolute_gain']:,.2f}")
                st.metric("Avg Total Units", f"{metrics['total_units']:,.2f}")
            with col3:
                st.metric("Avg Max Price DD", f"{metrics['price_drawdown']:,.2f}%")
                st.metric("Avg Max Value DD", f"{metrics['value_drawdown']:,.2f}%")
            with col4:
                st.metric("Avg DCA % Gain", f"{metrics['percentage_gain']:,.2f}%")
                st.metric("Avg DCA Monthly Gain", f"{metrics['monthly_gain']:,.2f}%")
            with col5:
                st.metric("Avg B&H Gain", f"{metrics['buy_hold_gain']:,.2f}%")
                st.metric("Avg B&H Monthly", f"{metrics['buy_hold_monthly']:,.2f}%")

            # Add detailed runs table if enabled
            if params["show_individual_runs"] and "all_runs" in metrics:
                st.markdown("#### Individual Test Runs")
                df = pd.DataFrame(metrics["all_runs"])
                # Format numeric columns
                df = df.round(2)
                for col in df.columns:
                    if col in ["final_investment", "final_value", "absolute_gain"]:
                        df[col] = df[col].apply(lambda x: f"${x:,.2f}")
                    elif col in ["percentage_gain", "monthly_gain", "price_drawdown", "value_drawdown", "buy_hold_gain", "buy_hold_monthly"]:
                        df[col] = df[col].apply(lambda x: f"{x}%")
                st.dataframe(df)


def main():
    st.set_page_config(page_title="DCA Calculator", page_icon="📈", layout="wide")

    params = create_ui()

    if params["selected_assets"]:
        asset_data = {}
        for asset in params["selected_assets"]:
            asset_data[asset] = fetch_historical_data(asset, params["start_date"])

        # Calculate regular DCA metrics
        results = calculate_multi_asset_dca(asset_data, params)

        # Create and display charts
        fig1, fig2 = create_comparison_charts(asset_data, results, params)
        price_fig = create_price_chart(asset_data, params)

        st.plotly_chart(fig1, use_container_width=True)
        st.plotly_chart(price_fig, use_container_width=True)
        st.plotly_chart(fig2, use_container_width=True)

        display_detailed_results(results, params["color_map"])

        # Run and display random tests if enabled
        if params.get("run_random_tests"):
            with st.spinner(f'Running {params["num_tests"]} random tests...'):
                random_results = run_randomized_tests(asset_data, params, params["num_tests"])
                display_random_test_results(random_results, params)  # Pass entire params instead of just color_map


if __name__ == "__main__":
    main()
