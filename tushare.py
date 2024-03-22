import os
import tushare as ts

def GetStockData(ts_code, start_date, end_date, unit):
    pro = ts.pro_api('1805031f8a621ab787a4cbb44289a873ba2b4beff7ff6ea47ab4c624')

    df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)

    StockSimulation(reversed(df['pct_chg']),unit)

def GetLocalStockData(path, unit):
    price_percents = []
    with open(path) as f:
        price_percents = [float(line) for line in f.readlines()]
    StockSimulation(price_percents, unit)

def StockSimulation(price_percents, unit):
    total_money = 0
    total_earns = 0
    previous_money = 0
    total_days = 0
    max_total_money = 0
    min_total_earns = 0

    for price_percent in price_percents:
        total_days += 1
        previous_money = total_money
        if(total_money - price_percent * unit) > 0:
            if(total_earns   < -25 * unit and price_percent < 0):
                total_money -= price_percent * 2 * unit
            elif(total_earns < -50 * unit and price_percent < 0):
                total_money -= price_percent * 3 * unit
            else:
                total_money -= price_percent * unit
        else:
            total_money = unit
        max_total_money = max(max_total_money, total_money)
        total_earns += previous_money * price_percent / 100
        min_total_earns = min(min_total_earns, total_earns)
        print("{:.2f}%, total_money: {:.0f}, total_earns: {:.0f}, total_days: {:.0f}, max_total_money: {:.0f}, min_total_earns: {:.0f}".format(
            price_percent, total_money, total_earns, total_days,max_total_money,min_total_earns))



if __name__ == '__main__':
    GetLocalStockData('zhonggai_internet.txt', unit= 10000)
    # GetStockData(ts_code='000630.SZ',start_date='20231031', end_date='20240222', unit= 50000)
