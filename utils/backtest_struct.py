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


sell_rule_dict = {"破底賣": lambda df, date: df.loc[date, 'Low and Low']}
buy_rule_dict = {"過高買": lambda df, date: df.loc[date, 'High and High']}
