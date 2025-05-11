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

    # Load the stock data
    data = load_data(selected_stock)

    if data is None:  # If no data is returned, show a warning
        st.warning("No data found for this symbol. Please try another symbol.")
    else:
        if option == 'Past Trends':
            company_name = selected_stock
            st.subheader(company_name + "'s Stocks")
            populateSideBar(data)  # Pass the data to the sidebar function
            pastTrends(data)

        if option == 'Predict Stock Price':
            company_name = selected_stock
            st.subheader(company_name + "'s Stocks")
            populateSideBar(data)  # Pass the data to the sidebar function
            predictingTheStockPrices(data)

        if option == 'Trending Business News':
            business_news_feed()

except KeyError:
    st.error('This company is not listed!')

except FileNotFoundError:
    st.error('No data is available about this stock!')

except TypeError:
    st.error('No data is available about this stock!')

except ValueError:
    st.error('Symbol cannot be empty!')

except ConnectionError:
    st.error('Could not connect to the internet :(')
