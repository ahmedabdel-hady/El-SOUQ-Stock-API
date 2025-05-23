import streamlit as st
from datetime import date
import yfinance as yf
from prophet import Prophet
from prophet.plot import plot_plotly
import pandas as pd
from plotly import graph_objs as go
import config
import requests
import constants
import json

countries = constants.countries

# Replace 'api_key' with your actual API key
api_key = 'd11f123b13714c05b3ee95bb809265af'

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

def sideBarHelper(text):
    st.sidebar.text(text)

def populateSideBar():
    st.sidebar.header(selection.info.get('longName', 'N/A'))
    sideBarHelper("Sector: " + selection.info.get('sector', 'N/A'))
    sideBarHelper("Financial Currency: " + selection.info.get('financialCurrency', 'N/A'))
    sideBarHelper("Exchange: " + selection.info.get('exchange', 'N/A'))
    sideBarHelper("Timezone: " + selection.info.get('timeZoneFullName', 'N/A'))
    url = selection.info.get('website', '')
    if url:
        st.sidebar.markdown(f"[Visit website]({url})")
    st.sidebar.success(selection.info.get('recommendationKey', 'N/A').capitalize())

def stockPricesToday():
    today_data = {
        'Current Price': [selection.info.get('currentPrice', 0)],
        'Previous Close': [selection.info.get('previousClose', 0)],
        'Open': [selection.info.get('open', 0)],
        'Day Low': [selection.info.get('dayLow', 0)],
        'Day High': [selection.info.get('dayHigh', 0)]
    }

    df = pd.DataFrame(today_data)
    col1, col2 = st.columns(2)
    priceChangeToday = selection.info.get('currentPrice', 0) - selection.info.get('open', 0)
    col1.metric(label="Current Price, Change w.r.t Opening Price", value='%.2f' % selection.info.get('currentPrice', 0),
                delta='%.2f' % priceChangeToday)

    if len(data) >= 2:
        priceChangeYesterday = data['Close'].iloc[-1] - data['Close'].iloc[-2]
    else:
        priceChangeYesterday = 0

    col2.metric(label="Previous Closing, Previous Day Change", value='%.2f' % data['Close'].iloc[-1],
                delta='%.2f' % priceChangeYesterday)

    st.dataframe(df)

def load_data(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(interval='1d', start=START, end=TODAY)
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

def pastTrends():
    st.info(selection.info.get('longBusinessSummary', ''))
    st.subheader('Today')
    stockPricesToday()

# Streamlit app interface
st.title('Stock Price Predictor')
today = date.today()
START = "2015-01-01"
TODAY = today.strftime("%Y-%m-%d")

selected_stock = st.text_input('Enter stock ticker', 'AAPL')
selection = yf.Ticker(selected_stock)
data = load_data(selected_stock)

populateSideBar()
plot_raw_data()
pastTrends()
business_news_feed()
