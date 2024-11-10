import pathlib
from datetime import datetime, timedelta
from functools import lru_cache

import pandas as pd
import yfinance as yf


def get_cache_path(ticker: str) -> pathlib.Path:
    """Get the path for cached parquet file"""
    cache_dir = pathlib.Path("cache")
    cache_dir.mkdir(exist_ok=True)
    safe_ticker = ticker.replace("^", "").replace("-", "_").replace(".", "_")
    return cache_dir / f"{safe_ticker.lower()}_history.parquet"


@lru_cache(maxsize=10)
def fetch_historical_data(ticker: str, start_date: datetime = None) -> pd.DataFrame:
    """Fetch daily historical data for a given ticker with caching"""
    if not ticker:
        raise ValueError(f"Invalid ticker: {ticker}")

    today = datetime.now().date()
    start_date = start_date or datetime(2010, 1, 1)
    adjusted_start = start_date - timedelta(days=5)  # Buffer for weekends/holidays
    cache_file = get_cache_path(ticker)

    def process_df(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()
        df = df.reset_index()
        df = df.rename(columns={"Date": "date"})
        df["date"] = pd.to_datetime(df["date"]).dt.date
        return df

    try:
        if cache_file.exists():
            cached_df = pd.read_parquet(cache_file)
            earliest_date = cached_df["date"].min()
            latest_date = cached_df["date"].max()

            ticker_data = yf.Ticker(ticker)
            updated_df = cached_df.copy()

            # Fetch earlier data if needed
            if adjusted_start < earliest_date:
                early_df = process_df(ticker_data.history(start=adjusted_start, end=earliest_date))
                updated_df = pd.concat([early_df, updated_df]) if not early_df.empty else updated_df

            # Fetch newer data if needed
            if latest_date < today:
                new_df = process_df(ticker_data.history(start=latest_date + timedelta(days=1), end=today))
                updated_df = pd.concat([updated_df, new_df]) if not new_df.empty else updated_df

            if len(updated_df) != len(cached_df):
                updated_df = updated_df.sort_values("date").drop_duplicates(subset=["date"])
                updated_df.to_parquet(cache_file)
        else:
            updated_df = process_df(yf.Ticker(ticker).history(start=adjusted_start, end=today))
            if not updated_df.empty:
                updated_df.to_parquet(cache_file)

        result_df = updated_df[(updated_df["date"] >= start_date) & (updated_df["date"] <= today)]
        return result_df if not result_df.empty else pd.DataFrame()

    except Exception as e:
        print(f"Warning: Could not fetch data for {ticker}: {str(e)}")
        return pd.DataFrame()
