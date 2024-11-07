import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List
import os
from functools import lru_cache
import pathlib

def get_ticker_symbol(asset: str) -> str:
    """Map asset names to their ticker symbols"""
    ticker_mapping = {
        "BTC": "BTC-USD",
        "ETH": "ETH-USD",
        "S&P500": "^GSPC",
        "NASDAQ-100": "^NDX"
    }
    return ticker_mapping.get(asset)

def get_cache_path(asset: str) -> pathlib.Path:
    """Get the path for cached parquet file"""
    cache_dir = pathlib.Path("cache")
    cache_dir.mkdir(exist_ok=True)
    return cache_dir / f"{asset.lower()}_history.parquet"

@lru_cache(maxsize=4)  # Cache for the 4 assets we support
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
        latest_date = cached_df["date"].max()
        
        # If we need older data than what's cached
        if start_date < latest_date:
            return cached_df[cached_df["date"] >= start_date]
            
        # If we need to fetch new data
        if latest_date < datetime.now().date():
            new_start_date = latest_date + timedelta(days=1)
            ticker_data = yf.Ticker(ticker)
            new_df = ticker_data.history(start=new_start_date)
            
            if not new_df.empty:
                new_df = new_df.reset_index()
                new_df = new_df.rename(columns={"Date": "date"})
                new_df["date"] = pd.to_datetime(new_df["date"]).dt.date
                
                # Combine and save updated data
                combined_df = pd.concat([cached_df, new_df])
                combined_df.to_parquet(cache_file)
                return combined_df[combined_df["date"] >= start_date]
                
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
