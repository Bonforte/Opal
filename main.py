import yfinance as yf
from datetime import timedelta
import mplfinance as mpf
import pandas as pd
from numpy import trapz
from helpers import get_adx, compute_ichimoku, get_surfaces, parse_surfaces, last_surface_trigger, test_profit

#'AAPL', 'CDNS', 'NVDA', 'FDX', 'CRM', 'AMD', 'NKE', 'QCOM', 'TSLA', 'CRWD', 'PAYC',  'TTD', 'ATVI', 'CTAS', 'COST', 'ADBE', 'TDG', 'HEI', 'BWA', 'IPAR', 'RACE', 'LVMHF', 
stock_tickers = ['AAPL', 'NVDA', 'FDX', 'AMD', 'NKE', 'QCOM', 'TSLA', 'CRWD', 'PAYC', 'ATVI', 'COST', 'ADBE', 'TDG',  'BWA', 'IPAR', 'RACE', ] 
stock_tickers = list(dict.fromkeys(stock_tickers))
special_ones = ['MC']
train_periods = ['4y', '3y', '2y','1y']
test_periods = ['5y']
stocks_performance = dict()
for stock in stock_tickers:
    stocks_performance[stock] = []

yearly_returns = []
for period in train_periods:
    sum_avg = 0
    stop_loss_sum = 0
    counter_stop_loss = 0
    stop_loss_list = []
    take_profit_list = []
    for stock_ticker in stock_tickers:
        take_profit_ticker = None
        ticker = yf.Ticker(stock_ticker)
        
        df_stock = ticker.history(period=period)


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


        date_intervals = []
        for index in range(len(border_dates)-1):
            date_intervals.append((border_dates[index], border_dates[index+1]))

        surfaces = get_surfaces(df_stock, date_intervals)
        
        SURFACE_THESHOLD = parse_surfaces(surfaces)

        
        test_df_stock = df_stock.head(365)
        adx_average = sum(df_stock['adx'][-365:])/ len(df_stock['adx'][-365:])
        stock_profits, transactions, maximum_possible_loss, take_profit_percentage_list, transactions_profit_list = test_profit(test_df_stock, date_intervals, 4, 0.1, 0.7)

        if transactions_profit_list:
            average_profit = sum(transactions_profit_list)/ len(transactions_profit_list)
            final_average_profit = (average_profit + max(transactions_profit_list))/2

        if take_profit_percentage_list:
            take_profit_ticker = final_average_profit + sum(take_profit_percentage_list)/len(take_profit_percentage_list)

        if take_profit_ticker:
            take_profit_list.append(take_profit_ticker)

        initial_sum = 100
        for profit in stock_profits:
            if profit <= -100:
                initial_sum += initial_sum*(-5/100)
            else:
                initial_sum += initial_sum*(profit/100)
            
        print(f'{stock_ticker} - yearly_return: {initial_sum - 100} % - max_loss = {maximum_possible_loss} %')
        stop_loss_list.append(maximum_possible_loss)
        stocks_performance[stock_ticker].append('- ') if initial_sum-100 <= 5 else stocks_performance[stock_ticker].append('+ ')
        sum_avg += initial_sum-100
    
    stop_loss_average = sum(stop_loss_list)/len(stop_loss_list)
    final_stop_loss_average = (stop_loss_average + max(stop_loss_list))/2
    print(F'TAKE PROFIT:{sum(take_profit_list)/len(take_profit_list) if take_profit_list else None}')
    print(F'STOP LOSS:{final_stop_loss_average}')
    print(f'TOTAL YEARLY RETURN:{sum_avg/len(stock_tickers)}')
    yearly_returns.append(sum_avg/len(stock_tickers))

print(yearly_returns)
yearly_returns_average = sum(yearly_returns)/len(yearly_returns)
print(yearly_returns_average)
for key, value in stocks_performance.items():
    negatives = value.count('- ')
    positives = value.count('+ ')
    stocks_performance[key] = (positives/len(train_periods)) * 100
print(stocks_performance)


# transaction_date, buy_flag, strength = surface_trigger(df_stock)
# print(transaction_date, buy_flag, strength, sum(df_stock['adx'][-182:])/ len(df_stock['adx'][-365:]))
                
# signals = []
# for index, entry in df_stock.iterrows():
#     if entry['Date']!= transaction_date:
#         signals.append(0)
#     else:
#         signals.append(float(entry['Low']))
# print(len(signals[-250:]))

        

# add_plots= [
#             mpf.make_addplot(df_stock.tail(365)['kijun_avg']),
#             mpf.make_addplot(df_stock.tail(365)['tenkan_avg']),
#             mpf.make_addplot(df_stock.tail(365)['adx'], color='red'),
#             #mpf.make_addplot(signals[-250:],type='scatter',markersize=200,marker='^'),
#             # mpf.make_addplot(df_stock['senkou_a'][-500:]),
#             # mpf.make_addplot(df_stock['senkou_b'][-500:])
#            ]

# mpf.plot(df_stock.tail(365), type = 'candle', volume = True, ylabel = "Price", ylabel_lower  = 'Volume', style = 'nightclouds', figratio=(15,10), figscale = 1.5,  addplot = add_plots)
