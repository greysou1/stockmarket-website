# Stock Market Website

A web app via which you can manage portfolios of stocks. Not only will this tool allow you to check real stocks' actual prices and portfolios' values, it will also let you buy (okay, "buy") and sell (okay, "sell") stocks by querying AlphaVantage for stocks' prices.

## Usage

1. Install the required libraries using this command

`pip install -r requirements.txt`

2. This project does an API call to [AlphaAdvantage](https://www.alphavantage.co/documentation/)
   You need to get your own API key, simply head on to their website and [claim your free api key](https://www.alphavantage.co/support/#api-key)

3. Now open the "helpers.py" file and head on to line number 53.
   > url = f"https://www.alphavantage.co/query?apikey=yourapikey&datatype=csv&function=TIME_SERIES_INTRADAY&interval=1min&symbol={symbol}"

4. Now replace "yourapikey" with your API key.

5. Run the program 

`python3 application.py`

6. Run the server

`flask run`

7. Enter the address in browser



**Note**: If you're running into an error that says "You did not provide the "FLASK_APP" environment variable" run the following command before running step 3
`export FLASK_APP=application.py`

### Credits
[CS50X course by Harvard](https://www.edx.org/course/cs50s-introduction-computer-science-harvardx-cs50x) on EdX
This version of the repository is almost similar (borrowed code) to pset7 Finance in the course. 
Future releases to have stock predictions using sentiment analysis.
