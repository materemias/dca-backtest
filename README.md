# DCA Investment Calculator

A powerful Dollar Cost Averaging (DCA) backtesting tool that allows investors to analyze and compare DCA investment strategies across multiple assets.

🔗 **[Try it live here](https://dca-backtest.streamlit.app/)**

## Features

- **Multi-Asset Analysis**: Compare DCA performance across different assets (cryptocurrencies, stocks, ETFs)
- **Flexible Parameters**:
  - Customizable start and end dates
  - Adjustable initial and periodic investment amounts
  - Daily, weekly, or monthly investment frequencies
- **Comprehensive Metrics**:
  - Total investment and final value
  - Absolute and percentage gains
  - Monthly gain calculations
  - Maximum drawdown analysis
  - Buy & Hold comparison
- **Dynamic Visualizations**:
  - Investment vs. Value over time
  - Price performance relative to all-time highs
  - Performance comparison across assets
- **Advanced Features**:
  - Random date range testing
  - Parallel processing for quick results
  - Detailed individual test results
  - Custom ticker support with YFinance integration

## How to Use

1. Visit [https://dca-backtest.streamlit.app/](https://dca-backtest.streamlit.app/)
2. Select your assets from the sidebar
3. Set your investment parameters:
   - Start and end dates
   - Initial investment amount
   - Periodic investment amount
   - Investment frequency
4. Analyze the results through interactive charts and detailed metrics
5. Optionally run random tests to see how your strategy performs across different time periods

## Technical Details

Built with:
- Streamlit for the web interface
- Pandas for data manipulation
- Plotly for interactive visualizations
- YFinance for market data
- Multiprocessing for parallel computations

## Local Development

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Run the app:
```bash
streamlit run app.py
```

## Contributing

Feel free to open issues or submit pull requests with improvements.

## License

MIT License

## Disclaimer

This tool is for educational purposes only. Past performance does not guarantee future results. Always do your own research before making investment decisions.
