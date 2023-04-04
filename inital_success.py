import yfinance as yf
from datetime import timedelta
import mplfinance as mpf
import pandas as pd
from numpy import trapz

def compute_ichimoku(df_stock):
    #Tenkan Sen
    tenkan_max = df_stock['High'].rolling(window = 9, min_periods = 0).max()
    tenkan_min = df_stock['Low'].rolling(window = 9, min_periods = 0).min()
    df_stock['tenkan_avg'] = (tenkan_max + tenkan_min) / 2

    #Kijun Sen
    kijun_max = df_stock['High'].rolling(window = 26, min_periods = 0).max()
    kijun_min = df_stock['Low'].rolling(window = 26, min_periods = 0).min()
    df_stock['kijun_avg'] = (kijun_max + kijun_min) / 2

    return df_stock

# ADX Plot
def get_adx(high, low, close, lookback):
    plus_dm = high.diff()
    minus_dm = low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0
    
    tr1 = pd.DataFrame(high - low)
    tr2 = pd.DataFrame(abs(high - close.shift(1)))
    tr3 = pd.DataFrame(abs(low - close.shift(1)))
    frames = [tr1, tr2, tr3]
    tr = pd.concat(frames, axis = 1, join = 'inner').max(axis = 1)
    atr = tr.rolling(lookback).mean()
    
    plus_di = 100 * (plus_dm.ewm(alpha = 1/lookback).mean() / atr)
    minus_di = abs(100 * (minus_dm.ewm(alpha = 1/lookback).mean() / atr))
    dx = (abs(plus_di - minus_di) / abs(plus_di + minus_di)) * 100
    adx = ((dx.shift(1) * (lookback - 1)) + dx) / lookback
    adx_smooth = adx.ewm(alpha = 1/lookback).mean()
    return plus_di, minus_di, adx_smooth

def get_surfaces(df_stock, date_intervals):
    counter=0
    surfaces=[]

    for interval in date_intervals:
        filtered_df = df_stock[(df_stock['Date']>interval[0]) & (df_stock['Date']<interval[1])]
        interval_values = filtered_df[['tenkan_avg', 'kijun_avg']]

        interval_buy_line = interval_values['tenkan_avg']
        interval_sell_line = interval_values['kijun_avg']

        buy_area_interval = trapz(interval_buy_line, dx=1)
        sell_area_interval = trapz(interval_sell_line, dx=1)

        area_between_lines_interval = abs(buy_area_interval - sell_area_interval)
        counter+=1
        surfaces.append(abs(area_between_lines_interval))
    return surfaces

def parse_surfaces(surfaces):
    surface_average = float(sum(surfaces)/len(surfaces))
    low_values = [value for value in surfaces if value<=surface_average/2]
    low_values_average = float(sum(low_values)/len(low_values))
    surface_threshold = 6
    return surface_threshold

def last_surface_trigger(df_stock, border_dates, SURFACE_THESHOLD):
    filtered_df_stock = df_stock[df_stock['Date']>=border_dates[-2]]
    
    for index, entry in filtered_df_stock.iterrows():
        entry_flag = False
        buy_flag=None
        current_date = entry['Date']
        final_df_stock = filtered_df_stock[filtered_df_stock['Date']<=current_date]
        interval_buy_line = final_df_stock['tenkan_avg']
        interval_sell_line = final_df_stock['kijun_avg']

        buy_area_interval = trapz(interval_buy_line, dx=1)
        sell_area_interval = trapz(interval_sell_line, dx=1)

        area_between_lines_interval = buy_area_interval - sell_area_interval
        
        if(abs(area_between_lines_interval) >= SURFACE_THESHOLD):
            entry_flag = True

            if(area_between_lines_interval >= 0):
                buy_flag=True
            else:
                buy_flag=False

        if entry_flag:
            return current_date, buy_flag, entry['adx']
        

    return None, None, None

def test_profit(df_stock, date_intervals, SURFACE_THESHOLD, adx_average):
    stock_transactions = []
    transactions = []
    for interval in date_intervals:
        filtered_df_stock = df_stock[(df_stock['Date']>=interval[0]) & (df_stock['Date']<=interval[1])]
        entry_price = None
        stop_price = None
        entry_flag = False
        buy_flag = None
        slope_sell = None
        slope_buy = None
        
        for index, entry in filtered_df_stock.iterrows():
            
            current_date = entry['Date']
            intermediary_df_stock = filtered_df_stock[filtered_df_stock['Date']<=current_date]
            #print(intermediary_df_stock)
            interval_buy_line = intermediary_df_stock['tenkan_avg']
            interval_sell_line = intermediary_df_stock['kijun_avg']
            if len(interval_sell_line) > 2 and len(interval_buy_line) > 2:
                x1_sell,y1_sell = 1, interval_sell_line[-2]
                x2_sell,y2_sell = 2, interval_sell_line[-1]
                slope_sell = ((y2_sell-y1_sell)/(x2_sell-x1_sell))
                x1_buy,y1_buy = 1, interval_buy_line[-2]
                x2_buy,y2_buy = 2, interval_buy_line[-1]
                slope_buy = ((y2_buy-y1_buy)/(x2_buy-x1_buy))

            buy_area_interval = trapz(interval_buy_line, dx=1)
            sell_area_interval = trapz(interval_sell_line, dx=1)
            area_between_lines_interval = buy_area_interval - sell_area_interval
            

            slope_intent = (slope_sell>=0.2 and slope_buy>=0.2) or  (slope_sell<=-0.2 and slope_buy<=-0.2) if slope_sell and slope_buy else False
            #print(slope_intent)
            
            if (abs(area_between_lines_interval) >= SURFACE_THESHOLD) and slope_intent:
                entry_flag = True

                if(area_between_lines_interval >= 0):
                    buy_flag=True
                elif area_between_lines_interval < 0:
                    buy_flag=False

            if entry_flag:
                if not entry_price:
                    entry_price = entry['High'] 

                if (buy_flag and ((slope_sell<-0.5 and slope_buy<-0.5) or slope_buy<-0.5 or slope_sell<-0.5)) or (not buy_flag and ((slope_sell>0.5 and slope_buy>0.5) or slope_buy>-0.5 or slope_sell>-0.5)):
                    stop_price = entry['High']

                if entry_price and stop_price:
                    transaction_profit = (stop_price/entry_price * 100) - 100
                    transaction_profit = transaction_profit
                    if(buy_flag):
                        transactions.append(f'{current_date} - {float(entry_price)} -> {float(stop_price)} (BUY)')
                    else:
                        transactions.append(f'{current_date} - {float(entry_price)} -> {float(stop_price)} (SELL)')
                    if (buy_flag and transaction_profit >= 0) or (not buy_flag and transaction_profit<0):
                        profit_string = abs(transaction_profit)
                    if (buy_flag and transaction_profit < 0)  or (not buy_flag and transaction_profit>=0):
                        profit_string = -abs(transaction_profit)

                    stock_transactions.append(profit_string)
                    break
    return stock_transactions, transactions
                