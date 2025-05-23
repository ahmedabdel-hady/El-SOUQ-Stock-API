import streamlit as st
import yfinance as yf
from datetime import date
from prophet import Prophet
from prophet.plot import plot_plotly
import pandas as pd
from plotly import graph_objs as go
import requests
import json
import constants

# Constants
countries = constants.countries
api_key = 'd11f123b13714c05b3ee95bb809265af'


def business_news_feed():
    select_country = st.sidebar.selectbox("Select Country: ", countries.keys())
    st.header('NEWS FEED')
    url = f'https://newsapi.org/v2/top-headlines?country={countries[select_country]}&category=business&apikey={api_key}'
    try:
        r = requests.get(url)
        data_news = r.json()
        articles = data_news.get('articles', [])
        for i in range(min(15, len(articles))):
            article = articles[i]
            st.subheader(article['title'])
            if article['urlToImage']:
                st.image(article['urlToImage'])
            st.write(article.get('content', 'No content available'))
            st.write(article['url'])
    except Exception as e:
        st.error(f"Failed to load news: {e}")


def load_data(ticker, start, end):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(start=start, end=end)
        df.reset_index(inplace=True)
        return df
    except Exception as e:
        st.error(f"Failed to load stock data for {ticker}: {e}")
        return pd.DataFrame()


def sideBarHelper(text):
    st.sidebar.text(text)


def populateSideBar(stock_data, ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        st.sidebar.header(info.get('shortName', ticker))
        sideBarHelper("Sector: " + str(info.get('sector', 'N/A')))
        sideBarHelper("Currency: " + str(info.get('financialCurrency', 'N/A')))
        sideBarHelper("Exchange: " + str(info.get('exchange', 'N/A')))
        st.sidebar.markdown("[Visit Website](%s)" % info.get('website', '#'))
    except Exception as e:
        st.sidebar.error(f"Sidebar info not available: {e}")


# MAIN APP
st.title("Stock Price Forecast App")

# Input
ticker_input = st.text_input("Enter Stock Ticker", value="AAPL")
START = st.date_input("Start Date", date(2015, 1, 1))
TODAY = st.date_input("End Date", date.today())

# Load data
data = load_data(ticker_input, START, TODAY)

if not data.empty:
    populateSideBar(data, ticker_input)

    # Show raw data
    st.subheader('Raw Data')
    st.write(data.tail())

    # Forecasting
    df_train = data[['Date', 'Close']]
    df_train = df_train.rename(columns={"Date": "ds", "Close": "y"})

    m = Prophet()
    m.fit(df_train)
    future = m.make_future_dataframe(periods=365)
    forecast = m.predict(future)

    st.subheader('Forecast Data')
    st.write(forecast.tail())

    st.subheader('Forecast Chart')
    fig1 = plot_plotly(m, forecast)
    st.plotly_chart(fig1)

    st.subheader("Closing Price vs Time Chart")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=data['Date'], y=data['Close'], name='Close Price'))
    st.plotly_chart(fig2)

# Show news
business_news_feed()
