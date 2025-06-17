import yfinance as yf

data = yf.download("AAPL", start="2016-01-01", end="2025-06-01")
print(data.head())