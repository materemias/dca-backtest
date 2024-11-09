from datetime import date
from typing import Dict, List

import streamlit as st
import yfinance as yf

from config import DEFAULT_INITIAL_INVESTMENT, DEFAULT_PERIODIC_INVESTMENT, DEFAULT_START_DATE
from ui_core import create_color_mapping, get_ticker_info, initialize_session_state, truncate_name, validate_ticker


def handle_new_ticker_form():
    """Handle the new ticker form submission."""
    with st.form("add_ticker_form"):
        new_ticker = st.text_input("Add new ticker", placeholder="Enter Yahoo Finance ticker (e.g. AAPL)", help="Enter a valid Yahoo Finance ticker symbol")
        submitted = st.form_submit_button("Add Ticker")

        if submitted and new_ticker:
            is_valid, ticker_obj = validate_ticker(new_ticker)
            if is_valid:
                if new_ticker not in st.session_state.default_tickers:
                    st.session_state.default_tickers.append(new_ticker)
                    try:
                        info = ticker_obj.info
                        new_display_name = f"{info.get('longName', new_ticker)} ({new_ticker})"
                    except:
                        new_display_name = new_ticker

                    if "selected_formatted_names" not in st.session_state:
                        st.session_state.selected_formatted_names = []
                    st.session_state.selected_formatted_names.append(new_display_name)
                    st.session_state.multiselect_key += 1
                    st.success(f"Added {new_display_name} to the list!")
                else:
                    st.warning("This ticker is already in the list!")
            else:
                st.error("Invalid ticker symbol - no data available")


def display_legend(selected_formatted, name_to_ticker, color_map):
    """Display the legend with colored rectangles."""
    st.subheader("Legend")

    for name in selected_formatted:
        ticker = name_to_ticker[name]
        try:
            info = yf.Ticker(ticker).info
            full_name = f"{info.get('longName', ticker)} ({ticker})"
            truncated_name = f"{truncate_name(info.get('longName', ticker))} ({ticker})"
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


def apply_custom_styling(selected_formatted: List[str], name_to_ticker: Dict[str, str], color_map: Dict[str, str]):
    """Apply custom styling to the multiselect."""
    st.markdown(
        """
        <style>
            .stMultiSelect span[data-baseweb="tag"] {
                background-color: transparent !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    selected_styles = ""
    for i, name in enumerate(selected_formatted, 1):
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


def get_investment_parameters() -> Dict:
    """Get investment parameters from user input."""
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start date", value=DEFAULT_START_DATE, min_value=date(2010, 1, 1), max_value=date.today())
    with col2:
        if start_date > st.session_state.end_date:
            st.session_state.end_date = start_date

        end_date = st.date_input("End date", value=st.session_state.end_date, min_value=start_date, max_value=date.today())
        st.session_state.end_date = end_date

    col3, col4 = st.columns(2)
    with col3:
        initial_investment = st.number_input("Initial investment ($)", min_value=0, value=DEFAULT_INITIAL_INVESTMENT, step=100)
    with col4:
        periodic_investment = st.number_input("Periodic investment ($)", min_value=0, value=DEFAULT_PERIODIC_INVESTMENT, step=100)

    periodicity = st.selectbox("Investment frequency", options=["Daily", "Weekly", "Monthly"], index=2)

    # Add randomized testing controls
    date_diff = end_date - start_date
    run_random_tests = False
    num_tests = 100  # default value
    show_individual_runs = False  # default value

    if date_diff.days >= 730:  # 2 years
        st.sidebar.markdown("### Random Tests")
        num_tests = st.number_input("Number of random tests", min_value=10, max_value=1000, value=100, step=10)
        show_individual_runs = st.checkbox("Show individual runs", value=False, help="Display detailed results for each test run")

        if st.sidebar.button("Run Random Tests", help="Run multiple tests with random date ranges"):
            run_random_tests = True

    return {
        "start_date": start_date,
        "end_date": end_date,
        "initial_investment": initial_investment,
        "periodic_investment": periodic_investment,
        "periodicity": periodicity,
        "run_random_tests": run_random_tests,
        "num_tests": num_tests,
        "show_individual_runs": show_individual_runs,
    }


def create_ui() -> Dict:
    """Create the main user interface."""
    st.title("DCA Investment Calculator")

    with st.sidebar:
        st.header("Settings")
        initialize_session_state()
        handle_new_ticker_form()

        color_map = create_color_mapping(st.session_state.default_tickers)
        formatted_options = [get_ticker_info(ticker) for ticker in st.session_state.default_tickers]
        name_to_ticker = dict(zip(formatted_options, st.session_state.default_tickers))

        selected_formatted = st.multiselect(
            "Enter ticker symbols",
            options=formatted_options,
            default=st.session_state.selected_formatted_names if st.session_state.selected_formatted_names else [formatted_options[0]],
            help="Enter valid Yahoo Finance ticker symbols",
            key=f"ticker_multiselect_{st.session_state.multiselect_key}",
        )

        st.session_state.selected_formatted_names = selected_formatted
        selected_tickers = [name_to_ticker[name] for name in selected_formatted]

        display_legend(selected_formatted, name_to_ticker, color_map)
        params = get_investment_parameters()
        apply_custom_styling(selected_formatted, name_to_ticker, color_map)

    return {
        "selected_assets": selected_tickers,
        "start_date": params["start_date"],
        "end_date": params["end_date"],
        "initial_investment": params["initial_investment"],
        "periodic_investment": params["periodic_investment"],
        "periodicity": params["periodicity"],
        "color_map": color_map,
        "run_random_tests": params.get("run_random_tests", False),
        "num_tests": params.get("num_tests", 100),
        "show_individual_runs": params.get("show_individual_runs", False),
    }
