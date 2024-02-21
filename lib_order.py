import pandas as pd
import numpy as np
    
class Orders(object):
    def __init__(self):
        self.setup_order_table()    
    
    def setup_order_table(self):
        order_cols = ['order_id', 'long_short', 'size','b_closed',
                      'entry_comments', 'pos_scale',
                      'entry_date', 'highest_ptf_date', 'last_date',
                      'entry_price', 'highest_ptf_price', 'last_price', 
                      'entry_ptf_v', 'highest_ptf_v', 'last_ptf_v',
                      'max_pnl', 'order_drawdown',   'unrealised_pnl', 'stop_loss_limit'
                        ]
        self.df_orders = pd.DataFrame(columns=order_cols)
        self.total_orders = 0
        return self.df_orders
    
    def create_order(self, long_short, pos_scale, date, entry_price, pos_token, stop_loss_limit, entry_comments = ""):
        
        df = self.df_orders
        
        
        init_ptf_v= long_short*pos_token*entry_price
        
        order_id = self.total_orders
        new_row_data = {
            'order_id': order_id, 'long_short': long_short, 'size': pos_token, 'b_closed': False,
            'entry_comments':entry_comments, 'pos_scale':pos_scale,
            'entry_date': date, 'highest_ptf_date': date, 'last_date': None,
            'entry_price': entry_price, 'highest_ptf_price': entry_price, 'last_price': entry_price,
            'entry_ptf_v' : init_ptf_v, 'highest_ptf_v': init_ptf_v, 'last_ptf_v':init_ptf_v,
            'order_drawdown' : 0.0, 'unrealised_pnl': 0.0, 'max_pnl':0.0,
            'stop_loss_limit': stop_loss_limit
        }
        df.loc[order_id] = new_row_data
        
        self.total_orders = self.total_orders+1
        return order_id


    def close_order(self, order_id, price):
        # this function will work out delta amount for token and cash change. 
        order  = self.get_set_order(order_id)
        token_size = order['size']
        long_short = order['long_short']
        order_total_pnl = order['unrealised_pnl']
        
        if(long_short == 1) : # long position
            cash_delta = token_size*price 
            token_delta  =  - token_size
        elif(long_short == -1): # short market
            cash_delta = order_total_pnl
            token_delta  = token_size

        return cash_delta, token_delta

    @staticmethod
    def is_order_valid(order_id):
        return np.isnan(order_id) == False

    @staticmethod
    def id_nan():
        return np.nan

    def update_order_status(self, order_id, date, price_T):
        
        if not Orders.is_order_valid(order_id):
            # b_order_closed, order_daily_pnl, order_long_short, order_drawdown 
            return False, 0
        
        # get info
        order = self.get_set_order(order_id)
        
        long_short,  pos_token, stop_loss_limit = order['long_short'], order['size'], order['stop_loss_limit']
        highest_ptf_v, entry_ptf_v,  ptf_v_Tm1 = order['highest_ptf_v'], order['entry_ptf_v'],  order['last_ptf_v']

        ptf_v_T =long_short* pos_token* price_T        
        daily_pnl = ptf_v_T - ptf_v_Tm1
        unrealised_pnl = ptf_v_T -  entry_ptf_v
        
        if(ptf_v_T > highest_ptf_v):
            highest_ptf_v = ptf_v_T
            
            order['highest_ptf_date'] = date
            order['highest_ptf_price'] = price_T
            order['highest_ptf_v'] = highest_ptf_v
            order['max_pnl'] = highest_ptf_v - entry_ptf_v

        order['last_date'] = date
        order['last_price'] = price_T
        order['last_ptf_v'] = ptf_v_T
        order['order_drawdown'] = ptf_v_T - highest_ptf_v
        order['unrealised_pnl'] =  unrealised_pnl
        
        order['b_closed'] =  order['order_drawdown'] < stop_loss_limit
        
        # write updated order info back.
        self.get_set_order(order_id, order_row = order )
        
        order_id = order_id if order['b_closed'] == False else Orders.id_nan()

        return order['b_closed'], unrealised_pnl,  daily_pnl

    def get_set_order(self, order_id, order_row = None):
        
        if not Orders.is_order_valid(order_id):
            return None
        
        if order_row is None:
            order_row = self.df_orders.loc[order_id].to_dict()
        else:
            self.df_orders.loc[order_id] = order_row
        return order_row

    def get_order_detail(self, order_id, label = None):
        
        if not Orders.is_order_valid(order_id):
            return None
        
        if label is None:
            return self.df_orders.at[order_id]
        
        if not isinstance(label, list):
            return self.df_orders[label].at[order_id]
        
        rst_list = []
        for item in label:
            rst_list.append(self.df_orders[item].at[order_id])
        return rst_list