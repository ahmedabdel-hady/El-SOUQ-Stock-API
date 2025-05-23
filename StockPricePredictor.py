import streamlit as st
from datetime import date
from yahooquery import Ticker
from prophet import Prophet
from prophet.plot import plot_plotly
import pandas as pd
from plotly import graph_objs as go
import config
import requests
import constants
import json

countries = constants.countries

@st.cache_data
def get_ticker_data(stock_symbol):
    return Ticker(stock_symbol)

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

# Replace 'api_key' with your actual API key
api_key = 'd11f123b13714c05b3ee95bb809265af'

def isLeapYear(y):
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)

def sideBarHelper(text):
    st.sidebar.text(text)

def populateSideBar():
    # Get company name from available sources
    company_name = (
        selection.quotes[selected_stock].get('longName') or 
        selection.quotes[selected_stock].get('shortName') or 
        selected_stock
    )
    st.sidebar.header(company_name)
    
    try:
        sideBarHelper("Sector: " + selection.summary_profile[selected_stock]['sector'])
    except (KeyError, TypeError):
        pass
    
    try:
        sideBarHelper("Financial Currency: " + selection.financial_data[selected_stock]['financialCurrency'])
    except (KeyError, TypeError):
        pass
    
    try:
        sideBarHelper("Exchange: " + selection.quotes[selected_stock]['fullExchangeName'])
    except (KeyError, TypeError):
        pass
    
    try:
        sideBarHelper("Timezone: " + selection.quote_type[selected_stock]['timeZoneFullName'])
    except (KeyError, TypeError):
        pass
    
    try:
        url = selection.asset_profile[selected_stock]['website']
        st.sidebar.markdown("[Visit website](%s)" % url)
    except (KeyError, TypeError):
        pass
    
    try:
        st.sidebar.success(selection.financial_data[selected_stock]['recommendationKey'].capitalize())
    except (KeyError, TypeError):
        pass

def stockPricesToday():
    try:
        current_price = selection.financial_data[selected_stock].get('currentPrice', 'N/A')
        prev_close = selection.summary_detail[selected_stock].get('regularMarketPreviousClose', 'N/A')
        open_price = selection.summary_detail[selected_stock].get('open', 'N/A')
        day_low = selection.summary_detail[selected_stock].get('dayLow', 'N/A')
        day_high = selection.summary_detail[selected_stock].get('dayHigh', 'N/A')

        today_data = {
            'Current Price': [current_price],
            'Previous Close': [prev_close],
            'Open': [open_price],
            'Day Low': [day_low],
            'Day High': [day_high]
        }

        df = pd.DataFrame(today_data)
        col1, col2 = st.columns(2)
        
        try:
            priceChangeToday = current_price - open_price
            col1.metric(label="Current Price, Change w.r.t Opening Price", 
                       value=f'{current_price:.2f}' if isinstance(current_price, (int, float)) else current_price,
                       delta=f'{priceChangeToday:.2f}' if isinstance(priceChangeToday, (int, float)) else 'N/A')
        except (TypeError, KeyError):
            col1.metric(label="Current Price", value=current_price)

        try:
            priceChangeYesterday = data['close'][len(data) - 1] - data['close'][len(data) - 2] if len(data) >= 2 else 0
            col2.metric(label="Previous Closing, Previous Day Change", 
                       value=f"{data['close'][len(data) - 1]:.2f}",
                       delta=f"{priceChangeYesterday:.2f}")
        except (IndexError, KeyError):
            col2.metric(label="Previous Closing", value=prev_close)

        st.dataframe(df)
    except Exception as e:
        st.error(f"Could not load price data: {str(e)}")

@st.cache_data
def load_data(_ticker):
    try:
        historicData = _ticker.history(interval='1d', start=START, end=TODAY)
        historicData.reset_index(inplace=True)
        return historicData
    except Exception as e:
        st.error(f"Error loading historical data: {str(e)}")
        return pd.DataFrame()

def plot_raw_data():
    if data.empty:
        st.warning("No data available to plot")
        return

    # Plotting the raw data
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data['date'], y=data['open'], name="stock_open"))
    fig.add_trace(go.Scatter(x=data['date'], y=data['close'], name="stock_close"))
    fig.layout.update(
        title_text='Time Series data with Rangeslider', 
        xaxis_rangeslider_visible=True)
    st.plotly_chart(fig)

    if len(data) >= 30:
        fig = go.Figure()
        lastThirtyDays = data.tail(30)
        fig.add_trace(go.Candlestick(
            x=lastThirtyDays['date'], 
            open=lastThirtyDays['open'], 
            high=lastThirtyDays['high'],
            low=lastThirtyDays['low'],
            close=lastThirtyDays['close']
        ))
        fig.layout.update(
            title_text='Candle Stick Chart - Past 30 Days Trend', 
            xaxis_rangeslider_visible=True)
        st.plotly_chart(fig)
    else:
        st.warning("Not enough data for candlestick chart (need at least 30 days)")

def pastTrends():
    try:
        st.info(selection.asset_profile[selected_stock]['longBusinessSummary'])
    except (KeyError, TypeError):
        pass
    
    st.subheader('Today')
    stockPricesToday()

    st.subheader('Last 5 Days Trend')
    st.write(data.tail() if not data.empty else "No data available")

def predictingTheStockPrices():
    if data.empty:
        st.error("No historical data available for prediction")
        return

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

    try:
        df_train['cap'] = df_train["y"].max() + df_train["y"].std() * 0.05
        m.fit(df_train)
        future = m.make_future_dataframe(periods=period)
        future['cap'] = df_train['cap'].max()
        forecast = m.predict(future)

        # Showing and plotting the forecast
        st.subheader('Forecast data')
        st.write(forecast)

        st.write(f'Forecast plot for {n_years} years')
        fig1 = plot_plotly(m, forecast)
        st.plotly_chart(fig1)

        st.write("Forecast components - Yearly, Monthly and Quarterly Trends")
        fig2 = m.plot_components(forecast)
        st.write(fig2)
    except Exception as e:
        st.error(f"Error in prediction: {str(e)}")

# Main Application
START = "2016-01-01"
TODAY = date.today().strftime("%Y-%m-%d")
year = int(TODAY[:4])

st.title('ElSOUQ: STOCK FORECAST APP')

try:
    option = st.sidebar.selectbox(
        "Which Dashboard?", 
        ('Past Trends', 'Predict Stock Price', 'Trending Business News'),
        0
    )
    stock = st.sidebar.text_input("Symbol", value='GOOG')
    selected_stock = stock.upper().strip()

    if not selected_stock:
        raise ValueError("Symbol cannot be empty")

    selection = get_ticker_data(selected_stock)
    data = load_data(selection)

    if option == 'Past Trends':
        company_name = (
            selection.quotes[selected_stock].get('longName') or 
            selection.quotes[selected_stock].get('shortName') or 
            selected_stock
        )
        st.subheader(f"{company_name}'s Stocks")
        populateSideBar()
        pastTrends()
        plot_raw_data()

    elif option == 'Predict Stock Price':
        company_name = (
            selection.quotes[selected_stock].get('longName') or 
            selection.quotes[selected_stock].get('shortName') or 
            selected_stock
        )
        st.subheader(f"{company_name}'s Stocks")
        populateSideBar()
        predictingTheStockPrices()

    elif option == 'Trending Business News':
        business_news_feed()

except KeyError as e:
    st.error(f'This company is not listed or data is not available! Error: {str(e)}')

except FileNotFoundError:
    st.error('No data is available about this stock!')

except TypeError as e:
    st.error(f'Data format error: {str(e)}')

except ValueError as e:
    st.error(str(e))

except ConnectionError:
    st.error('Could not connect to the internet :(')

except Exception as e:
    st.error(f'An unexpected error occurred: {str(e)}')
