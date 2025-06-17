import streamlit as st
from datetime import date
from fbprophet import Prophet
from fbprophet.plot import plot_plotly
import pandas as pd
from plotly import graph_objs as go
import requests
import constants
import json
import time
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np

# Replace with your actual Alpha Vantage API key
ALPHA_VANTAGE_API_KEY = 'JYNMGFMU4IRD9XH9'
api_key = 'f2cb4ed05496493589aabeb3bbb38699'

countries = constants.countries


def business_news_feed():
    select_country = st.sidebar.selectbox("Select Country: ", countries.keys(), key="country")
    st.header('NEWS FEED')
    r = requests.get(f'https://newsapi.org/v2/top-headlines?country={countries[select_country]}&category=business&apikey={api_key}')
    data_news = json.loads(r.content)
    for article in data_news.get('articles', [])[:10]:
        st.subheader(article['title'])
        if article.get('urlToImage'):
            st.image(article['urlToImage'])
        st.write(article.get('content', 'No summary'))
        st.markdown(f"[Read more]({article['url']})")


def isLeapYear(y):
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)


def stockPricesToday():
    st.warning("Real-time stock metrics are unavailable in Alpha Vantage free tier. Showing last available close price.")
    st.dataframe(data.tail(1))


def load_data(symbol):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=full&apikey={ALPHA_VANTAGE_API_KEY}'
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
    df = df.astype({'open': float, 'close': float})
    return df


def plot_raw_data():
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data['date'], y=data['open'], name="stock_open"))
    fig.add_trace(go.Scatter(x=data['date'], y=data['close'], name="stock_close"))
    fig.update_layout(title_text='Time Series Data with Rangeslider', xaxis_rangeslider_visible=True)
    st.plotly_chart(fig)


def pastTrends():
    st.subheader('Today')
    stockPricesToday()
    st.subheader('Last 5 Days Trend')
    st.write(data.tail())


def predictingTheStockPrices():
    period = 0
    n_years = st.slider('Years of prediction:', 1, 4)
    for i in range(n_years):
        period += 366 if isLeapYear(year + i) else 365

    df_train = data[['date', 'close']].rename(columns={"date": "ds", "close": "y"})
    df_train['cap'] = df_train['y'].max() + df_train['y'].std() * 0.05

    m = Prophet(
        growth="logistic",
        daily_seasonality=False,
        weekly_seasonality=False,
        yearly_seasonality=True,
        seasonality_mode="multiplicative"
    )
    m.add_seasonality(name="monthly", period=30, fourier_order=10)
    m.add_seasonality(name="quarterly", period=92.25, fourier_order=10)

    start_time = time.time()
    m.fit(df_train)
    duration = time.time() - start_time

    future = m.make_future_dataframe(periods=period)
    future['cap'] = df_train['cap'].max()
    forecast = m.predict(future)

    st.subheader('Forecast data')
    st.write(forecast)
    st.write(f'Training Time: {duration:.2f} seconds')

    st.write(f'Forecast plot for {n_years} years')
    fig1 = plot_plotly(m, forecast)
    st.plotly_chart(fig1)

    st.write("Forecast components - Yearly, Monthly and Quarterly Trends")
    fig2 = m.plot_components(forecast)
    st.write(fig2)
    test_days = 60
    actual = df_train.set_index("ds")["y"].iloc[-test_days:]
    forecast.set_index("ds", inplace=True)
    predicted = forecast.loc[actual.index]["yhat"]

    mae = mean_absolute_error(actual, predicted)
    rmse = mean_squared_error(actual, predicted, squared=False)
    r2 = r2_score(actual, predicted)

    st.success(f"""✅ **Model Evaluation (Last {test_days} Days)**  
- **MAE**: {mae:.2f}  
- **RMSE**: {rmse:.2f}  
- **R² Score**: {r2:.2f}  
The model shows how accurately it forecasts recent stock performance.""")




# Driver
START = "2016-01-01"
TODAY = date.today().strftime("%Y-%m-%d")
year = int(TODAY[:4])

st.title('ElSOUQ: STOCK FORECAST APP')

try:
    option = st.sidebar.selectbox("Which Dashboard?", ('Past Trends', 'Predict Stock Price', 'Trending Business News'), 0)
    stock = st.sidebar.text_input("Symbol", value='AAPL')
    selected_stock = stock.upper()

    data = load_data(selected_stock)

    if data.empty:
        st.error("No data available for the selected symbol. Please try a different one.")
        st.stop()

    if option == 'Past Trends':
        st.subheader(selected_stock + " Stock")
        pastTrends()
        plot_raw_data()

    elif option == 'Predict Stock Price':
        st.subheader(selected_stock + " Stock")
        predictingTheStockPrices()

    elif option == 'Trending Business News':
        business_news_feed()

except Exception as e:
    st.error(f"Error: {e}")
