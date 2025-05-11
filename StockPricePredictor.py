import streamlit as st
from datetime import date
import yfinance as yf  # Import yfinance instead of yahooquery
from prophet import Prophet
from prophet.plot import plot_plotly
import pandas as pd
from plotly import graph_objs as go
import config
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
    st.sidebar.header(selection.info['longName'])
    sideBarHelper("Sector: " + selection.info['sector'])
    sideBarHelper("Financial Currency: " + selection.info['currency'])
    sideBarHelper("Exchange: " + selection.info['exchange'])
    sideBarHelper("Timezone: " + selection.info['timezone'])
    url = selection.info['website']
    st.sidebar.markdown("[Visit website](%s)" % url)
    st.sidebar.success(selection.recommendations['buyHoldSell'].capitalize())

def stockPricesToday():
    today_data = {'Current Price': [selection.history(period='1d')['Close'].iloc[-1]],
                  'Previous Close': [selection.history(period='1d')['Close'].iloc[-2]],
                  'Open': [selection.history(period='1d')['Open'].iloc[-1]],
                  'Day Low': [selection.history(period='1d')['Low'].iloc[-1]],
                  'Day High': [selection.history(period='1d')['High'].iloc[-1]]
                  }

    df = pd.DataFrame(today_data)
    col1, col2 = st.columns(2)
    priceChangeToday = selection.history(period='1d')['Close'].iloc[-1] - \
        selection.history(period='1d')['Open'].iloc[-1]  # Current Price - Previous Closing
    col1.metric(label="Current Price, Change w.r.t Opening Price", value='%.2f' % selection.history(period='1d')['Close'].iloc[-1],
                delta='%.2f' % priceChangeToday)

    priceChangeYesterday = data['close'][len(data) - 1] - data['close'][len(data) - 2] if len(data) >= 2 else 0
    col2.metric(label="Previous Closing, Previous Day Change", value='%.2f' % data['close'][len(data) - 1],
                delta='%.2f' % priceChangeYesterday)

    st.dataframe(df)

# Use yfinance to load data
def load_data(symbol):
    data = yf.Ticker(symbol)
    historic_data = data.history(period="1y")  # Fetch data for 1 year by default
    historic_data.reset_index(inplace=True)
    return historic_data

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
    st.info(selection.info['longBusinessSummary'])
    st.subheader('Today')
    stockPricesToday()
    st.subheader('Last 5 Days Trend')
    st.write(data.tail())

def predictingTheStockPrices():
    period = 0
    n_years = st.slider('Years of prediction:', 1, 4)

    for i in range(0, n_years):
        if isLeapYear(year + i):
            period += 366
        else:
            period += 365

    df_train = data[['Date', 'Close']].rename(columns={"Date": "ds", "Close": "y"})
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
year = int(TODAY[: 4])

st.title('ElSOUQ: STOCK FORECAST APP')

try:
    option = st.sidebar.selectbox("Which Dashboard?", ('Past Trends', 'Predict Stock Price', 'Trending Business News'),
                                  0)
    stock = st.sidebar.text_input("Symbol", value='GOOG')
    selected_stock = stock

    data = load_data(selected_stock)

    if option == 'Past Trends':
        company_name = selected_stock
        st.subheader(company_name + "'s Stocks")
        populateSideBar()
        pastTrends()
        plot_raw_data()

    if option == 'Predict Stock Price':
        company_name = selected_stock
        st.subheader(company_name + "'s Stocks")
        populateSideBar()
        predictingTheStockPrices()

    if option == 'Trending Business News':
        business_news_feed()

except KeyError:
    st.error('This company is not listed !')

except FileNotFoundError:
    st.error('No data is available about this stock !')

except TypeError:
    st.error('No data is available about this stock !')

except ValueError:
    st.error('Symbol cannot be empty !')

except ConnectionError:
    st.error('Could not connect to the internet :(')
