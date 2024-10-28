import streamlit as st
from datetime import date
from prophet import Prophet
from prophet.plot import plot_plotly
import yfinance as yf
import pandas as pd
from plotly import graph_objs as go
import requests
import constants
import json

countries = constants.countries

def business_news_feed():
    select_country = st.sidebar.selectbox("Select Country: ", countries.keys())
    st.header('NEWS FEED')
    api_key = st.secrets["NEWS_API_KEY"]  # Uses st.secrets if configured
    r = requests.get(f'https://newsapi.org/v2/top-headlines?country={countries[select_country]}&category=business&apikey={api_key}')
    data_news = json.loads(r.content)
    length = min(15, len(data_news['articles']))
    for i in range(length):
        news = data_news['articles'][i]['title']
        st.subheader(news)
        st.image(data_news['articles'][i].get('urlToImage', None))
        st.write(data_news['articles'][i]['content'])
        st.write(data_news['articles'][i]['url'])

def isLeapYear(y):
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)

def load_data(stock_ticker):
    ticker = yf.Ticker(stock_ticker)
    return ticker.history(start=START, end=TODAY)

def plot_raw_data(data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['Open'], name="stock_open"))
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="stock_close"))
    fig.layout.update(title_text='Time Series data with Rangeslider', xaxis_rangeslider_visible=True)
    st.plotly_chart(fig)

def predictingTheStockPrices(data):
    n_years = st.slider('Years of prediction:', 1, 4)
    period = sum(366 if isLeapYear(year + i) else 365 for i in range(n_years))
    df_train = data[['Close']].rename(columns={"Close": "y"})
    df_train['ds'] = df_train.index
    model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
    model.fit(df_train)
    future = model.make_future_dataframe(periods=period)
    forecast = model.predict(future)
    st.write(forecast)
    fig1 = plot_plotly(model, forecast)
    st.plotly_chart(fig1)

START = "2016-01-01"
TODAY = date.today().strftime("%Y-%m-%d")
year = int(TODAY[:4])

st.title('ElSOUQ: STOCK FORECAST APP')

option = st.sidebar.selectbox("Which Dashboard?", ('Past Trends', 'Predict Stock Price', 'Trending Business News'))
stock = st.sidebar.text_input("Symbol", value='COMI.CA')

try:
    data = load_data(stock)
    if option == 'Past Trends':
        st.subheader(f"{stock}'s Stocks")
        plot_raw_data(data)
    elif option == 'Predict Stock Price':
        st.subheader(f"{stock}'s Stock Prediction")
        predictingTheStockPrices(data)
    elif option == 'Trending Business News':
        business_news_feed()
except Exception as e:
    st.error(f"Error: {str(e)}")
