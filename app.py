import streamlit as st
import polars as pl
from datetime import datetime, date
from data_fetcher import fetch_historical_data, get_ticker_symbol

def create_ui():
    st.title("DCA Investment Calculator")
    
    # Asset selector - multiple choice
    assets = ["BTC", "ETH", "S&P500", "NASDAQ-100"]
    selected_assets = st.multiselect(
        "Select assets to analyze",
        options=assets,
        default=["BTC"]
    )
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start date",
            value=date(2020, 1, 1),
            min_value=date(2010, 1, 1),
            max_value=date.today()
        )
    with col2:
        end_date = st.date_input(
            "End date",
            value=date.today(),
            min_value=start_date,
            max_value=date.today()
        )
    
    # Investment parameters
    col3, col4 = st.columns(2)
    with col3:
        initial_investment = st.number_input(
            "Initial investment ($)",
            min_value=0,
            value=1000,
            step=100
        )
    with col4:
        periodic_investment = st.number_input(
            "Periodic investment ($)",
            min_value=0,
            value=100,
            step=50
        )
    
    # Periodicity selector
    periodicity = st.selectbox(
        "Investment frequency",
        options=["Daily", "Weekly", "Monthly"],
        index=2  # Monthly as default
    )
    
    return {
        "selected_assets": selected_assets,
        "start_date": start_date,
        "end_date": end_date,
        "initial_investment": initial_investment,
        "periodic_investment": periodic_investment,
        "periodicity": periodicity
    }

def main():
    st.set_page_config(
        page_title="DCA Calculator",
        page_icon="📈",
        layout="wide"
    )
    
    params = create_ui()
    
    # Only proceed if assets are selected
    if params["selected_assets"]:
        # Placeholder for data processing and visualization
        # (We'll implement this in the next feature)
        st.write("Selected parameters:", params)
        
        # Load data for selected assets
        for asset in params["selected_assets"]:
            data = fetch_historical_data(asset, params["start_date"])
            st.write(f"Preview of {asset} data:")
            st.dataframe(data.head())

if __name__ == "__main__":
    main()
