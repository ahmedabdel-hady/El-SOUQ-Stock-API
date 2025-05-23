import streamlit as st
from datetime import date
import yfinance as yf
from prophet import Prophet
from prophet.plot import plot_plotly
import pandas as pd
from plotly import graph_objs as go
import requests
import json

# Constants
START = "2016-01-01"
TODAY = date.today().strftime("%Y-%m-%d")
year = int(TODAY[:4])
api_key = 'd11f123b13714c05b3ee95bb809265af'

countries = {
    "United States": "us",
    "United Kingdom": "gb",
    "Germany": "de",
    "France": "fr",
    "Egypt": "eg",
    "United Arab Emirates": "ae",
    "China": "cn",
    "Japan": "jp"
}

def business_news_feed():
    select_country = st.sidebar.selectbox("Select Country: ", countries.keys())
    st.header('NEWS FEED')
    r = requests.get(f'https://newsapi.org/v2/top-headlines?country={countries[select_country]}&category=business&apikey={api_key}')
    data_news = json.loads(r.content)
    for i, article in enumerate(data_news.get('articles', [])[:15]):
        st.subheader(article['title'])
        if article.get('urlToImage'):
            st.image(article['urlToImage'])
        st.write(article.get('content', 'No content available'))
        st.write(article['url'])

def isLeapYear(y):
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)

def stockPricesToday(selection, data):
    try:
        current = selection.info.get('currentPrice')
        open_ = selection.info.get('open')
        change_today = current - open_ if current and open_ else None

        previous = data['Close'].iloc[-2] if len(data) > 1 else None
        latest = data['Close'].iloc[-1] if len(data) > 0 else None
        change_yesterday = latest - previous if previous and latest else None

        col1, col2 = st.columns(2)
        if change_today is not None:
            col1.metric("Current Price vs Open", f"{current:.2f}", f"{change_today:.2f}")
        else:
            col1.warning("Missing current/open price data.")

        if change_yesterday is not None:
            col2.metric("Yesterday's Close vs Day Before", f"{latest:.2f}", f"{change_yesterday:.2f}")
        else:
            col2.warning("Not enough data for daily change.")

        df = pd.DataFrame({
            'Current Price': [current],
            'Previous Close': [selection.info.get('previousClose')],
            'Open': [open_],
            'Day Low': [selection.info.get('dayLow')],
            'Day High': [selection.info.get('dayHigh')]
        })
        st.dataframe(df)
    except Exception as e:
        st.error(f"Error displaying stock prices: {e}")

def load_data(ticker):
    df = yf.download(ticker, start=START, end=TODAY)
    df.reset_index(inplace=True)
    return df

def plot_raw_data(df):
    st.subheader("Stock Time Series")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Open'], name="Open"))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], name="Close"))
    fig.update_layout(title_text='Time Series', xaxis_rangeslider_visible=True)
    st.plotly_chart(fig)

    st.subheader("Last 30 Days Candlestick")
    fig2 = go.Figure()
    last30 = df.tail(30)
    fig2.add_trace(go.Candlestick(
        x=last30['Date'],
        open=last30['Open'],
        high=last30['High'],
        low=last30['Low'],
        close=last30['Close']
    ))
    fig2.update_layout(xaxis_rangeslider_visible=True)
    st.plotly_chart(fig2)

def pastTrends(selection, df):
    st.subheader("Company Summary")
    st.info(selection.info.get('longBusinessSummary', 'No summary available.'))
    st.subheader("Today")
    stockPricesToday(selection, df)
    st.subheader("Last 5 Days")
    st.write(df.tail())

def predictingTheStockPrices(df):
    st.subheader("Forecasting")
    n_years = st.slider("Years of prediction:", 1, 4)
    future_days = sum(366 if isLeapYear(year + i) else 365 for i in range(n_years))

    df_train = df[['Date', 'Close']].rename(columns={"Date": "ds", "Close": "y"})
    df_train['cap'] = df_train["y"].max() + df_train["y"].std() * 0.05

    m = Prophet(growth="logistic", yearly_seasonality=True, seasonality_mode='multiplicative')
    m.add_seasonality(name="monthly", period=30.5, fourier_order=5)
    m.fit(df_train)

    future = m.make_future_dataframe(periods=future_days)
    future['cap'] = df_train['cap'].max()

    forecast = m.predict(future)

    st.subheader("Forecast Data")
    st.write(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail())

    st.plotly_chart(plot_plotly(m, forecast))

# Streamlit interface
st.title("📈 Stock Forecast App")
selected_stock = st.text_input("Enter a stock ticker (e.g. AAPL, GOOG):", "AAPL")

stock_data = load_data(selected_stock)
stock_selection = yf.Ticker(selected_stock)

tabs = st.tabs(["📊 Historical Trends", "🔮 Forecast", "🗞️ Business News"])
with tabs[0]:
    pastTrends(stock_selection, stock_data)
    plot_raw_data(stock_data)

with tabs[1]:
    predictingTheStockPrices(stock_data)

with tabs[2]:
    business_news_feed()
