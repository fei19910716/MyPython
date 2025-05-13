import easytrader
import pathlib
import os
import sys,json,time
import signal
import akshare as ak
import pyautogui as pg

import logbook
from logbook import Logger, StreamHandler, FileHandler

logbook.set_datetime_format('local')



class Trader(object):
    def __init__(self):
        self.buy_tab      = pg.Point(x=292, y=115)
        self.sale_tab     = pg.Point(x=424, y=115)
        self.input_symbol = pg.Point(x=294, y=165)
        self.amount_input = pg.Point(x=294, y=325)
        self.price_input  = pg.Point(x=302, y=261)

    def moveTo(self,point):
        pg.moveTo(point.x,point.y)

    def clear_price_input(self):
        self.moveTo(self.price_input)
        pg.click()
        
        pg.press('end')
        for i in range(10):
            pg.press('backspace')

    def buy(self,symbol,price,amount):
        self.moveTo(self.buy_tab)
        pg.click()
        time.sleep(0.1)

        self.moveTo(self.input_symbol)
        pg.click()
        time.sleep(0.1)

        pg.hotkey('ctrl','a')
        pg.press('delete')
        pg.write(symbol)
        pg.press('enter')

        self.moveTo(self.price_input)
        pg.click()
        time.sleep(0.1)

        self.clear_price_input()
        pg.write(str(price))
        pg.press('enter')

        self.moveTo(self.amount_input)
        pg.click()
        time.sleep(0.1)

        pg.hotkey('ctrl','a')
        pg.press('delete')
        pg.write(str(amount))
        pg.press('enter')

        pg.press('tab')
        time.sleep(2)
        pg.press('enter')

    def sale(self,symbol,price,amount):
        self.moveTo(self.sale_tab)
        pg.click()
        time.sleep(0.1)

        self.moveTo(self.input_symbol)
        pg.click()
        time.sleep(0.1)

        pg.hotkey('ctrl','a')
        pg.press('delete')
        pg.write(symbol)
        pg.press('enter')

        self.moveTo(self.price_input)
        pg.click()
        time.sleep(0.1)

        self.clear_price_input()
        pg.write(str(price))
        pg.press('enter')

        self.moveTo(self.amount_input)
        pg.click()
        time.sleep(0.1)

        pg.hotkey('ctrl','a')
        pg.press('delete')
        pg.write(str(amount))
        pg.press('enter')

        pg.press('tab')
        time.sleep(2)
        pg.press('enter')


class DefaultLogHandler(object):
    """默认的 Log 类"""

    def __init__(self, name='default', log_type='stdout', filepath='default.log', loglevel='DEBUG'):
        """Log对象
        :param name: log 名字
        :param :logtype: 'stdout' 输出到屏幕, 'file' 输出到指定文件
        :param :filename: log 文件名
        :param :loglevel: 设定log等级 ['CRITICAL', 'ERROR', 'WARNING', 'NOTICE', 'INFO', 'DEBUG', 'TRACE', 'NOTSET']
        :return log handler object
        """
        self.log = Logger(name)
        if log_type == 'stdout':
            StreamHandler(sys.stdout, level=loglevel).push_application()
        if log_type == 'file':
            if os.path.isdir(filepath) and not os.path.exists(filepath):
                os.makedirs(os.path.dirname(filepath))
            file_handler = FileHandler(filepath, level=loglevel)
            self.log.handlers.append(file_handler)

    def __getattr__(self, item, *args, **kwargs):
        return self.log.__getattribute__(item, *args, **kwargs)




class Stock(object):
    def __init__(self):
        self.symbol = ''
        self.name   = ''
        self.left   = 0.0
        self.count  = 0

    def fromDict(self,dict):
        self.__dict__ = dict
class StockEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Stock):
            return {
                "symbol": obj.symbol,
                "name": obj.name,
                "left": obj.left
            }
        return super().default(obj)

# 登录账户
class Test(object):
    def __init__(self, broker=None, need_data=None, logHandler=DefaultLogHandler()):
        self.logger = logHandler
        if (broker is not None) and (need_data is not None):
            self.user = easytrader.use(broker)
            need_data_file = pathlib.Path(need_data)
            if need_data_file.exists():
                self.user.prepare(need_data)
            else:
                self.user = None
                self.logger.info("账号信息文件 %s 不存在, easytrader 将不可用" % (need_data))
                return
        else:
            self.user = None
            self.logger.info('账号 Error')
            return

        
        self.shutdown_signals = [
            signal.SIGINT,  # 键盘信号
            signal.SIGTERM,  # kill 命令
        ]

        for s in self.shutdown_signals:
            # 捕获退出信号后的要调用的,唯一的 shutdown 接口
            signal.signal(s, self._shutdown)

        self.path = pathlib.Path('stock.json')
        self.stocks = {}
        self.trader = Trader()

        self.positions = self.user.get_position()
        for position in self.positions:
            if(position.current_amount > 0):
                self.logger.info('%s' % position)
                stock = Stock()
                stock.symbol = position.stock_code
                stock.name   = position.stock_name
                stock.count  = position.enable_amount
                self.stocks[stock.symbol] = stock
        
        # read the stock left
        self.read()

    def _shutdown(self, sig, frame):
        self.logger.info("强制关闭进程...")
        
        sys.exit(1)

    def read(self):

        with open(self.path, 'r', encoding="utf-8") as file:
            stocks = json.load(file)

            for item in stocks.values():
                symbol = item['symbol']
                if(symbol in self.stocks):
                    self.stocks[symbol].left = item['left']

        
        for item in self.stocks.values():
            self.logger.info('[read] %s' % item.__dict__)

    def write(self):
        for item in self.stocks.values():
            self.logger.info('[write] %s' % item.__dict__)
        
        with open(self.path, 'w', encoding='utf-8') as file:
            json.dump(self.stocks,file,ensure_ascii=False, cls=StockEncoder)

    def update(self, trade = False):

        for stock in self.stocks.values():
            try:
                stock_individual_spot_xq_df = ak.stock_bid_ask_em(symbol=stock.symbol)
                self.balance                = self.user.get_balance()[0].enable_balance
                today                       = stock_individual_spot_xq_df.value[22]
                current_price               = stock_individual_spot_xq_df.value[20]
                max_price                   = stock_individual_spot_xq_df.value[32]
                min_price                   = stock_individual_spot_xq_df.value[33]
                name                        = stock.name
                percent                     = 4 # 涨跌4%
                sale_money                  = 0
                buy_money                   = 0

                stock.left += today
                sum         = stock.left

                self.logger.info('{}, today:{:.2f}%, SUM:{:.2f}%, avalable_count:{}, avalable_money:{:.2f}' .format(name,today,sum,stock.count,self.balance))
            except Exception:
                continue

            # 涨幅大于4%，需要卖出
            if(stock.left >=  percent):
                sale_money     =  10000 * stock.left / percent
                self.logger.info("original sale_money:{:.2f}".format(sale_money))

                # 卖出的钱大于持仓，可能委托失败
                if(sale_money > stock.count * current_price):
                    sale_money = stock.count * current_price #清仓
                    
                    if(sale_money >= 100 * current_price):
                        stock.left = 0
                        self.logger.info("清仓... {}" .format(stock.symbol))
                    else:
                        sale_money = 0

                # 卖出的金额小于持仓，放心卖
                else:
                    if(stock.count * current_price - sale_money < 100 * current_price):
                        sale_money = stock.count * current_price #清仓
                        
                    stock.left = 0
            
            # 跌超-4%，需要买入
            if(stock.left <= -percent):
                buy_money      = -10000 * stock.left / percent
                self.logger.info("original buy_money:{:.2f}".format(buy_money))

                # 如果可用金额足够，并且够100股，则买入
                if(buy_money <= self.balance):
                    if(buy_money >= 100 * current_price):
                        stock.left = 0
                    else:
                        buy_money = 0
                # 如果可用金额不够，则可以把剩下的钱全部买入
                else:
                    if(self.balance >= 100 * current_price):
                        buy_money = self.balance #满仓
                        self.logger.info("满仓... {}".format(stock.symbol))
                        stock.left = (self.balance - buy_money) * percent / 10000
                    else:
                        buy_money = 0

            ### 交易
            if(buy_money == 0 and sale_money > 0):
                if(trade == True):
                    self.sale(stock.symbol,name,sale_money,current_price,min_price)
                else:
                    self.logger.info('Not trade time.')
            elif(buy_money > 0 and sale_money == 0):
                if(trade == True):
                    self.buy(stock.symbol,name,buy_money,current_price,max_price)
                else:
                    self.logger.info('Not trade time.')
    
    def buy(self,symbol,name,buy_money,current_price,max_price):
        try:
            self.user.buy(symbol, price=max_price,amount=buy_money/current_price)
            self.logger.info('买单 pytrader {}, buy:{:.2f}, current_price:{:.2f}, max_price:{:.2f}.'.format(name,buy_money,current_price,max_price))
        except Exception:
            self.trader.buy(symbol, price=max_price,amount=buy_money/current_price)
            self.logger.info('买单 pyautogui {}, buy:{:.2f}, current_price:{:.2f}, max_price:{:.2f}.'.format(name,buy_money,current_price,max_price))

    def sale(self,symbol,name,sale_money,current_price,min_price):
        try:
            self.user.sell(symbol, price=min_price,amount=sale_money/current_price)
            self.logger.info('卖单 pytrader {}, sale:{:.2f}, current_price:{:.2f}, min_price:{:.2f}.'.format(name,sale_money,current_price,min_price))
        except Exception:
            self.trader.sale(symbol, price=min_price,amount=sale_money/current_price)
            self.logger.info('卖单 pyautogui {}, sale:{:.2f}, current_price:{:.2f}, min_price:{:.2f}.'.format(name,sale_money,current_price,min_price))

    def run(self):
        if(self.user == None):
            return
        
        self.logger.info("loop...")

        save = False

        while True:

            local_time = time.localtime()
            self.logger.info('hour: %s, min:%s, sec:%s' %(local_time.tm_hour,local_time.tm_min,local_time.tm_sec))

            if(local_time.tm_hour == 14 and local_time.tm_min >= 57):
                self.update(trade = True)
                save = True
                break
            else:
                # self.update(trade = True)
                pass

            time.sleep(10)
        
        if(save == True):
            self.write()


    def test(self):
        self.buy('920029',price=25.5,amount=200)

if __name__ == "__main__":
    logHandler=DefaultLogHandler(log_type='stdout')
    test = Test(broker = 'eastmoney',need_data = 'eastmoney.json', logHandler=logHandler)
    test.run()