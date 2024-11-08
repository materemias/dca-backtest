from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

from data_fetcher import fetch_historical_data
from dca_calculator import calculate_multi_asset_dca


def create_ui():
    st.title("DCA Investment Calculator")

    # Move all settings to sidebar
    with st.sidebar:
        st.header("Settings")

        # Replace asset selector with ticker input
        if "default_tickers" not in st.session_state:
            st.session_state.default_tickers = ["BTC-USD", "ETH-USD", "^GSPC", "^NDX", "QQQ3.L", "AAAU"]

        # Initialize selected formatted names session state
        if "selected_formatted_names" not in st.session_state:
            st.session_state.selected_formatted_names = []

        # Add a new ticker using a form
        with st.form("add_ticker_form"):
            new_ticker = st.text_input(
                "Add new ticker", placeholder="Enter Yahoo Finance ticker (e.g. AAPL)", help="Enter a valid Yahoo Finance ticker symbol to add to the list", key="new_ticker_input"
            )
            submitted = st.form_submit_button("Add Ticker")

            if submitted and new_ticker:
                try:
                    # Try to get history for the ticker to validate it
                    ticker_obj = yf.Ticker(new_ticker)
                    # Just check if we can get any recent history
                    test_data = ticker_obj.history(period="1d")
                    if not test_data.empty:
                        if new_ticker not in st.session_state.default_tickers:
                            st.session_state.default_tickers.append(new_ticker)
                            # Get the formatted name for the new ticker
                            try:
                                info = ticker_obj.info
                                new_display_name = f"{info.get('longName', new_ticker)} ({new_ticker})"
                            except:
                                new_display_name = new_ticker
                            # Add to selected items
                            if "selected_formatted_names" not in st.session_state:
                                st.session_state.selected_formatted_names = []
                            st.session_state.selected_formatted_names.append(new_display_name)
                            st.success(f"Added {new_display_name} to the list!")
                        else:
                            st.warning("This ticker is already in the list!")
                    else:
                        st.error("Invalid ticker symbol - no data available")
                except Exception as e:
                    st.error(f"Error adding ticker: {str(e)}")

        # Generate a color palette for all tickers
        colors = px.colors.qualitative.Set3[: len(st.session_state.default_tickers)]
        color_map = dict(zip(st.session_state.default_tickers, colors))

        # Create formatted options with colors for the multiselect
        formatted_options = []
        for ticker in st.session_state.default_tickers:
            try:
                info = yf.Ticker(ticker).info
                display_name = f"{info.get('longName', ticker)} ({ticker})"
            except:
                display_name = ticker
            formatted_options.append(display_name)

        # Create a mapping between formatted names and actual tickers
        name_to_ticker = dict(zip(formatted_options, st.session_state.default_tickers))

        # First, select the default tickers
        selected_formatted = st.multiselect(
            "Enter ticker symbols",
            options=formatted_options,
            default=st.session_state.selected_formatted_names if st.session_state.selected_formatted_names else [formatted_options[0]],
            help="Enter valid Yahoo Finance ticker symbols",
        )

        # Update the session state with current selection
        st.session_state.selected_formatted_names = selected_formatted

        # Convert selected formatted names back to tickers
        selected_tickers = [name_to_ticker[name] for name in selected_formatted]

        # Add Legend section with colored rectangles
        st.subheader("Legend")

        def truncate_name(name, max_length=20):
            """Truncate name if longer than max_length and add ellipsis"""
            if len(name) > max_length:
                return name[: max_length - 3] + "..."
            return name

        # Important: Use selected_formatted to maintain color consistency
        for name in selected_formatted:  # Use selected_formatted instead of selected_tickers
            ticker = name_to_ticker[name]  # Get the ticker from the mapping
            try:
                info = yf.Ticker(ticker).info
                full_name = f"{info.get('longName', ticker)} ({ticker})"
                truncated_name = f"{truncate_name(info.get('longName', ticker))} ({ticker})"

                # Use the same color from color_map
                color_rect = f'<div style="width: 20px; height: 20px; background-color: {color_map[ticker]}; display: inline-block; margin-right: 8px; vertical-align: middle;"></div>'
                st.markdown(
                    f"""<div style="display: flex; align-items: center;" title="{full_name}">
                        {color_rect}<div>{truncated_name}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            except:
                st.markdown(f"{ticker}", unsafe_allow_html=True)
        st.markdown("<hr style='margin-top: 10px; margin-bottom: 10px;'>", unsafe_allow_html=True)

        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start date", value=date(2022, 1, 1), min_value=date(2010, 1, 1), max_value=date.today())
        with col2:
            end_date = st.date_input("End date", value=max(start_date, date.today()), min_value=start_date, max_value=date.today())

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

        # Custom CSS for the multiselect tags
        st.markdown(
            """
            <style>
                /* Base styles for all tags */
                .stMultiSelect span[data-baseweb="tag"] {
                    background-color: transparent !important;
                }
            </style>
        """,
            unsafe_allow_html=True,
        )

        # Create dynamic CSS for selected items
        selected_styles = ""
        for i, name in enumerate(selected_formatted, 1):  # Only style selected items
            ticker = name_to_ticker[name]
            selected_styles += f"""
                .stMultiSelect span[data-baseweb="tag"]:nth-of-type({i}) {{
                    background-color: {color_map[ticker]} !important;
                    color: black !important;
                }}
                .stMultiSelect span[data-baseweb="tag"]:nth-of-type({i}) span {{
                    color: black !important;
                }}
            """

        st.markdown(f"<style>{selected_styles}</style>", unsafe_allow_html=True)

    return {
        "selected_assets": selected_tickers,  # Changed from selected_assets to selected_tickers
        "start_date": start_date,
        "end_date": end_date,
        "initial_investment": initial_investment,
        "periodic_investment": periodic_investment,
        "periodicity": periodicity,
        "color_map": color_map,  # Add color_map to the returned dictionary
    }


def create_comparison_charts(asset_data: dict, results: dict, params: dict):
    # Use the color map from params instead
    color_map = params["color_map"]

    # Create investment value over time chart
    fig1 = go.Figure()

    for asset in asset_data.keys():
        snapshots = results[asset]["snapshots"]
        color = color_map[asset]

        # Try to get descriptive name
        try:
            info = yf.Ticker(asset).info
            display_name = f"{info.get('longName', asset)} ({asset})"
        except:
            display_name = asset

        # Add investment line using the actual tracked total_investment
        fig1.add_trace(go.Scatter(x=snapshots["date"], y=snapshots["total_investment"], name=f"{display_name} - Investment", line=dict(dash="dash", color=color)))

        # Add value line using the actual tracked total_value
        fig1.add_trace(go.Scatter(x=snapshots["date"], y=snapshots["total_value"], name=f"{display_name} - Value", line=dict(color=color)))

    fig1.update_layout(title="Investment vs. Value Over Time", xaxis_title="Date", yaxis_title="Value ($)", hovermode="x unified")

    # Create performance comparison chart
    fig2 = go.Figure()

    performance_data = {"Asset": [], "Display_Name": [], "Final Investment": [], "Final Value": [], "Absolute Gain": [], "Percentage Gain": [], "Color": []}

    for asset, metrics in results.items():
        try:
            info = yf.Ticker(asset).info
            display_name = f"{info.get('longName', asset)} ({asset})"
        except:
            display_name = asset

        performance_data["Asset"].append(asset)
        performance_data["Display_Name"].append(display_name)
        performance_data["Final Investment"].append(metrics["final_investment"])
        performance_data["Final Value"].append(metrics["final_value"])
        performance_data["Absolute Gain"].append(metrics["absolute_gain"])
        performance_data["Percentage Gain"].append(metrics["percentage_gain"])
        performance_data["Color"].append(params["color_map"][asset])

    # Convert to DataFrame and sort by Final Value
    perf_df = pd.DataFrame(performance_data)
    perf_df = perf_df.sort_values("Final Value", ascending=False)

    # Add bars for investment and final value using sorted data
    fig2.add_trace(go.Bar(name="Final Investment", x=perf_df["Display_Name"], y=perf_df["Final Investment"], marker_color="lightgray"))

    fig2.add_trace(go.Bar(name="Final Value", x=perf_df["Display_Name"], y=perf_df["Final Value"], marker_color=perf_df["Color"]))

    fig2.update_layout(title="Investment Performance Comparison", barmode="group", yaxis_title="Value ($)", hovermode="x unified")

    return fig1, fig2


def create_price_chart(asset_data: dict, params: dict) -> go.Figure:
    """Create a price chart showing prices as percentage of all-time high"""
    fig = go.Figure()

    for asset, df in asset_data.items():
        # Calculate all-time high for the asset
        all_time_high = df["Close"].max()
        # Calculate percentage of ATH
        normalized_prices = (df["Close"] / all_time_high) * 100

        # Try to get descriptive name
        try:
            info = yf.Ticker(asset).info
            display_name = f"{info.get('longName', asset)} ({asset})"
        except:
            display_name = asset

        # Add trace using the same color as other charts
        fig.add_trace(go.Scatter(x=df["date"], y=normalized_prices, name=display_name, line=dict(color=params["color_map"][asset])))

    fig.update_layout(
        title="Price Performance (% of All-Time High)", xaxis_title="Date", yaxis_title="Percentage of All-Time High", hovermode="x unified", yaxis=dict(tickformat=".1f", ticksuffix="%")
    )

    return fig


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
        # Add the new price chart
        price_fig = create_price_chart(asset_data, params)
        st.plotly_chart(price_fig, use_container_width=True)
        st.plotly_chart(fig2, use_container_width=True)

        # Display detailed metrics
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
