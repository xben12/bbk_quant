import requests
from datetime import datetime, timedelta
import pandas as pd
import os


TOKEN_INFO = {'btc':'bitcoin', 'eth':'ethereum', 'sol':'solana'}

def get_token_csv_name(token, vs_currency = 'usd', info = 'price'):
    if info == 'price':
        return "output/price_"+token+"_vs_"+vs_currency+".csv"
    else:
        return "output/volume_"+token+"_vs_"+vs_currency+".csv"



def get_token_price_from_csv_dates(token,start_date, end_date):
    df = get_token_price_volume_from_csv(token)
    df = df_filter_date(df, start_date, end_date)
    return df


def df_filter_date(df, start_date, end_date, col = 'index'):
    start_date = todatetime(start_date)
    end_date = todatetime(end_date)
    
    fv= df.index
    if col != 'index':
        fv = df[col]
    df = df[(fv>= start_date) & (fv<= end_date)]
    return df.copy()

def get_token_price_volume_from_csv(token,vs_currency = 'usd' ):
    dfp = get_token_price_from_csv(token,vs_currency = vs_currency, info = 'price' )
    dfv = get_token_price_from_csv(token,vs_currency = vs_currency, info = 'volume' )
    df=dfp.merge(dfv[['volume']],how='left',left_index=True, right_index=True)
    return df


def get_token_price_from_csv(token,vs_currency = 'usd', info = 'price' ):
    f_name = get_token_csv_name(token, vs_currency, info)
    
    if not os.path.exists(f_name):
        token_name = None
        download_hist_daily_crypto_price(token_name, token, start_date='2015-01-01', end_date = datetime.now(),  vs_currency='usd')

    df = pd.read_csv(f_name, parse_dates=True)
    df['date'] = pd.to_datetime(df['date'])
    df.index = df['date']
    df.sort_index(ascending=True, inplace=True)
    return df

def todatetime(date_in, format = '%Y-%m-%d'):
    if(isinstance(date_in, datetime)):
        return date_in
    return datetime.strptime(date_in, format)

def download_hist_daily_crypto_price( token, start_date, end_date, token_name=None, vs_currency='usd'):
    if(not isinstance(start_date, datetime)):
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    if(not isinstance(end_date, datetime)):
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    days_btw = (end_date - start_date).days+10 # get a few more days and later fitler out

    token_name = TOKEN_INFO[token] if token_name is None else token_name

    url = f"https://api.coingecko.com/api/v3/coins/{token_name}/market_chart"
    params = {
        'vs_currency': vs_currency,
        'from': int(start_date.timestamp()),
        'to': int(end_date.timestamp()),
        'interval': 'daily',
        'days': days_btw
    }

    response = requests.get(url, params=params)
    if(response.status_code != 200) : # error of request
        print(f"Error: {response.status_code}")
        print(response.text)
        return None
    
    data = response.json()
    prices = data.get('prices', [])

    df = pd.DataFrame(prices, columns=['date', 'price'])
    df['date'] = pd.to_datetime(df['date']/1000, unit='s') # 
    df = df[(df.date>= start_date) & (df.date<= end_date)]
    df['token'] = str.upper(token)
    df['vs_currency'] = vs_currency
    df = df[['date', 'token', 'vs_currency', 'price']]

    df.index = df['date']
    df['date'] =  df['date'].dt.strftime("%Y-%m-%d")
    df.sort_index(ascending=False, inplace=True)

    # Remove duplicates by taking the last value for each date
    df = df[~df.index.duplicated(keep='last')]
    df = df[(df.index>= start_date) & (df.index<= end_date)]
    df.to_csv(get_token_csv_name(token, vs_currency),index=False)
    return df


def download_hist_daily_volume(token= "btc", begin_date = datetime(2015,1,1), end_date = None,  vs_currency = 'usd'):

    # Base URL for the CoinGecko API
    base_url = "https://api.coingecko.com/api/v3"

    crypto_id= TOKEN_INFO[token]

    if end_date is None:
        dtnow = datetime.now()
        end_date = datetime(dtnow.year, dtnow.month, dtnow.day)

    # Construct the endpoint URL for historical market data
    endpoint = f"/coins/{crypto_id}/market_chart/range"
    params = {
        "vs_currency": vs_currency,
        "from": begin_date.timestamp(),
        "to": end_date.timestamp(),
    }

    # Construct the full URL
    url = base_url + endpoint

    # Make a GET request to the endpoint
    response = requests.get(url, params=params)

    # Check if the request was successful (status code 200)
    if response.status_code != 200:
        # Print error details
        print(f"Error: {response.status_code} - {response.reason}")
        
        # Print the full URL for debugging
        print("URL:", response.url)

    data = response.json()
        
    df = pd.DataFrame(data['total_volumes'], columns=['date', 'volume']) 
    df['date'] = pd.to_datetime(df['date']/1000, unit='s') # 
    df = df[(df.date>= start_date) & (df.date<= end_date)]
    
    df['token'] = str.upper(token)
    df['vs_currency'] = vs_currency
    df = df[['date', 'token', 'vs_currency', 'volume']]
    
    df['date'] =  df['date'].dt.strftime("%Y-%m-%d")
    df.sort_values(by='date', inplace=True)


    # Remove duplicates by taking the last value for each date
    df.index = df['date']
    df = df[~df.index.duplicated(keep='last')]
    
    df.to_csv(get_token_csv_name(token, vs_currency,info = 'volume'),index=False)
    
    return df




# Check if the script is being run as the main program
if __name__ == "__main__":

    download_price_related_data = False;
    if download_price_related_data: # getting pool fee/vol related data
        # Set the start and end date
        start_date = datetime(2013, 1, 1)
        end_date = datetime.now() - timedelta(days=1)

        df_price = download_hist_daily_crypto_price('btc', start_date, end_date, 'bitcoin', vs_currency='usd')
        df_price = download_hist_daily_crypto_price('eth', start_date, end_date, 'ethereum', vs_currency='usd')
        df_price = download_hist_daily_crypto_price('sol', start_date, end_date,'solana', vs_currency='usd')

    download_volume_data = True;
    if download_volume_data: # getting pool fee/vol related data
        # Set the start and end date
        start_date = datetime(2013, 1, 1)
        end_date = datetime.now() - timedelta(days=1)

        df_price = download_hist_daily_volume('btc', start_date, end_date, vs_currency='usd')
        #df_price = download_hist_daily_volume('eth', start_date, end_date, vs_currency='usd')
        #df_price = download_hist_daily_volume('sol', start_date, end_date, vs_currency='usd')



    df_btc = get_token_price_from_csv('btc')
    print('\n price info')
    print(df_btc.head(2))
    
    df_btc = get_token_price_from_csv('btc', info = 'volume')
    print('\n price info')
    print(df_btc.head(2))