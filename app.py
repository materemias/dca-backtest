# Standard library imports

# Third-party imports
import streamlit as st
import yfinance as yf

from chart_creators import create_comparison_charts, create_price_chart
from data_fetcher import fetch_historical_data
from dca_calculator import calculate_multi_asset_dca

# Local imports
from ui_components import create_ui


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
                st.metric("Total Units", f"{metrics['total_units']:,.6f}")
            with col3:
                st.metric("Price Max Drawdown", f"{metrics['price_drawdown']:,.2f}%")
                st.metric("Value Max Drawdown", f"{metrics['value_drawdown']:,.2f}%")
            with col4:
                st.metric("DCA % Gain", f"{metrics['percentage_gain']:,.2f}%")
                st.metric("DCA Monthly Gain", f"{metrics['monthly_gain']:,.2f}%")
            with col5:
                st.metric("Buy & Hold % Gain", f"{metrics['buy_hold_gain']:,.2f}%")
                st.metric("B&H Monthly Gain", f"{metrics['buy_hold_monthly']:,.2f}%")


def display_random_test_results(random_results, color_map):
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
                st.metric("Avg % Gain", f"{metrics['percentage_gain']:,.2f}%")
            with col3:
                st.metric("Avg Monthly Gain", f"{metrics['monthly_gain']:,.2f}%")
                st.metric("Avg Price DD", f"{metrics['price_drawdown']:,.2f}%")
            with col4:
                st.metric("Avg Value DD", f"{metrics['value_drawdown']:,.2f}%")
            with col5:
                st.metric("Avg B&H Gain", f"{metrics['buy_hold_gain']:,.2f}%")
                st.metric("Avg B&H Monthly", f"{metrics['buy_hold_monthly']:,.2f}%")

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
                display_random_test_results(random_results, params["color_map"])


if __name__ == "__main__":
    main()
