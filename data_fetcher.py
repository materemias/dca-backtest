import yfinance as yf
import polars as pl
from datetime import datetime, timedelta
from typing import List

def get_ticker_symbol(asset: str) -> str:
    """Map asset names to their ticker symbols"""
    ticker_mapping = {
        "BTC": "BTC-USD",
        "ETH": "ETH-USD",
        "S&P500": "^GSPC",
        "NASDAQ-100": "^NDX"
    }
    return ticker_mapping.get(asset)

def fetch_historical_data(asset: str, start_date: datetime = None) -> pl.DataFrame:
    """
    Fetch daily historical data for a given asset
    Returns a Polars DataFrame with columns: date, open, high, low, close, volume
    """
    ticker = get_ticker_symbol(asset)
    if not ticker:
        raise ValueError(f"Unknown asset: {asset}")
    
    if start_date is None:
        start_date = datetime(2010, 1, 1)  # Default start date
        
    # Fetch data using yfinance
    ticker_data = yf.Ticker(ticker)
    df = ticker_data.history(start=start_date)
    
    # Convert to Polars and clean up
    pl_df = pl.from_pandas(df).with_columns([
        pl.col("Date").cast(pl.Date).alias("date")
    ]).select([
        "date",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume"
    ])
    
    return pl_df
