import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

RATES_DICT = {'3m':'^IRX', '5y':'^FVX', '10y':'^TNX', '30y':'^TYX'}
INDEX_DICT = {'^SPX':'Large 500', '^MID':'Middle 400', '^SP600':'Small 600', '^NDX':"Nasdaq 100", '^RLV':'Russell 100 value'}
US_MAJOR_INDEX = ['SPX', 'NDX', 'MID', 'SP600' ]

def get_index_price(ticker, str_date_begin='2023-01-01', str_date_end = '2100-01-01', label = None):
    if label is None:
        label = ticker
    treasury_data = yf.download(ticker, start=str_date_begin, end=str_date_end)
    df = treasury_data[['Adj Close']]
    df = df.rename(columns = {'Adj Close':label})
    return df

def get_rates(list_rates, str_date_begin='2023-01-01', str_date_end = '2100-01-01'):
    
    list_df = []
    for rate in list_rates:
        ticker = RATES_DICT[rate]
        df = get_index_price(ticker, str_date_begin, str_date_end, label=rate) 
        list_df.append(df)
    combined_df = pd.concat(list_df, axis=1)
    return combined_df

def get_stocks_index(list_index, str_date_begin='2023-01-01', str_date_end = '2100-01-01'):
    
    list_df = []
    for idx in list_index:
        ticker =index_prefix_op(idx)
        df = get_index_price(ticker, str_date_begin, str_date_end, label=index_prefix_op(ticker, op = 'remove')) 
        list_df.append(df)
    combined_df = pd.concat(list_df, axis=1)
    return combined_df

def index_prefix_op(ticker, op = 'add', op_list = ['add', 'remove']):
    if op == 'add':
        if ticker[0] != '^':
            ticker = '^' + ticker
    elif op == 'remove':
        if ticker[0] == '^':
            ticker = ticker[1:]
    return ticker

def compute_period_return_risk(df, lookbacks = [3, 7, 14, 30]):

    p_chg_cols = []
    r_std_cols = []

    df['return'] = np.log(df['price']/df['price'].shift(1))
    for lb in lookbacks:
        col_p = f'prc_chg_{lb}'
        col_v = f'risk_std_{lb}'

        df[col_p] = df['return'].rolling(lb).mean()
        df[col_v] = df['return'].rolling(lb).std()
        p_chg_cols.append(col_p)
        r_std_cols.append(col_v)
    
    return df, p_chg_cols, r_std_cols

def get_tick_data(ticker, start_date = '2014-01-01', end_date = '2023-12-31'):
    df = yf.download(ticker, start=start_date, end=end_date)
    df['returns'] = np.log(df['Close']/df['Close'].shift(1))
    df = df.rename(columns={'Close':"price"})
    df['ticker'] = ticker
    return df[['price', 'returns']].copy()

def get_tick_risk(ticker, start_date = '2010-01-01', end_date = '2100-12-31', data = None, base_rate = 0.02 ):

    if data is None:
        # Fetch historical data from Yahoo Finance
        data = get_tick_data(ticker, start_date=start_date, end_date=end_date)
   

    data = data.sort_index( ascending=True)
    std = data['returns'].std() * np.sqrt(252)
    mu = data['returns'].mean()*252
    sharpe = (mu - base_rate)/std
    p=data['price'].dropna()
    pmax, pmin, pmean = p.max(), p.min(), p.mean()
    prange = (pmax - pmin)/pmean
    cur_p = data['price'].iloc[-1]
    
    return {"ret_mean":mu, "std":std, "sharpe":sharpe, 'prc_high':pmax, 'prc_low':pmin, 'prc_mean':pmean, 'prc_range_%': prange, 'cur_prc':cur_p}







if __name__ == '__main__':
    
    # related to sti ETF
    df_tickers = pd.read_csv("data/STI_comp.csv", index_col=False)
    sti_row = {"Symbol":"ES3.SI", "Company name":"STI ETF"}
    df_tickers.loc[len(df_tickers)] = sti_row
    df_tickers.tail(2)
    
    print("SG stocks:")
    tks = ['D05.SI', 'O39.SI', 'ES3.SI']
    list_df = [] 
    date_begin, date_end = datetime.now() - timedelta(days=365*2+1), datetime.now()
    str_date_begin, str_date_end = date_begin.strftime('%Y-%m-%d'), date_end.strftime('%Y-%m-%d')
    for tk in tks:
        rst_risk = get_tick_risk(tk, start_date = str_date_begin, end_date = str_date_end, base_rate = -0.02)
        df_t = pd.DataFrame(data =rst_risk, index = [tk] )
        list_df.append(df_t)
    print('date:', str_date_begin, str_date_end)
    print(pd.concat(list_df))