from typing import Tuple

import pandas as pd
import plotly.graph_objects as go
import yfinance as yf


def create_comparison_charts(asset_data: dict, results: dict, params: dict) -> Tuple[go.Figure, go.Figure]:
    """Create investment value and performance comparison charts."""
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

        # Calculate running maximum value and drawdown for hover data
        running_max = snapshots["total_value"].expanding().max()
        drawdown = ((snapshots["total_value"] - running_max) / running_max) * 100

        # Add investment line using the actual tracked total_investment
        fig1.add_trace(go.Scatter(x=snapshots["date"], y=snapshots["total_investment"], name=f"{display_name} - Investment", line=dict(dash="dash", color=color)))

        # Add value line using the actual tracked total_value with drawdown in hover
        fig1.add_trace(
            go.Scatter(
                x=snapshots["date"],
                y=snapshots["total_value"],
                name=f"{display_name} - Value",
                line=dict(color=color),
                hovertemplate=("<b>%{fullData.name}</b><br>" + "Date: %{x}<br>" + "Value: $%{y:,.2f}<br>" + "Drawdown: %{customdata:.2f}%<br>" + "<extra></extra>"),
                customdata=drawdown,
            )
        )

    fig1.update_layout(title="Investment vs. Value Over Time", xaxis_title="Date", yaxis_title="Value ($)", hovermode="x unified")

    # Create performance comparison chart
    fig2 = go.Figure()

    performance_data = {
        "Asset": [], 
        "Display_Name": [], 
        "DCA_Gain": [],  # Changed from Final Investment
        "BH_Gain": [],   # Changed from Final Value
        "Color": []
    }

    for asset, metrics in results.items():
        try:
            info = yf.Ticker(asset).info
            display_name = f"{info.get('longName', asset)} ({asset})"
        except:
            display_name = asset

        performance_data["Asset"].append(asset)
        performance_data["Display_Name"].append(display_name)
        performance_data["DCA_Gain"].append(metrics["percentage_gain"])  # Changed
        performance_data["BH_Gain"].append(metrics["buy_hold_gain"])     # Changed
        performance_data["Color"].append(params["color_map"][asset])

    # Convert to DataFrame and sort by DCA Gain
    perf_df = pd.DataFrame(performance_data)
    perf_df = perf_df.sort_values("DCA_Gain", ascending=False)  # Changed sorting column

    # Add bars for DCA and Buy & Hold gains
    fig2.add_trace(
        go.Bar(
            name="DCA % Gain", 
            x=perf_df["Display_Name"], 
            y=perf_df["DCA_Gain"],
            marker_color=perf_df["Color"]
        )
    )

    fig2.add_trace(
        go.Bar(
            name="Buy & Hold % Gain", 
            x=perf_df["Display_Name"], 
            y=perf_df["BH_Gain"],
            marker_color="lightgray"
        )
    )

    fig2.update_layout(
        title="Investment Performance Comparison", 
        barmode="group", 
        yaxis_title="Gain (%)",  # Changed
        yaxis=dict(tickformat=".1f", ticksuffix="%"),  # Added percentage formatting
        hovermode="x unified"
    )

    return fig1, fig2


def create_price_chart(asset_data: dict, params: dict) -> go.Figure:
    """Create a price chart showing prices as percentage of all-time high"""
    fig = go.Figure()

    for asset, df in asset_data.items():
        # Filter data for the selected date range
        mask = (df["date"] >= params["start_date"]) & (df["date"] <= params["end_date"])
        df_filtered = df[mask]

        # Calculate all-time high for the asset within the selected date range
        all_time_high = df_filtered["Close"].max()
        # Calculate percentage of ATH
        normalized_prices = (df_filtered["Close"] / all_time_high) * 100

        # Try to get descriptive name
        try:
            info = yf.Ticker(asset).info
            display_name = f"{info.get('longName', asset)} ({asset})"
        except:
            display_name = asset

        # Add trace with customized hover template
        fig.add_trace(
            go.Scatter(
                x=df_filtered["date"],
                y=normalized_prices,
                name=display_name,
                line=dict(color=params["color_map"][asset]),
                hovertemplate=("<b>%{fullData.name}</b><br>" + "Date: %{x}<br>" + "Price: $%{customdata:,.2f}<br>" + "Percent of ATH: %{y:.1f}%<br>" + "<extra></extra>"),
                customdata=df_filtered["Close"],  # Add actual price data for hover
            )
        )

    fig.update_layout(
        title="Price Performance (% of All-Time High)", xaxis_title="Date", yaxis_title="Percentage of All-Time High", hovermode="x unified", height=800, yaxis=dict(tickformat=".1f", ticksuffix="%")
    )

    return fig
