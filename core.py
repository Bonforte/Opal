import yfinance as yf
from datetime import timedelta
import mplfinance as mpf
import pandas as pd
from numpy import trapz
from helpers import get_adx, compute_ichimoku, get_surfaces, parse_surfaces, get_stock_state

stock_tickers = ['AAPL', 'NVDA', 'FDX', 'AMD', 'NKE', 'QCOM', 'TSLA', 'CRWD', 'PAYC', 'ATVI', 'COST', 'ADBE', 'TDG',  'BWA', 'IPAR', 'RACE', ]  

for stock in stock_tickers:
    ticker = yf.Ticker(stock)
    df_stock = ticker.history(period = '1y')  

    df_stock['Date'] = df_stock.index.values
    df_stock = compute_ichimoku(df_stock)
    df_stock['adx'] = pd.DataFrame(get_adx(df_stock['High'], df_stock['Low'], df_stock['Close'], 14)[2]).rename(columns = {0:'adx'})
    df_stock = df_stock.dropna()

    buy_line = df_stock['kijun_avg']
    sell_line = df_stock['tenkan_avg']

    first_entry = df_stock.head(1)
    last_order = first_entry['tenkan_avg'] < first_entry['kijun_avg']

    border_dates = []
    for index, row in df_stock.iterrows():
        new_order = row['tenkan_avg'] < row['kijun_avg']
        if new_order is not last_order:
            border_dates.append(row['Date'])

        last_sell_line = row['tenkan_avg']
        last_buy_line = row['kijun_avg']
        last_order = last_sell_line < last_buy_line

    border_dates.append(df_stock['Date'].iloc[-1])
    border_dates.pop(0)


    date_intervals = []
    for index in range(len(border_dates)-1):
        date_intervals.append((border_dates[index], border_dates[index+1]))

    surfaces = get_surfaces(df_stock, date_intervals)
        
    SURFACE_THESHOLD = parse_surfaces(surfaces)

    last_interval_df = df_stock[df_stock['Date'] >= border_dates[-2]]

    stock_update_message = get_stock_state(stock, last_interval_df, 4, 0.1, 0.7)

    print(stock_update_message)

print(border_dates[-1])
    