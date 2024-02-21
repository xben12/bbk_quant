class Alpha(object):
    def __init__(self, data):
        self.data = data
        
    @staticmethod
    def feature_name(window, label= 'mmt' ):
        return f'{label}_{window}'
    
    @staticmethod
    def rolling_agg(window, func):
        if func == 'sum':
            return window.sum()
        elif func == 'mean':
            return window.mean()
        elif func == 'std':
            return window.std()
    
    def create_feature_roll_agg(self, win_list = [7, 180], label = 'mmt', agg_func = "sum"):
        
        df = self.data
        rst_cols = [] 

        for win in win_list:
            col_name = Alpha.feature_name(win, label=label)
            df[col_name] = df['returns'].rolling(win).agg(lambda x: Alpha.rolling_agg(x,agg_func)) 
            rst_cols.append(col_name)
        
        return rst_cols
    
    def create_feature_mmt(self, win_list = [30]):
        rst_cols = self.create_feature_roll_agg(win_list, 'mmt', 'sum')
        self.mmt_cols= rst_cols
        return rst_cols
    
    def create_feature_volatility(self, win_list = [7, 180]):
        rst_cols = self.create_feature_roll_agg(win_list, 'vlt', 'std')
        self.vlt_cols = rst_cols
        return rst_cols

    def get_features_on_date(self, date):
        vl = self.data.loc[date, self.mmt_cols + self.vlt_cols ].values
        return vl[0], vl[1], vl[2]

    def _new_trade_long_short(self, mmt_val, vlt_short):
        if (mmt_val > vlt_short ): 
            long_short  = 1
        elif mmt_val < - vlt_short :
            long_short  = -1
        else:
            long_short = 0
        return long_short
    
    def decide_on_new_trade_long_short(self, date):
        mmt_val, vlt_short, vlt_long = self.get_features_on_date(date)
        return self._new_trade_long_short(mmt_val, vlt_short)
    




