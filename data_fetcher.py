import pathlib
from datetime import datetime, timedelta
from functools import lru_cache

import pandas as pd
import yfinance as yf


def get_ticker_symbol(asset: str) -> str:
    """Map asset names to their ticker symbols"""
    ticker_mapping = {
        "BTC": "BTC-USD",
        "ETH": "ETH-USD",
        "S&P500": "^GSPC",
        "NASDAQ-100": "^NDX",
        "WD Nasdaq 3x": "QQQ3.L",
    }
    return ticker_mapping.get(asset)


def get_cache_path(asset: str) -> pathlib.Path:
    """Get the path for cached parquet file"""
    cache_dir = pathlib.Path("cache")
    cache_dir.mkdir(exist_ok=True)
    return cache_dir / f"{asset.lower()}_history.parquet"


@lru_cache(maxsize=10)
def fetch_historical_data(asset: str, start_date: datetime = None) -> pd.DataFrame:
    """
    Fetch daily historical data for a given asset
    Returns a Pandas DataFrame with columns: date, open, high, low, close, volume
    Uses both parquet caching and function memoization
    """
    ticker = get_ticker_symbol(asset)
    if not ticker:
        raise ValueError(f"Unknown asset: {asset}")

    if start_date is None:
        start_date = datetime(2010, 1, 1)  # Default start date

    cache_file = get_cache_path(asset)

    # Try to load cached data
    if cache_file.exists():
        cached_df = pd.read_parquet(cache_file)
        earliest_cached_date = cached_df["date"].min()
        latest_cached_date = cached_df["date"].max()

        need_earlier_data = start_date < earliest_cached_date
        need_later_data = latest_cached_date < datetime.now().date()
        
        if need_earlier_data or need_later_data:
            # Fetch missing historical data
            ticker_data = yf.Ticker(ticker)
            
            if need_earlier_data:
                # Fetch earlier data
                early_df = ticker_data.history(start=start_date, end=earliest_cached_date)
                if not early_df.empty:
                    early_df = early_df.reset_index()
                    early_df = early_df.rename(columns={"Date": "date"})
                    early_df["date"] = pd.to_datetime(early_df["date"]).dt.date
                    cached_df = pd.concat([early_df, cached_df])
            
            if need_later_data:
                # Fetch newer data
                new_start_date = latest_cached_date + timedelta(days=1)
                new_df = ticker_data.history(start=new_start_date)
                if not new_df.empty:
                    new_df = new_df.reset_index()
                    new_df = new_df.rename(columns={"Date": "date"})
                    new_df["date"] = pd.to_datetime(new_df["date"]).dt.date
                    cached_df = pd.concat([cached_df, new_df])
            
            # Save updated cache
            cached_df = cached_df.sort_values("date")
            cached_df.to_parquet(cache_file)

        return cached_df[cached_df["date"] >= start_date]

    # If no cache exists, fetch all data
    ticker_data = yf.Ticker(ticker)
    df = ticker_data.history(start=start_date)

    # Clean up DataFrame
    df = df.reset_index()
    df = df.rename(columns={"Date": "date"})
    df["date"] = pd.to_datetime(df["date"]).dt.date

    # Cache the data
    df.to_parquet(cache_file)
    return df
