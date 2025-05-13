import easytrader
import pathlib
import os
import sys,json,time
import signal
import akshare as ak


class Stock(object):
    def __init__(self):
        self.symbol = ''
        self.name   = ''
        self.left   = 0.0
        self.unit   = 1
        self.enable = True
        self.manual_buy = 0

    def fromDict(self,dict):
        self.__dict__ = dict

    def __repr__(self):
        return '({}, left:{:.2f}%)'.format(self.name, self.left)

    def __lt__(self, other):
        return self.left < other.left

class StockEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Stock):
            return {
                "symbol": obj.symbol,
                "name": obj.name,
                "left": obj.left,
                "unit": obj.unit,
                "enable": obj.enable,
                "manual_buy": obj.manual_buy
            }
        return super().default(obj)


# 登录账户
class Test(object):
    def __init__(self, broker=None, need_data=None):

        if (broker is not None) and (need_data is not None):
            self.user = easytrader.use(broker)
            need_data_file = pathlib.Path(need_data)
            if need_data_file.exists():
                self.user.prepare(need_data)
            else:
                self.user = None
                print("账号信息文件 %s 不存在, easytrader 将不可用" % (need_data))
                return
        else:
            self.user = None
            print('账号 Error')
            return


        self.shutdown_signals = [
            signal.SIGINT,  # 键盘信号
            signal.SIGTERM,  # kill 命令
        ]

        for s in self.shutdown_signals:
            # 捕获退出信号后的要调用的,唯一的 shutdown 接口
            signal.signal(s, self._shutdown)

        self.postions_file = pathlib.Path('positions.json')
        self.positions = []

        self.read_positions()

    def _shutdown(self, sig, frame):
        print("强制关闭进程...")

        sys.exit(1)

    def read_positions(self):

        print("Read positions.")

        self.balance = self.user.get_balance()[0]
        for position in self.user.get_position():
            if(position.current_amount > 0):
                print('{}'.format(position))

        with open(self.postions_file, 'r', encoding="utf-8") as file:
            stocks = json.load(file)

            for item in stocks:
                stock = Stock()
                stock.fromDict(item)

                self.positions.append(stock)

        print("------------------------------")

    def write_positons(self):
        print("Write positions.\n")

        with open(self.postions_file, 'w', encoding='utf-8') as file:
            json.dump(self.positions,file,ensure_ascii=False, cls=StockEncoder)

    def update_positions(self,save):

        for stock in self.positions:

            stock_individual_spot_xq_df = ak.stock_bid_ask_em(symbol=stock.symbol)
            today                       = stock_individual_spot_xq_df.value[22]
            name                        = stock.name
            unit                        = stock.unit
            enable                      = stock.enable
            manual_buy                  = stock.manual_buy
            percent                     = 4 # 涨跌4%
            sales                       = 0
            buys                        = 0

            stock.left       += today
            stock.left       += (manual_buy / (10000 * stock.unit)) * percent
            stock.manual_buy  = 0
            sum               = stock.left

            if(stock.left >= percent and enable == True):
                while(stock.left >= percent):
                    stock.left -= percent
                    sales += 1
                # sales = stock.left * 10000 / percent
                # stock.left = 0

            if(stock.left <= -percent and enable == True):
                while(stock.left <= -percent):
                    stock.left += percent
                    buys += 1
                # buys = -stock.left * 10000 / percent
                # stock.left = 0

            if(sales > 0):
                print("{}, {}%, SUM:\033[1;33m{:.2f}%\033[0m, S:\033[1;31m{:.2f}\033[0m, left:{:.2f}%\n" .format('WuYangZiKong',today,sum,sales*unit,stock.left))
                self.sale()
            elif(buys > 0):
                print("{}, {}%, SUM:\033[1;33m{:.2f}%\033[0m, B:\033[1;32m{:.2f}\033[0m, left:{:.2f}%\n" .format('WuYangZiKong',today,sum,buys*unit, stock.left))
                self.buy()
            else:
                # print("{}, {}%, SUM:\033[1;33m{:.2f}%\033[0m, left:{:.2f}%\n"                            .format('WuYangZiKong',today,sum,stock.left))
                pass

        if(save == True):
            self.write_positons()


    def update_candidates(self,save):
        self.candidates_file = pathlib.Path('candidates.json')
        self.candidates = []

        with open(self.candidates_file, 'r', encoding="utf-8") as file:
            stocks = json.load(file)

            for item in stocks:
                stock = Stock()
                stock.fromDict(item)

                stock_individual_spot_xq_df = ak.stock_bid_ask_em(symbol=stock.symbol)
                today                       = stock_individual_spot_xq_df.value[22]
                stock.left                  += today

                self.candidates.append(stock)

        self.candidates.sort()
        print(self.candidates)

        if(save == True):
            with open(self.candidates_file, 'w', encoding='utf-8') as file:
                json.dump(self.candidates,file,ensure_ascii=False, cls=StockEncoder)

    def buy(self):
        pass

    def sale(self):
        pass

    def run(self, save):
        if(self.user == None):
            return

        self.update_positions(save)
        self.update_candidates(save)


if __name__ == "__main__":

    test = Test(broker = 'eastmoney',need_data = 'eastmoney.json')
    save = (len(sys.argv) > 1 and sys.argv[1] != '0')
    test.run(save)