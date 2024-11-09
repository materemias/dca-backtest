# Standard library imports
from datetime import date
from typing import Dict, List, Tuple

# Third-party imports
import plotly.express as px
import streamlit as st
import yfinance as yf

from config import DEFAULT_TICKERS

def initialize_session_state():
    """Initialize session state variables."""
    if "default_tickers" not in st.session_state:
        st.session_state.default_tickers = DEFAULT_TICKERS
    if "selected_formatted_names" not in st.session_state:
        st.session_state.selected_formatted_names = []
    if "end_date" not in st.session_state:
        st.session_state.end_date = date.today()
    if "multiselect_key" not in st.session_state:
        st.session_state.multiselect_key = 0


def get_ticker_info(ticker: str) -> str:
    """Get formatted display name for a ticker."""
    try:
        info = yf.Ticker(ticker).info
        return f"{info.get('longName', ticker)} ({ticker})"
    except:
        return ticker


def validate_ticker(ticker: str) -> Tuple[bool, yf.Ticker]:
    """Validate a ticker symbol."""
    try:
        ticker_obj = yf.Ticker(ticker)
        test_data = ticker_obj.history(period="1d")
        return not test_data.empty, ticker_obj
    except:
        return False, None


def create_color_mapping(tickers: List[str]) -> Dict[str, str]:
    """Create color mapping for tickers."""
    colors = px.colors.qualitative.Set3[: len(tickers)]
    return dict(zip(tickers, colors))


def truncate_name(name: str, max_length: int = 20) -> str:
    """Truncate name if longer than max_length."""
    return f"{name[:max_length-3]}..." if len(name) > max_length else name
