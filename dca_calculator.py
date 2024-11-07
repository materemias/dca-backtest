from typing import Dict

import polars as pl


def resample_price_data(df: pl.DataFrame, periodicity: str) -> pl.DataFrame:
    """Resample price data according to investment frequency"""
    # Convert to pandas for easier resampling
    pdf = df.to_pandas().set_index("date")

    freq_map = {"Daily": "D", "Weekly": "W", "Monthly": "ME"}

    # Resample using pandas
    resampled = pdf.resample(freq_map[periodicity]).agg({"Close": "last", "Volume": "sum"}).reset_index()

    # Convert back to polars
    return pl.from_pandas(resampled)


def calculate_dca_metrics(df: pl.DataFrame, initial_investment: float, periodic_investment: float, periodicity: str) -> Dict:
    """Calculate DCA investment metrics"""

    # Resample data according to investment frequency
    resampled_df = resample_price_data(df, periodicity)

    # Calculate number of periods
    num_periods = len(resampled_df)

    # Calculate total investment
    total_investment = initial_investment + (periodic_investment * (num_periods - 1))

    # Calculate units bought at each period
    initial_units = initial_investment / resampled_df["Close"][0]
    periodic_units = [periodic_investment / price for price in resampled_df["Close"][1:]]
    total_units = initial_units + sum(periodic_units)

    # Calculate final value
    final_price = resampled_df["Close"].tail(1)[0]
    final_value = total_units * final_price

    # Calculate gains
    absolute_gain = final_value - total_investment
    percentage_gain = (absolute_gain / total_investment) * 100

    # Calculate average monthly gain
    months_elapsed = (resampled_df["date"].tail(1)[0] - resampled_df["date"][0]).days / 30.44  # Average days per month
    monthly_gain = (((final_value / total_investment) ** (1 / months_elapsed)) - 1) * 100

    return {
        "total_investment": round(total_investment, 2),
        "final_value": round(final_value, 2),
        "absolute_gain": round(absolute_gain, 2),
        "percentage_gain": round(percentage_gain, 2),
        "monthly_gain": round(monthly_gain, 2),
        "total_units": round(total_units, 6),
    }


def calculate_multi_asset_dca(asset_data: Dict[str, pl.DataFrame], params: Dict) -> Dict[str, Dict]:
    """Calculate DCA metrics for multiple assets"""
    results = {}

    for asset, df in asset_data.items():
        results[asset] = calculate_dca_metrics(df, params["initial_investment"], params["periodic_investment"], params["periodicity"])

    return results
