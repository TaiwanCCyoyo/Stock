#!/usr/bin/python3

import pandas as pd
import argparse
import os
from datetime import datetime, timedelta
import re
import twstock
import sys
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__ + "/..")))  # noqa
from user_logger import user_logger  # noqa
import config  # noqa
from utils.backtest_struct import StockPosition, TradeHistory  # noqa
from utils.stock_category import tse_stock_category_dict  # noqa


args = None
logger = None
stock_groups = set()


def arg_parse():
    """
    解析參數設定並回傳解析結果。

    Returns:
        argparse.Namespace: 解析後的參數設定。
    """

    parser = argparse.ArgumentParser(description='shioaji test script')
    # 設定參數選項
    parser.add_argument('--version', action='version', version='%(prog)s 0.1')
    parser.add_argument('-v', '--verbose', action='count', default=0)
    parser.add_argument('-k', '--key', dest='key', type=str,
                        metavar='*.key', default="api.key", help='key file name')
    parser.add_argument('-u', '--update', dest='update', action="store_true",
                        default=False, help='Update from Shioaji even if there is *.csv')
    parser.add_argument('-l', '--log', dest='log', type=str,
                        metavar='*.log', default=f"{config.DEFAULT_LOG_DIR}/backtest_all.log", help='log file name')
    parser.add_argument('--cache_dir', dest='cache_dir', type=str,
                        metavar='*', default="stock_cache", help='local data cache directory')
    parser.add_argument('--amount', dest='amount', type=int,
                        metavar='<UNSIGNED INT>', default="2000000", help='initial amount')
    parser.add_argument('--investment_per_trade', dest='investment_per_trade', type=int,
                        metavar='<UNSIGNED INT>', default="500000", help='investment per trade')
    parser.add_argument('--group', dest='group', type=str,
                        metavar='<UNSIGNED INT>|ALL', default="ALL", help='investment per trade')

    # 解析參數
    return parser.parse_args()


def decode_group():
    """
    將 group 的數字轉成 list
    """
    global stock_groups

    group_str = args.group
    groups = group_str.split("|")
    stock_groups = set()
    if "ALL" in groups:
        for g in tse_stock_category_dict:
            stock_groups.add(tse_stock_category_dict[g])
    else:
        for g in groups:
            if g in tse_stock_category_dict.keys():
                stock_groups.add(tse_stock_category_dict[g])

    if '-' in stock_groups:
        stock_groups.remove('-')

    logger.info("回測群組:" + ",".join(stock_groups))


def read_stock_data(cache_dir, df_dict):
    """
    取得資料夾中的所有 _day.csv 檔案 (日K)
    """
    day_files = [f for f in os.listdir(cache_dir) if f.endswith("_day.csv")]

    for f in day_files:
        match = re.search(r'(\d+)_cache_day.csv', f)
        if match:
            code = match.group(1)
            if ((code in twstock.codes.keys()) and twstock.codes[code].type == "股票" and
                    (twstock.codes[code].group in stock_groups)):
                # and (code == "3231")):
                logger.info(f'Reading {cache_dir}/{f}')
                df = pd.read_csv(f'{cache_dir}/{f}')
                df.set_index('ts', inplace=True)
                df_dict[code] = df


def sell_rule(df, date):
    """
    賣的規則
    """
    return df.loc[date, 'Low and Low']


def buy_rule(df, date):
    """
    購買規則
    """
    return df.loc[date, 'High and High']


def backtest(date_list, df_dict, amount, investment_per_trade, stock_symbol_name_mapping):
    """
    回測
    """
    logger.info("開始回測")
    logger.info(f"每次購買金額 {investment_per_trade }")
    logger.info(f"初始金額 {amount}")
    hold = {}
    trade = {}
    count_buy = 0
    count_sell = 0
    total_fee = 0

    for date in date_list:
        # 更新最後收盤價
        for code in hold.keys():
            df = df_dict[code]
            if date in df.index:
                hold[code].update_price(int(df.loc[date, 'Close'] * 1000), df.loc[date, 'Close'])

        # 買賣
        logger.info(f"日期:{date}")

        # 賣
        hold_codes = list(hold.keys())
        i = 0
        while i < len(hold_codes):
            code = hold_codes[i]
            df = df_dict[code]

            if date in df.index and sell_rule(df, date):
                count_sell += 1
                fee = int(hold[code].value * 0.004425)
                hold[code].fee += fee
                cost = hold[code].cost + hold[code].fee
                profit = hold[code].value - cost
                total_fee += hold[code].fee
                amount += (hold[code].value - fee)
                logger.info("=======================")
                logger.info(f"賣出 {stock_symbol_name_mapping[code]}({code})")
                logger.info("-----------------------")
                logger.info(f"張數：        {hold[code].num} 張")
                logger.info(f"單價：        {hold[code].price:.2f} 元")
                logger.info(f"總價：        {hold[code].value} 元")
                logger.info(f"平均購買單價： {hold[code].purchase_price:.2f} 元")
                logger.info(f"成本：        {hold[code].cost} 元")
                logger.info(f"賣手續：      {fee} 元")
                logger.info(f"總手續：      {hold[code].fee} 元")
                logger.info(
                    f"獲利：        {profit} 元 " +
                    f"({profit/cost*100:.2f}) %")
                logger.info("-----------------------")
                logger.info(f"總持有現金： {amount} 元")

                # 更新歷史交易
                if code in trade:
                    trade[code].update(hold[code])
                else:
                    tradeHistory = TradeHistory(hold[code])
                    trade[code] = tradeHistory

                hold.pop(code, None)
                logger.info("總持有股票：")
                propert = 0
                for hold_code in hold.keys():
                    logger.info(
                        f"    {stock_symbol_name_mapping[hold_code]}({hold_code}) 有 {hold[hold_code].num} 張 " +
                        f"共 {hold[hold_code].value} 成本 {hold[hold_code].cost} " +
                        f"獲利 {hold[hold_code].value - hold[hold_code].cost - hold[hold_code].fee}")
                    propert += hold[hold_code].value
                logger.info(f"總資產： {amount+propert} 元")
                logger.info("=======================")
                logger.info("")
                logger.info("=======================")
                logger.info("")
            i += 1

        # 找到可購買清單
        buy_list = []
        if amount >= investment_per_trade:
            for code in df_dict.keys():
                df = df_dict[code]

                if date in df.index:
                    # 單價
                    price_unit = int(df.loc[date, 'Close'] * 1000)
                    vol = int(df.loc[date, 'Volume'])

                    item = (code, vol, price_unit)

                    if price_unit <= investment_per_trade and buy_rule(df, date):
                        buy_list.append(item)

            # 購買優先找成交金額大的
            buy_list = sorted(buy_list, key=lambda x: (x[1]*x[2]), reverse=True)

        # 列出購買清單
        if buy_list:
            logger.info("**********")
            logger.info("可買清單")
            for (code, vol, price_unit) in buy_list:
                logger.info(f"    {stock_symbol_name_mapping[code]:5}({code}) 量:{vol:6} 價:{(price_unit/1000):.2f}")

            logger.info("**********")

        # 買
        for (code, vol, price_unit) in buy_list:
            df = df_dict[code]

            # 更新買入次數
            count_buy += 1

            # 買入張數
            num_per_time = int(investment_per_trade/price_unit)

            # 手續費
            fee = int(price_unit * num_per_time * 0.001425)

            # 更新持有張數和平均買入價
            if code in hold.keys():
                hold[code].add_position(price_unit, num_per_time, fee)
            else:
                stockPosition = StockPosition(price_unit, num_per_time, fee)
                hold[code] = stockPosition

            # 花費
            cost = num_per_time * price_unit
            amount -= (cost + fee)
            logger.info("=======================")
            logger.info(f"買入 {stock_symbol_name_mapping[code]}({code})")
            logger.info("-----------------------")
            logger.info(f"張數： {num_per_time} 張")
            logger.info(f"單價： {df.loc[date, 'Close']:.2f} 元")
            logger.info(f"總價： {cost} 元")
            logger.info(f"手續： {fee} 元")
            logger.info("-----------------------")
            logger.info(f"總持有現金： {amount} 元")
            logger.info("總持有股票：")
            propert = 0
            for hold_code in hold.keys():
                logger.info(
                    f"    {stock_symbol_name_mapping[hold_code]}({hold_code}) 有 {hold[hold_code].num} 張 " +
                    f"共 {hold[hold_code].value} 成本 {hold[hold_code].cost} " +
                    f"獲利 {hold[hold_code].value - hold[hold_code].cost- hold[hold_code].fee}")
                propert += hold[hold_code].value
            logger.info(f"總資產： {amount+propert} 元")
            logger.info("=======================")
            logger.info("")

            if amount < investment_per_trade:
                break

    # 結算
    logger.info("=======================")
    logger.info(f"總持有現金： {amount} 元")
    logger.info("總持有股票：")
    propert = 0

    for hold_code in hold.keys():
        total_fee += hold[hold_code].fee
        logger.info(
            f"    {stock_symbol_name_mapping[hold_code]}({hold_code}) 有 {hold[hold_code].num} 張" +
            f"平均成本:{hold[hold_code].purchase_price:.2f} " +
            f"最後收盤價:{hold[hold_code].price:.2f} 市值: {hold[hold_code].value} 成本 {hold[hold_code].cost} " +
            f"獲利 {hold[hold_code].value - hold[hold_code].cost -  hold[hold_code].fee}")
        propert += hold[hold_code].value
    logger.info(f"總資產： {amount+propert} 元")
    logger.info("=======================")

    logger.info("歷史交易")
    for trade_code in trade:
        logger.info(
            f"    {stock_symbol_name_mapping[trade_code]}({trade_code}) 共花 {trade[trade_code].cost} " +
            f"賣 {trade[trade_code].num} 次 總獲利{trade[trade_code].profit} " +
            f"({trade[trade_code].profit/trade[trade_code].cost*100:.2f} %)")
    logger.info("=======================")
    total_returns = (float(amount+propert)/args.amount-1) * 100
    days_difference = (end_date - start_date).days
    annualized_returns = (total_returns / days_difference) * 365

    logger.info(f"初始金額： {args.amount}")
    logger.info(f"時間： {days_difference}")
    logger.info(f"總報酬： {total_returns:.2f} %")
    logger.info(f"年化報酬: {annualized_returns:.2f}%")
    logger.info(f"買次數: {count_buy}")
    logger.info(f"賣次數: {count_sell}")
    logger.info(f"總手續費: {total_fee}")

    logger.info("=======================")
    logger.info("")


if __name__ == '__main__':
    args = arg_parse()  # 命令參數解析
    start_time = datetime.now()
    logger = user_logger.get_logger(args.log)  # 取得logger
    decode_group()

    # 設定本地暫存檔名稱
    cache_dir = args.cache_dir

    if not os.path.exists(cache_dir):
        logger.critical(f"找不到{cache_dir}")
        exit()

    # 取得半導體業股票列表資料
    df_dict = {}
    read_stock_data(cache_dir, df_dict)

    # 取得股號股名對照表
    stock_symbol_name_mapping = {}
    with open(config.STOCK_SYMBOL_NAME_MAPPING, 'r', encoding='utf-8') as f:
        stock_symbol_name_mapping = json.load(f)

    # 取得要計算的日期
    # start_date_str = '2018-12-07'
    start_date_str = '2022-07-01'
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = start_date
    for code in df_dict.keys():
        df = df_dict[code]
        last_date = datetime.strptime(df.index.max(), '%Y-%m-%d')
        print(last_date)
        if end_date < last_date:
            end_date = last_date

    end_date_str = end_date.strftime('%Y-%m-%d')
    delta = timedelta(days=1)
    date_list = []
    current_date = start_date
    while current_date <= end_date:
        current_date_str = current_date.strftime("%Y-%m-%d")
        date_list.append(current_date_str)
        current_date += delta

    # 回測
    backtest(date_list, df_dict, args.amount, args.investment_per_trade, stock_symbol_name_mapping)

    end_time = datetime.now()
    logger.info(f"{start_date_str} 到 {end_date_str} 的回測結束")
    logger.info(f"結束: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

    total_time = (end_time - start_time).total_seconds()
    logger.info(f"程式共花費: {total_time} 秒")
