import pandas as pd


class StockPosition:
    def __init__(self, purchase_price_unit, num, fee):
        self.purchase_price_unit = purchase_price_unit  # 每張平均購買價
        self.price_unit = purchase_price_unit  # 每張價錢
        self.num = num  # 張數
        self.cost = purchase_price_unit * num  # 總成本
        self.value = self.price_unit * self.num  # 市值
        self.purchase_price = purchase_price_unit/1000  # 平均購買價
        self.price = self.purchase_price  # 價錢
        self.fee = fee

    def add_position(self, purchase_price_unit, num, fee):
        self.cost += purchase_price_unit * num
        self.num += num
        self.purchase_price_unit = self.cost/self.num
        self.purchase_price = self.purchase_price_unit/1000
        self.value = self.price_unit * self.num
        self.fee += fee

    def update_price(self, price_unit, price):
        self.price_unit = price_unit
        self.price = price
        self.value = self.price_unit * self.num


class TradeHistory:
    def __init__(self, stockPosition):
        self.cost = stockPosition.cost  # 總成本
        self.profit = stockPosition.value - stockPosition.cost - stockPosition.fee  # 獲利
        self.num = 1  # 買賣次數

    def update(self, stockPosition):
        self.cost += stockPosition.cost
        self.profit += (stockPosition.value - stockPosition.cost - stockPosition.fee)
        self.num += 1


sell_rule_dict = {"破底賣":  # 破底就賣
                  lambda df, date: df.loc[date, '破底'],
                  "ESMA20死亡交叉":  # 死亡交叉賣，不過保留一點誤差值
                  lambda df, date:
                  ((df.loc[date, 'Close'] < df.loc[date, 'SMA20'] and df.loc[date, 'Close'] < df.loc[date, 'EMA20']) and
                   ((float(df.loc[date, 'SMA20'] - df.loc[date, 'Close'])/df.loc[date, 'Close'] > 0.01) or
                    (float(df.loc[date, 'EMA20'] - df.loc[date, 'Close'])/df.loc[date, 'Close'] > 0.01)
                    )),
                  }
# sell_rule_dict = {"破底賣":  # 破底就賣
#                   lambda df, date: df.loc[date, '破底'],
#                   "ESMA20死亡交叉":  # 死亡交叉賣，不過保留一點誤差值
#                   lambda df, date:
#                   (((float(df.loc[date, 'SMA20'] - df.loc[date, 'Close'])/df.loc[date, 'Close'] > 0.01) and
#                     df.loc[date, 'Close'] < df.loc[date, 'SMA20']) or
#                    ((float(df.loc[date, 'EMA20'] - df.loc[date, 'Close'])/df.loc[date, 'Close'] > 0.01) and
#                     df.loc[date, 'EMA20'] < df.loc[date, 'SMA20'])),
#                   }


buy_rule_dict = {"過高買":  # 第一次過高就買
                 lambda df, date: pd.notnull(df.loc[date, 'Previous Index']) and pd.notnull(df.loc[date, '過前高']) and (
                     not df.loc[df.loc[date, 'Previous Index'], '過前高'] and df.loc[date, '過前高']),
                 "過高後均線聚集買":  # 若前高有過前前高，在均線聚集處買
                 lambda df, date: df.loc[df.loc[date, '前高 Index'], '過前高'] and df.loc[date, '均線聚集後突破'],
                 "突破下降壓力均線聚集買":  # 突破下降壓力，在均線聚集處買
                 lambda df, date: (df.loc[date, 'Close'] > df.loc[date, '高點連線']) and df.loc[date, '均線聚集後突破'],
                 "突破下降壓力或過高後均線聚集買":  # 突破下降壓力，在均線聚集處買
                 lambda df, date: (((df.loc[date, 'Close'] > df.loc[date, '高點連線']) or
                                   df.loc[df.loc[date, '前高 Index'], '過前高']) and
                                   df.loc[date, '均線聚集']),

                 "聚集買":  # 在均線聚集處買
                 lambda df, date: (df.loc[date, '均線聚集後突破'] or
                                   (df.loc[date, '短均線聚集後突破'] and
                                    (df.loc[df.loc[date, '前高 Index'], '過前高'] or
                                     not df.loc[df.loc[date, '前低 Index'], '破底']))),
                 #  "聚集買":  # 在均線聚集處買
                 #  lambda df, date: (df.loc[date, '短均線聚集']),
                 }
