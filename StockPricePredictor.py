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
START = "2017-01-01"
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

# Functions

def business_news_feed():
    select_country = st.sidebar.selectbox("Select Country: ", countries.keys())
    st.header('NEWS FEED')
    r = requests.get(f'https://newsapi.org/v2/top-headlines?country={countries[select_country]}&category=business&apikey={api_key}')
    data_news = json.loads(r.content)
    length = min(15, len(data_news['articles']))
    for i in range(length):
        article = data_news['articles'][i]
        st.subheader(article['title'])
        try:
            st.image(article['urlToImage'])
        except:
            pass
        st.write(article.get('content', ''))
        st.write(article['url'])

def isLeapYear(y):
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)

def stockPricesToday(selection, data):
    today_data = {
        'Current Price': [selection.info.get('currentPrice')],
        'Previous Close': [selection.info.get('previousClose')],
        'Open': [selection.info.get('open')],
        'Day Low': [selection.info.get('dayLow')],
        'Day High': [selection.info.get('dayHigh')]
    }

    df = pd.DataFrame(today_data)
    col1, col2 = st.columns(2)
    try:
        price_change_today = selection.info['currentPrice'] - selection.info['open']
        col1.metric(label="Current Price, Change w.r.t Opening Price",
                    value=f"{selection.info['currentPrice']:.2f}",
                    delta=f"{price_change_today:.2f}")

        price_change_yesterday = data['Close'].iloc[-1] - data['Close'].iloc[-2] if len(data) >= 2 else 0
        col2.metric(label="Previous Closing, Previous Day Change",
                    value=f"{data['Close'].iloc[-1]:.2f}",
                    delta=f"{price_change_yesterday:.2f}")
    except:
        st.warning("Incomplete price data available.")

    st.dataframe(df)

def load_data(ticker_symbol):
    df = yf.download(ticker_symbol, start=START, end=TODAY)
    df.reset_index(inplace=True)
    return df

def plot_raw_data(data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data['Date'], y=data['Open'], name="Open"))
    fig.add_trace(go.Scatter(x=data['Date'], y=data['Close'], name="Close"))
    fig.update_layout(title_text='Time Series Data', xaxis_rangeslider_visible=True)
    st.plotly_chart(fig)

    fig2 = go.Figure()
    last30 = data.tail(30)
    fig2.add_trace(go.Candlestick(
        x=last30['Date'],
        open=last30['Open'],
        high=last30['High'],
        low=last30['Low'],
        close=last30['Close']
    ))
    fig2.update_layout(title_text='Last 30 Days - Candlestick', xaxis_rangeslider_visible=True)
    st.plotly_chart(fig2)

def pastTrends(selection, data):
    st.info(selection.info.get('longBusinessSummary', 'No summary available.'))
    st.subheader('Today')
    stockPricesToday(selection, data)
    st.subheader('Last 5 Days Trend')
    st.write(data.tail())

def predictingTheStockPrices(data):
    n_years = st.slider('Years of prediction:', 1, 4)
    period = sum(366 if isLeapYear(year + i) else 365 for i in range(n_years))

    df_train = data[['Date', 'Close']].rename(columns={"Date": "ds", "Close": "y"})
    df_train['cap'] = df_train["y"].max() + df_train["y"].std() * 0.05

    m = Prophet(
        daily_seasonality=False,
        weekly_seasonality=False,
        yearly_seasonality=True,
        seasonality_mode="multiplicative",
        growth="logistic"
    )
    m.add_seasonality(name="monthly", period=30, fourier_order=10)
    m.add_seasonality(name="quarterly", period=92.25, fourier_order=10)

    m.fit(df_train)
    future = m.make_future_dataframe(periods=period)
    future['cap'] = df_train['cap'].max()
    forecast = m.predict(future)

    st.subheader('Forecast data')
    st.write(forecast)
    st.subheader(f'Forecast plot for {n_years} years')
    st.plotly_chart(plot_plotly(m, forecast))
    st.write("Forecast components")
    st.write(m.plot_components(forecast))

# App Entry Point

st.title('ElSOUQ: STOCK FORECAST APP')

try:
    option = st.sidebar.selectbox("Which Dashboard?", ('Past Trends', 'Predict Stock Price', 'Trending Business News'), 0)
    stock = st.sidebar.text_input("Symbol", value='GOOG')
    selected_stock = stock.strip().upper()

    if selected_stock == "":
        raise ValueError("Symbol cannot be empty!")

    selection = yf.Ticker(selected_stock)
    data = load_data(selected_stock)

    if data.empty:
        st.error("No stock data available!")
    else:
        if option == 'Past Trends':
            st.subheader(selection.info.get('longName', selected_stock) + "'s Stocks")
            pastTrends(selection, data)
            plot_raw_data(data)

        elif option == 'Predict Stock Price':
            st.subheader(selection.info.get('longName', selected_stock) + "'s Stocks")
            predictingTheStockPrices(data)

        elif option == 'Trending Business News':
            business_news_feed()

except ValueError as ve:
    st.error(str(ve))
except Exception as e:
    st.error(f"Unexpected error: {str(e)}")
