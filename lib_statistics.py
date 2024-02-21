import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.stattools import kpss
import nolds


def adf_test(time_series, label='data'):

    dict = {}

    # Perform the Augmented Dickey-Fuller (ADF) test
    result = adfuller(time_series)
    dict['stats'] = result[0]
    dict['p_value'] = result[1]
    critical_values = result[4]
    
    keys = ['1%', '5%', '10%']
    for key in keys:
        dict[key] = critical_values[key]

    dict['name'] = 'adf'
    dict['label'] = label
    return pd.DataFrame(data=dict,index=[label])

def kpss_test(time_series, label='data'):
    dict = {}
    # Perform the Kwiatkowski-Phillips-Schmidt-Shin (KPSS) test
    result = kpss(time_series)
    dict['stats'] = result[0]
    dict['p_value'] = result[1]
    critical_values = result[3]

    keys = ['1%', '5%', '10%']
    for key in keys:
        dict[key] = critical_values[key]

    dict['name'] = 'kpss'
    dict['label'] = label
    return pd.DataFrame(data=dict,index=[label])


def single_ts_stationary_test(df_col):

    data_by_year = {year: group for year, group in df_col.groupby(df_col.index.year)}

    years = sorted(list(data_by_year.keys()))

    list_adf = []
    list_kpss =[]
    list_hurst = []

    for year in years:
        data  = data_by_year[year]
        
        adf_rst = adf_test(data, label=year)
        list_adf.append(adf_rst)
        
        kpss_rst = kpss_test(data, label=year)
        list_kpss.append(kpss_rst)
        
        hurst_exponent = nolds.hurst_rs(data)
        list_hurst.append(hurst_exponent)
        
    df_adf = pd.concat(list_adf)
    df_kpss = pd.concat(list_kpss)
    return list_hurst, df_adf, df_kpss
    

import lib_data
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":

    df = lib_data.get_token_price_volume_from_csv('btc')

    begin_date = datetime(2016,1,1)
    end_date = datetime(2023,12,31)
    df = lib_data.df_filter_date(df, begin_date, end_date)
    df['volume'] = df['volume']/1e9

    df['prc_ret'] = np.log(df['price']/df['price'].shift(1))
    df['vol_ret'] = np.log(df['volume']/df['volume'].shift(1))
    df.dropna(inplace=True)
    print(df.head(2))

    list_hurst, df_adf, df_kpss = single_ts_stationary_test( df['price'])
    
    print("\n list_hurst", list_hurst)
    print("\n df_adf \n", df_adf)
    print("\n df_kpss \n", df_kpss)