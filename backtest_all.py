#!/usr/bin/python3

import pandas as pd
import argparse
import os
import datetime
import user_logger.user_logger
import stock_function.indicators as indicators
import twstock
import re

args = None
logger = None


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
                        metavar='*.log', default="backtest_all.log", help='log file name')
    parser.add_argument('--amount', dest='amount', type=int,
                        metavar='<UNSIGNED INT>', default="10000000", help='initial amount')
    # 解析參數
    return parser.parse_args()
# End of arg_parse


if __name__ == '__main__':
    args = arg_parse()  # 命令參數解析
    start_time = datetime.datetime.now()
    logger = user_logger.user_logger.get_logger(args.log)  # 取得logger

    # 設定本地暫存檔名稱
    file_dir = 'stock_cache'

    # 取得半導體業股票列表資料
    file_list = os.listdir(file_dir)
    stock_file_list = []
    df_dict = {}
    for f in file_list:
        match = re.match(r'(\d+)_cache_min\.csv', f)
        if match:
            code = match.group(1)
            if (code in twstock.codes.keys()) and twstock.codes[code].type == "股票" and twstock.codes[code].group == "半導體業":
                stock_file_list.append(f)
                logger.info(f'Reading {file_dir}/{f}')
                df = pd.read_csv(f'{file_dir}/{f}')
                df_dict[code] = df

    # 轉日線並計算K線資料
    for code in df_dict.keys():
        df = df_dict[code]
        logger.info(f"計算 {code} 的資料")
        df.ts = pd.to_datetime(df.ts)
        df.set_index('ts', inplace=True)

        df = df.resample('1D').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        })

        df = df_dict[code] = df.dropna(subset=['Open'])

        # 計算均線
        indicators.set_ma(df)

        # 聚集
        indicators.set_concentrated(df)

        # 聚集 突破
        indicators.set_breakthrough(df)

        # 張嘴排列
        indicators.set_expansion(df)

        # 閉合排列
        indicators.set_clogging(df)

        # 區間高點
        indicators.set_range_high(df)

        # 區間低點
        indicators.set_range_low(df)

        # 過前高
        indicators.set_high_and_high(df)

        # 破前低
        indicators.set_low_and_low(df)

    # 取得所有有開盤的天數
    start_date_str = '2018-12-07'
    start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.datetime.today()
    delta = datetime.timedelta(days=1)
    date_list = []
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date)
        current_date += delta

    # 試算
    amount = args.amount
    tot_per_time = int(amount/5)

    logger.info(f"每次購買金額 {tot_per_time}")
    hold = {}
    last_close = {}

    for date in date_list:
        # 更新 last_close
        for code in df_dict.keys():
            df = df_dict[code]
            if date in df.index:
                last_close[code] = df.loc[date, 'Close']

        # 買賣
        for code in df_dict.keys():
            df = df_dict[code]
            if date in df.index:
                logger.info(f"日期:{date}")
                # 買
                if (df.loc[date, 'High and High'] and amount >= tot_per_time and (df.loc[date, 'Close']*1000 <= tot_per_time)):
                    logger.info(f"{tot_per_time}/df.loc[{date}, 'Close']/1000")
                    logger.info(f"{df.loc[date, 'Close']}")
                    logger.info(f"{code}")
                    num_per_time = int(tot_per_time/df.loc[date, 'Close']/1000)
                    if code in hold.keys():
                        hold[code] += num_per_time
                    else:
                        hold[code] = num_per_time
                    cost = int(num_per_time * (df.loc[date, 'Close']*1000))
                    amount -= cost
                    logger.info(f"=======================")
                    logger.info(f"買入 {code}")
                    logger.info(f"-----------------------")
                    logger.info(f"張數： {num_per_time} 張")
                    logger.info(f"單價： {df.loc[date, 'Close']} 元")
                    logger.info(f"總價： {cost} 元")
                    logger.info(f"-----------------------")
                    logger.info(f"總持有現金： {amount} 元")
                    logger.info(f"總持有股票：")
                    propert = 0
                    for hold_code in hold.keys():
                        logger.info(f"    {hold_code} 有 {hold[hold_code]} 張")
                        propert += (hold[hold_code] *
                                    (last_close[hold_code]*1000))
                    logger.info(f"總資產： {amount+propert} 元")
                    logger.info(f"=======================")
                    logger.info(f"")

                # 賣
                if (df.loc[date, 'Low and Low'] and (code in hold.keys())):
                    earned = int(hold[code] * (df.loc[date, 'Close']*1000))
                    amount += earned
                    logger.info(f"=======================")
                    logger.info(f"賣出 {code}")
                    logger.info(f"-----------------------")
                    logger.info(f"張數： {hold[code]} 張")
                    logger.info(f"單價： {df.loc[date, 'Close']} 元")
                    logger.info(f"總價： {earned} 元")
                    logger.info(f"-----------------------")
                    logger.info(f"總持有現金： {amount} 元")
                    hold.pop(code, None)
                    logger.info(f"總持有股票：")
                    propert = 0
                    for hold_code in hold.keys():
                        logger.info(f"    {hold_code} 有 {hold[hold_code]} 張")
                        propert += (hold[hold_code] *
                                    (last_close[hold_code]*1000))
                    logger.info(f"總資產： {amount+propert} 元")
                    logger.info(f"=======================")
                    logger.info(f"")
                    logger.info(f"=======================")
                    logger.info(f"")

    end_time = datetime.datetime.now()
    logger.info(f"結束: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

    total_time = (end_time - start_time).total_seconds()
    logger.info(f"程式共花費: {total_time} 秒")
