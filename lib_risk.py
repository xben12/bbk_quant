import numpy as np
import pandas as pd
from lib_utils import Bbk_Utils

class Risk(object):
    def __init__(self, drawdown_pct = -0.05, coverage_pctl = 0.9, risk_window = 30, df_returns = None):
        self.drawdown_pct =drawdown_pct
        self.coverage_pctl =coverage_pctl 
        self.df_returns = df_returns
        self.risk_window = risk_window
    
    def get_window_returns(self, cur_date):
        df = self.df_returns[['returns']]
        dfw = Bbk_Utils.extract_df_by_date_window(df, cur_date, win_size = self.risk_window)
        return dfw.values
        
    def position_scale(self, cur_date = None, long_short = 1, npa_returns = None):
        
        if npa_returns is None:
            npa_returns = self.get_window_returns(cur_date)
        
        pctl = 1-self.coverage_pctl if long_short ==1 else self.coverage_pctl
        
        risk_drawdown_pct = -1 * abs(np.percentile(npa_returns,pctl*100))
        # max below will disable levarage
        risk_drawdown_pct = min(self.drawdown_pct, risk_drawdown_pct)
        return self.drawdown_pct/risk_drawdown_pct 
    
    def drawdown_loss_limit_from_token(self, pos_token_notional, position_scale):
        return pos_token_notional / position_scale * self.drawdown_pct
    
    def drawdown_loss_limit_from_total_ptf(self, pft_notional):
        return pft_notional * self.drawdown_pct