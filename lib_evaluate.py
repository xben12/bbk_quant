import numpy as np
import pandas as pd

class InvestPerformance(object):

    def __init__(self):
        self.dfp = pd.DataFrame()

    @staticmethod
    def get_vol_fullupdown(x):
        full = np.std(x)
        up_x = x[x>0]
        up = np.sqrt(np.sum(up_x*up_x) / len(x) )
        down_x = x[x<0]
        down = np.sqrt(np.sum(down_x*down_x) / len(x) )
        return (full, up, down)

    @staticmethod
    def count_pct_pos_neg_zero( x):
        pct_abv_0 = (x>0).sum()/len(x)
        pct_blw_0 = (x<0).sum()/len(x)
        pct_0 = 1 - pct_abv_0 - pct_blw_0
        return (pct_abv_0, pct_blw_0, pct_0)

    def evaluate(self, df, return_cols = ['strategy'], return_labels = None, bench_rate = 0.03):
        list_rst = []
        for col in return_cols:
            rst = self._strategy_performance(df, return_col = col, bench_rate = bench_rate)
            list_rst.append(rst)
        
        if return_labels is None:
            labels = return_cols
        
        if len(return_cols) == 1:
            return list_rst[0]
        
        if len(return_labels) != len(return_cols):
            raise "input error"
        
        for i in range(len(return_cols)):
            self.add_to_df(list_rst[i], return_labels[i])
            
        return self.dfp
        

    def _strategy_performance(self, df,return_col = 'strategy', bench_rate = 0.03):
        rst = {}

        total_days = len(df)

        total_return = np.exp( df[return_col].sum() ) -1

        df['cum_ret'] = df[return_col].cumsum().apply(np.exp)
        df['cum_max'] = df['cum_ret'].cummax()
        df['drawdown'] = (df['cum_ret'] - df['cum_max'])/df['cum_max']
        max_drawdown = df['drawdown'].min()

        days_vs0 = InvestPerformance.count_pct_pos_neg_zero(df[return_col]) 
        vol_list = InvestPerformance.get_vol_fullupdown(df[return_col])

        num_years = total_days/365
        total_return_annual = np.exp( df[return_col].sum()/num_years ) -1
        sharpe_annual = (total_return_annual - bench_rate) / (vol_list[0] * np.sqrt(365) )
        sortino_annual = (total_return_annual - bench_rate) /(vol_list[2] * np.sqrt(365) )

        rst={'total_return':total_return, 'max_drawdown':max_drawdown, 
        'daily_std_vol':vol_list[0] , 'daily_upside_vol':vol_list[1], 'daily_downside_vol':vol_list[2],
        'total_return_annual': total_return_annual,
        'sharpe':sharpe_annual, 'sortino':sortino_annual,
        'total_days': total_days,
        'days_positive': days_vs0[0], 'days_negative':days_vs0[1], 'days_exact0':days_vs0[2]
        }

        return rst
    
    def add_to_df(self, rst, label):
        df_now = pd.DataFrame(rst, index=[label])
        if self.dfp.empty:
            self.dfp = df_now
        else:
            self.dfp = pd.concat((self.dfp, df_now)) # self.dfp.append(df_now)
            
        return self.dfp
    
