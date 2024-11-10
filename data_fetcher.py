import pathlib
from datetime import datetime, timedelta
from functools import lru_cache

import pandas as pd
import yfinance as yf


def get_cache_path(ticker: str) -> pathlib.Path:
    """Get the path for cached parquet file"""
    cache_dir = pathlib.Path("cache")
    cache_dir.mkdir(exist_ok=True)
    # Replace any special characters in ticker with underscore for filename
    safe_ticker = ticker.replace("^", "").replace("-", "_").replace(".", "_")
    return cache_dir / f"{safe_ticker.lower()}_history.parquet"


@lru_cache(maxsize=10)
def fetch_historical_data(ticker: str, start_date: datetime = None) -> pd.DataFrame:
    """
    Fetch daily historical data for a given ticker
    Returns a Pandas DataFrame with columns: date, open, high, low, close, volume
    Uses both parquet caching and function memoization
    """
    if not ticker:
        raise ValueError(f"Invalid ticker: {ticker}")

    # Define today at the start of the function
    today = datetime.now().date()

    if start_date is None:
        start_date = datetime(2010, 1, 1)  # Default start date

    # Add buffer days to handle weekends/holidays
    buffer_days = 5
    adjusted_start = start_date - timedelta(days=buffer_days)

    cache_file = get_cache_path(ticker)

    # Try to load cached data
    if cache_file.exists():
        cached_df = pd.read_parquet(cache_file)
        earliest_cached_date = cached_df["date"].min()
        latest_cached_date = cached_df["date"].max()

        need_earlier_data = adjusted_start < earliest_cached_date
        need_later_data = latest_cached_date < datetime.now().date()

        if need_earlier_data or need_later_data:
            # Fetch missing historical data
            ticker_data = yf.Ticker(ticker)
            today = datetime.now().date()

            if need_earlier_data:
                history_start = min(adjusted_start, earliest_cached_date - timedelta(days=1))
                history_end = earliest_cached_date
                if history_start < history_end:
                    try:
                        early_df = ticker_data.history(start=history_start, end=history_end, interval="1d")
                        if not early_df.empty:
                            early_df = early_df.reset_index()
                            early_df = early_df.rename(columns={"Date": "date"})
                            early_df["date"] = pd.to_datetime(early_df["date"]).dt.date
                            cached_df = pd.concat([early_df, cached_df])
                    except Exception as e:
                        print(f"Warning: Could not fetch earlier data for {ticker}: {str(e)}")

            if need_later_data:
                history_start = latest_cached_date + timedelta(days=1)
                history_end = today
                if history_start < history_end:
                    try:
                        new_df = ticker_data.history(start=history_start, end=history_end, interval="1d")
                        if not new_df.empty:
                            new_df = new_df.reset_index()
                            new_df = new_df.rename(columns={"Date": "date"})
                            new_df["date"] = pd.to_datetime(new_df["date"]).dt.date
                            cached_df = pd.concat([cached_df, new_df])
                    except Exception as e:
                        print(f"Warning: Could not fetch later data for {ticker}: {str(e)}")

            # Save updated cache
            cached_df = cached_df.sort_values("date").drop_duplicates(subset=["date"])
            cached_df.to_parquet(cache_file)

        # Filter to requested date range
        result_df = cached_df[(cached_df["date"] >= start_date) & (cached_df["date"] <= today)]
        return result_df if not result_df.empty else pd.DataFrame()

    # If no cache exists, fetch all data
    ticker_data = yf.Ticker(ticker)
    if adjusted_start < today:
        try:
            df = ticker_data.history(start=adjusted_start, end=today, interval="1d")
            if not df.empty:
                # Clean up DataFrame
                df = df.reset_index()
                df = df.rename(columns={"Date": "date"})
                df["date"] = pd.to_datetime(df["date"]).dt.date

                # Cache the data
                df.to_parquet(cache_file)

                # Filter to requested date range
                result_df = df[(df["date"] >= start_date) & (df["date"] <= today)]
                return result_df if not result_df.empty else pd.DataFrame()
        except Exception as e:
            print(f"Warning: Could not fetch data for {ticker}: {str(e)}")

    return pd.DataFrame()  # Return empty DataFrame if no data available
