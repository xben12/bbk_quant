
from lib_order import Orders
from lib_risk import Risk
from lib_alpha import Alpha

import lib_data
from lib_utils import Bbk_Utils
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

class Book(object):
    def __init__(self, symbol):
        self.symbol = symbol
        self.data_full = Bbk_Utils.load_price_data(symbol)
        self.data  = self.data_full.copy()
    
    def filter_underlying_data(self, date_begin, date_end, lead_days = 180):
        data_start_w_lead = date_begin - timedelta(days=lead_days)
        self.data = Bbk_Utils.filter_by_date(self.data_full, data_start_w_lead, date_end)

        
    def setup_alpha(self, mmt_list, vlt_list):
        self.alpha = Alpha(self.data)
        self.alpha.create_feature_mmt(mmt_list)
        self.alpha.create_feature_volatility(vlt_list)

    def setup_book_daily(self, start_date, end_date):
        
        df = Bbk_Utils.filter_by_date(self.data,start_date,end_date)
        added_cols = ['book_cash', 'book_token', 'book_token_net_pnl', 'day_pnl', 'book_nav', 
                      'book_max_v', 'book_drawdown', 
                      'order_id', 'daily_pnl', 'order_drawdown', 'stop_loss_limit']
        
        for col in added_cols:
            df[col] = [np.nan] * len(df)  # Add column to DataFrame
        self.book = df

    def setup_order_table(self):
        self.orders = Orders()

    def setup_risk(self, drawdown_pct = -0.05, coverage_pctl = 0.9, risk_window = 30):
        df_returns = self.data[['returns']]
        self.risk = Risk(drawdown_pct = drawdown_pct, 
                         coverage_pctl = coverage_pctl, 
                         risk_window = risk_window, 
                         df_returns = df_returns)

        
    def close_order(self, order_id, price):
        
        cash_delta, token_delta = self.orders.close_order(order_id, price)

        return cash_delta, token_delta

    def open_order(self, pos_new_scale, long_short, book_cash, token_price, date):
        pos_token = book_cash*pos_new_scale/token_price
        stop_loss_limit = self.risk.drawdown_loss_limit_from_total_ptf(book_cash)
        
        if(long_short == 1):
            token_delta = pos_token
            cash_delta =  - book_cash*pos_new_scale
        elif(long_short == -1 ):
            token_delta = - pos_token
            cash_delta = 0 # note cash is not reduced, whole amt is used as margin
        else:
            raise("error in long_short for open_order")
        
        order_id = self.orders.create_order(long_short, pos_new_scale, date, token_price, pos_token, stop_loss_limit,  entry_comments = "")
        
        return order_id, cash_delta, token_delta
    
    
    def get_set_book_record_by_date(self, date, bk_row = None, label = None):  
        if(bk_row is None):
            bk_row = self.book.loc[date]
        else: 
            self.book.loc[date] = bk_row

        if(label is not None):
            return bk_row[label]
        else:
            return bk_row
    

    def decide_on_new_trade(self, cur_date): 
        long_short = self.alpha.decide_on_new_trade_long_short(cur_date) 
        new_order_scale = self.risk.position_scale(cur_date = cur_date, long_short = long_short)
        b_new_order = long_short !=0 
        return b_new_order, long_short, new_order_scale
    
    def get_active_order(self, date):
        # active order is decide by day T-1
        yesterday = date - timedelta(days = 1)
        order_id = Orders.id_nan()
        is_order_valid = False
        
        if yesterday in self.book.index:
            order_id =  self.get_set_book_record_by_date(yesterday, label = 'order_id')
            if Orders.is_order_valid(order_id):
                is_order_valid = True
        
        return order_id, is_order_valid
    
        
    def update_book_order(self, date, cash_available, price_T):

        order_id, is_order_valid = self.get_active_order(date)
        cash_delta, token_delta, daily_pnl = 0, 0, 0
        
        if is_order_valid == True:    
            b_order_need_close, daily_pnl = self.orders.update_order_status(order_id, date, price_T)
            if b_order_need_close:
                cash_delta, token_delta = self.close_order(order_id, price_T)
                order_id = Orders.id_nan()

        else : # no position, check whether need to open
            b_new_order, long_short, new_order_scale = self.decide_on_new_trade(date)
            if b_new_order:
                order_id, cash_delta, token_delta = self.open_order(new_order_scale, long_short, cash_available, price_T, date)

        return cash_delta, token_delta, daily_pnl, order_id   


    @staticmethod
    def compute_book_nav(book_cash, book_token, book_token_net_pnl, price):
        if book_token >= 0 : # meaning long 
            nav = book_cash + book_token*price
        else :
            nav = book_cash + book_token_net_pnl
        return nav
            

    def run_book_daily(self):
    
        df_bk = self.book
        
        # initialisation for loop:
        book_cash, book_token, book_token_net_pnl  = self.amount, 0, 0
        
        for index, row in df_bk.iterrows():
            date = index
            price_T= row['price']

            cash_available = book_cash
            cash_delta, token_delta, daily_pnl, order_id = self.update_book_order(date, cash_available, price_T)

            # update circular value needed in loop
            book_cash = book_cash + cash_delta
            book_token =  book_token + token_delta
            book_token_net_pnl =  book_token_net_pnl + daily_pnl
            book_nav = Book.compute_book_nav(book_cash, book_token,book_token_net_pnl, price_T)
            
            # update book details section:
            book_cols_names = ['book_cash', 'book_token', 'book_token_net_pnl', 'day_pnl', 'book_nav']
            book_cols_val = [book_cash, book_token, book_token_net_pnl, daily_pnl, book_nav]
            row[book_cols_names] = book_cols_val
            
            # update order details section:
            order_cols_names = ['order_id',  'order_drawdown', 'stop_loss_limit']
            order_cols_val = self.orders.get_order_detail(order_id, label=order_cols_names)
            row[order_cols_names] = order_cols_val

            # write back to book
            df_bk.loc[index] = row

        df_bk['nav_returns'] = np.log(df_bk['book_nav']/df_bk['book_nav'].shift(1))
        df_bk['cstrategy'] = df_bk['nav_returns'].cumsum().apply(lambda x: np.exp(x)-1)
        df_bk['creturns'] = df_bk['returns'].cumsum().apply(lambda x: np.exp(x)-1) 
        return df_bk


    def run_strategy(self, start_out, end_out, invest_amt  = 1000,  mmt_list = [30], vlt_list = [7, 180]):

        # set input params
        self.amount = invest_amt
        start_out = lib_data.todatetime(start_out)
        end_out = lib_data.todatetime(end_out)
        self.filter_underlying_data(date_begin = start_out, date_end = end_out, lead_days = max(mmt_list + vlt_list) )
        
        # set up necessary data structure
        self.setup_order_table()
        self.setup_risk(drawdown_pct = -0.05, coverage_pctl = 0.9, risk_window = 30)
        self.setup_alpha(mmt_list, vlt_list) # set up alpha
        self.setup_book_daily(start_date = start_out, end_date = end_out)
            

        df_bk = self.run_book_daily()

        return df_bk
    
    
    
    

if __name__ == "__main__":
 
    if __name__ == "__main__":
        from lib_evaluate import InvestPerformance
        import pandas as pd

        mb = Book('btc')

        ip = InvestPerformance()
        df_bk = mb.run_strategy( '2021-01-01', '2023-12-31', invest_amt  = 1000, mmt_list = [30], vlt_list = [7, 180])
        df_orders = mb.orders.df_orders
        df_orders.to_clipboard()
        print(df_orders)
        
        df_bk[[ 'cstrategy', 'creturns']].plot()
        plt.show()

