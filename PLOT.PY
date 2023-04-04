import yfinance as yf
from datetime import timedelta
import mplfinance as mpf
import pandas as pd
from numpy import trapz
from helpers import get_adx, compute_ichimoku, get_surfaces, parse_surfaces, last_surface_trigger, test_profit

stock_tickers = ['AAPL', 'MSFT','NVDA', 'TSLA', 'V', 'PG', 'MA', 'HD', 'LLY',  'COST', 'CRM',  'ADBE', 'AMD', 'NKE','QCOM'] 

train_periods = ['5y', '4y', '3y', '2y']
test_periods = [ '1y']



ticker = yf.Ticker('qcom')

df_stock = ticker.history(period='1y')


#df_stock.index.values
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
print(border_dates)


date_intervals = []
for index in range(len(border_dates)-1):
    date_intervals.append((border_dates[index], border_dates[index+1]))

surfaces = get_surfaces(df_stock, date_intervals)

SURFACE_THESHOLD = parse_surfaces(surfaces)


test_df_stock = df_stock.head(365)
adx_average = sum(df_stock['adx'][-365:])/ len(df_stock['adx'][-365:])

    


# transaction_date, buy_flag, strength = surface_trigger(df_stock)
# print(transaction_date, buy_flag, strength, sum(df_stock['adx'][-182:])/ len(df_stock['adx'][-365:]))
                
# signals = []
# for index, entry in df_stock.iterrows():
#     if entry['Date']!= transaction_date:
#         signals.append(0)
#     else:
#         signals.append(float(entry['Low']))
# print(len(signals[-250:]))

        

add_plots= [
            mpf.make_addplot(df_stock.tail(365)['kijun_avg']),
            mpf.make_addplot(df_stock.tail(365)['tenkan_avg']),
            #mpf.make_addplot(df_stock.tail(365)['adx'], color='red'),
            #mpf.make_addplot(signals[-250:],type='scatter',markersize=200,marker='^'),
            mpf.make_addplot(df_stock.tail(365)['senkou_a']),
            mpf.make_addplot(df_stock.tail(365)['senkou_b'])
           ]

mpf.plot(df_stock.tail(365), type = 'candle', volume = True, ylabel = "Price", ylabel_lower  = 'Volume', style = 'nightclouds', figratio=(15,10), figscale = 1.5,  addplot = add_plots)
