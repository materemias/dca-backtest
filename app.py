# Standard library imports
from datetime import date

# Third-party imports
import streamlit as st
import yfinance as yf

# Local imports
from ui_components import create_ui
from data_fetcher import fetch_historical_data
from dca_calculator import calculate_multi_asset_dca
from chart_creators import create_comparison_charts, create_price_chart

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
                st.metric("DCA % Gain", f"{metrics['percentage_gain']:,.2f}%")
                st.metric("DCA Monthly Gain", f"{metrics['monthly_gain']:,.2f}%")
            with col4:
                st.metric("Price Max Drawdown", f"{metrics['price_drawdown']:,.2f}%")
                st.metric("Value Max Drawdown", f"{metrics['value_drawdown']:,.2f}%")
            with col5:
                st.metric("Buy & Hold Gain", f"{metrics['buy_hold_gain']:,.2f}%")
                st.metric("B&H Monthly Gain", f"{metrics['buy_hold_monthly']:,.2f}%")

def main():
    st.set_page_config(page_title="DCA Calculator", page_icon="📈", layout="wide")

    params = create_ui()

    # Only proceed if assets are selected
    if params["selected_assets"]:
        # Load data for selected assets
        asset_data = {}
        for asset in params["selected_assets"]:
            asset_data[asset] = fetch_historical_data(asset, params["start_date"])

        # Calculate DCA metrics for all assets
        results = calculate_multi_asset_dca(asset_data, params)

        # Create and display charts
        fig1, fig2 = create_comparison_charts(asset_data, results, params)
        price_fig = create_price_chart(asset_data, params)

        # Display charts
        st.plotly_chart(fig1, use_container_width=True)
        st.plotly_chart(price_fig, use_container_width=True)
        st.plotly_chart(fig2, use_container_width=True)

        # Display detailed metrics
        display_detailed_results(results, params["color_map"])

if __name__ == "__main__":
    main()
