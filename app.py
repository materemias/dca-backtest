from datetime import date

import plotly.graph_objects as go
import streamlit as st

from data_fetcher import fetch_historical_data
from dca_calculator import calculate_multi_asset_dca


def create_ui():
    st.title("DCA Investment Calculator")

    # Move all settings to sidebar
    with st.sidebar:
        st.header("Settings")

        # Asset selector - multiple choice
        assets = ["BTC", "ETH", "S&P500", "NASDAQ-100", "WD Nasdaq 3x"]
        selected_assets = st.multiselect("Select assets to analyze", options=assets, default=["BTC"])

        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start date", 
                value=date(2022, 1, 1), 
                min_value=date(2010, 1, 1), 
                max_value=date.today()
            )
        with col2:
            end_date = st.date_input(
                "End date", 
                value=max(start_date, date.today()),  
                min_value=start_date,  
                max_value=date.today()
            )

        # Investment parameters
        col3, col4 = st.columns(2)
        with col3:
            initial_investment = st.number_input("Initial investment ($)", min_value=0, value=100, step=100)
        with col4:
            periodic_investment = st.number_input("Periodic investment ($)", min_value=0, value=100, step=100)

        # Periodicity selector
        periodicity = st.selectbox(
            "Investment frequency",
            options=["Daily", "Weekly", "Monthly"],
            index=2,  # Monthly as default
        )

    return {
        "selected_assets": selected_assets,
        "start_date": start_date,
        "end_date": end_date,
        "initial_investment": initial_investment,
        "periodic_investment": periodic_investment,
        "periodicity": periodicity,
    }


def create_comparison_charts(asset_data: dict, results: dict, params: dict):
    # Create investment value over time chart
    fig1 = go.Figure()

    for asset in asset_data.keys():
        snapshots = results[asset]["snapshots"]  # Get the snapshots DataFrame

        # Add investment line using the actual tracked total_investment
        fig1.add_trace(go.Scatter(x=snapshots["date"], y=snapshots["total_investment"], name=f"{asset} - Investment", line=dict(dash="dash")))

        # Add value line using the actual tracked total_value
        fig1.add_trace(go.Scatter(x=snapshots["date"], y=snapshots["total_value"], name=f"{asset} - Value"))

    fig1.update_layout(title="Investment vs. Value Over Time", xaxis_title="Date", yaxis_title="Value ($)", hovermode="x unified")

    # Create performance comparison chart
    fig2 = go.Figure()

    performance_data = {"Asset": [], "Final Investment": [], "Final Value": [], "Absolute Gain": [], "Percentage Gain": []}

    for asset, metrics in results.items():
        performance_data["Asset"].append(asset)
        performance_data["Final Investment"].append(metrics["final_investment"])
        performance_data["Final Value"].append(metrics["final_value"])
        performance_data["Absolute Gain"].append(metrics["absolute_gain"])
        performance_data["Percentage Gain"].append(metrics["percentage_gain"])

    # Add bars for investment and final value
    fig2.add_trace(go.Bar(name="Final Investment", x=performance_data["Asset"], y=performance_data["Final Investment"], marker_color="lightgray"))

    fig2.add_trace(go.Bar(name="Final Value", x=performance_data["Asset"], y=performance_data["Final Value"], marker_color="lightgreen"))

    fig2.update_layout(title="Investment Performance Comparison", barmode="group", yaxis_title="Value ($)", hovermode="x unified")

    return fig1, fig2


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

        # Display charts
        st.plotly_chart(fig1, use_container_width=True)
        st.plotly_chart(fig2, use_container_width=True)

        # Display detailed metrics
        st.header("Detailed Results")

        for asset, metrics in results.items():
            with st.expander(f"{asset} Results", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Final Investment", f"${metrics['final_investment']:,.2f}")
                    st.metric("Final Value", f"${metrics['final_value']:,.2f}")
                with col2:
                    st.metric("Absolute Gain", f"${metrics['absolute_gain']:,.2f}")
                    st.metric("Total Units", f"{metrics['total_units']:,.6f}")
                with col3:
                    st.metric("Percentage Gain", f"{metrics['percentage_gain']:,.2f}%")
                    st.metric("Avg Monthly Gain", f"{metrics['monthly_gain']:,.2f}%")


if __name__ == "__main__":
    main()
