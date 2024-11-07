import yfinance as yf
import polars as pl
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
def fetch_historical_data(asset: str, start_date: datetime = None) -> pl.DataFrame:
    """
    Fetch daily historical data for a given asset
    Returns a Polars DataFrame with columns: date, open, high, low, close, volume
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
        cached_df = pl.read_parquet(cache_file)
        latest_date = cached_df["date"].max()
        
        # If we need older data than what's cached
        if start_date < latest_date:
            return cached_df.filter(pl.col("date") >= start_date)
            
        # If we need to fetch new data
        if latest_date < datetime.now().date():
            new_start_date = latest_date + timedelta(days=1)
            ticker_data = yf.Ticker(ticker)
            new_df = ticker_data.history(start=new_start_date)
            
            if not new_df.empty:
                new_pl_df = pl.from_pandas(new_df.reset_index()).with_columns([
                    pl.col("Date").cast(pl.Date).alias("date")
                ]).select([
                    "date",
                    "Open",
                    "High",
                    "Low",
                    "Close",
                    "Volume"
                ])
                
                # Combine and save updated data
                combined_df = pl.concat([cached_df, new_pl_df])
                combined_df.write_parquet(cache_file)
                return combined_df.filter(pl.col("date") >= start_date)
                
        return cached_df.filter(pl.col("date") >= start_date)
    
    # If no cache exists, fetch all data
    ticker_data = yf.Ticker(ticker)
    df = ticker_data.history(start=start_date)
    
    # Convert to Polars and clean up
    pl_df = pl.from_pandas(df.reset_index()).with_columns([
        pl.col("Date").cast(pl.Date).alias("date")
    ]).select([
        "date",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume"
    ])
    
    # Cache the data
    pl_df.write_parquet(cache_file)
    return pl_df
