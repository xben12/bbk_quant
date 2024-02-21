from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import lib_data
import matplotlib.pyplot as plt

class Bbk_Utils:
    @staticmethod
    def todatetime(date_in, format = '%Y-%m-%d'):
        if(isinstance(date_in, datetime)):
            return date_in
        return datetime.strptime(date_in, format)
    
    @staticmethod
    def extract_df_by_date_window(df, cur_date, win_size):
        start_index, end_index = Bbk_Utils.get_position_index_start_end(df.index, cur_date, win_size)
        return df[start_index:(end_index+1)]
    
    @staticmethod
    def get_position_index_start_end(date_index, cur_date, win_size):

        cur_date = Bbk_Utils.todatetime(cur_date)
        end_index = date_index.searchsorted(cur_date, side='right')
        start_index = max(0, end_index - win_size + 1)  # Ensure start_index >= 0

        return start_index, end_index

    @staticmethod
    def filter_by_date(data, start, end = '2100-01-01'):
        return  lib_data.df_filter_date(data, start, end)

    @staticmethod
    def load_price_data(symbol):
        df = lib_data.get_token_price_from_csv(symbol)        
        df['returns'] = np.log(df['price']/df['price'].shift(1))
        return df.dropna()
    
    @staticmethod
    def plot_scatter(x, y , z): 
        # Scatter plot
        plt.scatter(x, y, c=z, cmap='viridis', marker='o')

        # Add labels and title
        plt.xlabel('x')
        plt.ylabel('y')
        plt.title('Scatter Plot with Z as Color')

        # Add colorbar
        plt.colorbar(label='Z Value')

        # Show the plot
        plt.show()

    @staticmethod
    def df_draw(df, x_col = 'date', y_list = ['price'], title = "values vs date", color_list = ['blue', 'red', 'green', 'orange']):

        df[x_col] = pd.to_datetime(df[x_col])
        # Plotting
        plt.figure(figsize=(10, 6))

        for i  in range(len(y_list)):
            y_c = y_list[i]
            color = color_list[i]
            plt.plot(df[x_col], df[y_c], label=y_c, color=color)

        plt.title(title)
        plt.xlabel(x_col)
        plt.ylabel('Values')
        plt.legend()
        plt.grid(True)

        # Show the plot
        plt.show()

    @staticmethod
    def mmt_strategy_name(mmt):
        return f'mmt_{mmt}' if mmt > 0 else 'just_hold' 