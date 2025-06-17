import streamlit as st
from datetime import date
from fbprophet import Prophet
from fbprophet.plot import plot_plotly
import pandas as pd
from plotly import graph_objs as go
import requests
import constants
import json

# Replace this with your actual API key from Alpha Vantage
ALPHA_VANTAGE_API_KEY = 'JYNMGFMU4IRD9XH9'

countries = constants.countries

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

api_key = 'f2cb4ed05496493589aabeb3bbb38699'

def isLeapYear(y):
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)

def load_data(symbol):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&outputsize=full&apikey={ALPHA_VANTAGE_API_KEY}'
    response = requests.get(url)
    data = response.json()

    if 'Time Series (Daily)' not in data:
        return pd.DataFrame()

    df = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index')
    df = df.rename(columns={'1. open': 'open', '4. close': 'close'})
    df = df[['open', 'close']]
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)
    df.reset_index(inplace=True)
    df = df.rename(columns={'index': 'date'})
    df['open'] = df['open'].astype(float)
    df['close'] = df['close'].astype(float)
    return df

def plot_raw_data(data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data['date'], y=data['open'], name="stock_open"))
    fig.add_trace(go.Scatter(x=data['date'], y=data['close'], name="stock_close"))
    fig.layout.update(title_text='Time Series data with Rangeslider', xaxis_rangeslider_visible=True)
    st.plotly_chart(fig)

    fig = go.Figure()
    lastThirtyDays = data.tail(30)
    fig.add_trace(go.Candlestick(x=lastThirtyDays['date'], open=lastThirtyDays['open'], high=lastThirtyDays['open'],
                                 low=lastThirtyDays['close'], close=lastThirtyDays['close']))
    fig.layout.update(title_text='Candle Stick Chart - Past 30 Days Trend', xaxis_rangeslider_visible=True)
    st.plotly_chart(fig)

def predictingTheStockPrices(data):
    period = 0
    n_years = st.slider('Years of prediction:', 1, 4)

    for i in range(0, n_years):
        if isLeapYear(year + i):
            period += 366
        else:
            period += 365

    df_train = data[['date', 'close']]
    df_train = df_train.rename(columns={"date": "ds", "close": "y"})

    model_param = {
        "daily_seasonality": False,
        "weekly_seasonality": False,
        "yearly_seasonality": True,
        "seasonality_mode": "multiplicative",
        "growth": "logistic"
    }

    m = Prophet(**model_param)
    m = m.add_seasonality(name="monthly", period=30, fourier_order=10)
    m = m.add_seasonality(name="quarterly", period=92.25, fourier_order=10)

    df_train['cap'] = df_train["y"].max() + df_train["y"].std() * 0.05
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

    data = load_data(stock)

    if data is None or data.empty:
        st.error("No data available for the selected symbol. Please try a different one.")
        st.stop()

    if option == 'Past Trends':
        st.subheader(f"{stock} Stock Trends")
        st.subheader('Last 5 Days Trend')
        st.write(data.tail())
        plot_raw_data(data)

    elif option == 'Predict Stock Price':
        st.subheader(f"{stock} Stock Forecast")
        predictingTheStockPrices(data)

    elif option == 'Trending Business News':
        business_news_feed()

except Exception as e:
    st.error(f"An error occurred: {e}")
