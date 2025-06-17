import streamlit as st
from datetime import date
from fbprophet import Prophet
from fbprophet.plot import plot_plotly
import pandas as pd
from plotly import graph_objs as go
import yfinance as yf
import requests
import constants
import json

countries = constants.countries

# Replace 'api_key' with your actual API key
api_key = 'f2cb4ed05496493589aabeb3bbb38699'


def business_news_feed():
    select_country = st.sidebar.selectbox("Select Country: ", countries.keys())
    st.header('NEWS FEED')
    r = requests.get('https://newsapi.org/v2/top-headlines?country=' + countries[select_country] + '&category=business&apikey=' + api_key)
    data_news = json.loads(r.content)
    length = min(15, len(data_news['articles']))
    for i in range(length):
        news = data_news['articles'][i]['title']
        st.subheader(news)
        image = data_news['articles'][i]['urlToImage']
        try:
            st.image(image)
        except:
            pass
        content = data_news['articles'][i]['content']
        st.write(content)
        url = data_news['articles'][i]['url']
        st.write(url)


def isLeapYear(y):
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)


def load_data(ticker):
    df = yf.download(ticker, start=START, end=TODAY)
    df.reset_index(inplace=True)
    return df


def plot_raw_data():
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data['Date'], y=data['Open'], name="stock_open"))
    fig.add_trace(go.Scatter(x=data['Date'], y=data['Close'], name="stock_close"))
    fig.layout.update(title_text='Time Series data with Rangeslider', xaxis_rangeslider_visible=True)
    st.plotly_chart(fig)

    fig = go.Figure()
    lastThirtyDays = data.tail(30)
    fig.add_trace(go.Candlestick(x=lastThirtyDays['Date'], open=lastThirtyDays['Open'], high=lastThirtyDays['High'],
                                 low=lastThirtyDays['Low'], close=lastThirtyDays['Close']))
    fig.layout.update(title_text='Candle Stick Chart - Past 30 Days Trend', xaxis_rangeslider_visible=True)
    st.plotly_chart(fig)


def predictingTheStockPrices():
    period = 0
    n_years = st.slider('Years of prediction:', 1, 4)
    for i in range(0, n_years):
        if isLeapYear(year + i):
            period += 366
        else:
            period += 365

    df_train = data[['Date', 'Close']].rename(columns={"Date": "ds", "Close": "y"})
    df_train['cap'] = df_train["y"].max() + df_train["y"].std() * 0.05

    m = Prophet(daily_seasonality=False, weekly_seasonality=False, yearly_seasonality=True,
                seasonality_mode="multiplicative", growth="logistic")
    m.add_seasonality(name="monthly", period=30, fourier_order=10)
    m.add_seasonality(name="quarterly", period=92.25, fourier_order=10)
    m.fit(df_train)

    future = m.make_future_dataframe(periods=period)
    future['cap'] = df_train['cap'].max()
    forecast = m.predict(future)

    st.subheader('Forecast data')
    st.write(forecast)
    st.write(f'Forecast plot for {n_years} years')
    fig1 = plot_plotly(m, forecast)
    st.plotly_chart(fig1)
    st.write("Forecast components - Yearly, Monthly and Quarterly Trends")
    fig2 = m.plot_components(forecast)
    st.write(fig2)


# Driver
START = "2016-01-01"
TODAY = date.today().strftime("%Y-%m-%d")
year = int(TODAY[:4])

st.title('ElSOUQ: STOCK FORECAST APP')

try:
    option = st.sidebar.selectbox("Which Dashboard?", ('Past Trends', 'Predict Stock Price', 'Trending Business News'), 0)
    stock = st.sidebar.text_input("Symbol", value='GOOG')
    selected_stock = stock.upper()

    data = load_data(selected_stock)

    if data is None or data.empty:
        st.error("No data available for the selected symbol. Please try a different one.")
        st.stop()

    if option == 'Past Trends':
        st.subheader(f"{selected_stock}'s Stocks")
        past_5_days = data.tail(5)
        st.write(past_5_days)
        plot_raw_data()

    elif option == 'Predict Stock Price':
        st.subheader(f"{selected_stock}'s Stock Forecast")
        predictingTheStockPrices()

    elif option == 'Trending Business News':
        business_news_feed()

except Exception as e:
    st.error(f"An error occurred: {e}")
