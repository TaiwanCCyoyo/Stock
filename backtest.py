#!/usr/bin/python3

import shioaji as sj
import pandas as pd
import argparse
import os
import mplfinance as mpf
import matplotlib.pyplot as plt
import datetime
import user_logger.user_logger
import stock_function.indicators as indicators
import numpy as np

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
    parser.add_argument('--stock', dest='stock', type=str,
                        metavar='CODE', default="2330", help='The stock code to test')
    parser.add_argument('-l', '--log', dest='log', type=str,
                        metavar='*.log', default="shioaji_test.log", help='log file name')
    parser.add_argument('--amount', dest='amount', type=int,
                        metavar='<UNSIGNED INT>', default="3000000", help='initial amount')
    # 解析參數
    return parser.parse_args()
# End of arg_parse


if __name__ == '__main__':
    args = arg_parse()  # 命令參數解析
    logger = user_logger.user_logger.get_logger(args.log)  # 取得logger

    # 設定股票代碼
    stock_code = args.stock

    # 設定本地暫存檔名稱
    cache_dir = 'stock_cache'
    cache_file = f'{cache_dir}/{stock_code}_cache_min.csv'

    if (os.path.isfile(cache_file) and not args.update):
        logger.info('讀取本地暫存檔資料')
        # 嘗試從本地讀取暫存資料
        try:
            df = pd.read_csv(cache_file)
            print(df)
        except:
            logger.critical(f"{cache_file}讀取失敗")
            exit

        logger.info('從本地暫存檔讀取資料成功')
    else:
        # 如果本地暫存檔不存在，則從 Shioaji 獲取資料
        logger.info('讀取Shioaji資料')

        # 建立 Shioaji api 物件
        api = sj.Shioaji()

        # API key 以檔案形式存在 local
        if (os.path.isfile(args.key)):
            logger.info(f"從{args.key}讀取金鑰")
            try:
                with open(args.key, 'r') as f:
                    api_key = f.readline().strip()
                    secret_key = f.readline().strip()
            except:
                logger.critical("Key 取得失敗")
                exit

        else:
            logger.critical(f"遺失{args.key}")
            exit

        logger.info('登入')
        accounts = api.login(
            api_key=api_key,
            secret_key=secret_key
        )
        if not (accounts):
            logger.critical("登入失敗")
            exit
        logger.info('登入成功')

        # 取得 K 棒資料
        kbars = api.kbars(
            contract=api.Contracts.Stocks[stock_code],
            start='2018-12-07',
            end=datetime.date.today().strftime("%Y-%m-%d")
        )
        api.logout()
        # 將資料轉換成 DataFrame
        df = pd.DataFrame({**kbars})
        logger.info("\n" + str(df))

        # 將資料存儲到本地暫存檔
        logger.info('將 Shioaji 獲取的資料存儲到本地暫存檔')

        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        try:
            df.to_csv(cache_file, index=False)
        except:
            logger.warning(f"{cache_file} 儲存失敗")
            try:
                os.remove(cache_file)
            except OSError:
                pass

    df.ts = pd.to_datetime(df.ts)
    df.set_index('ts', inplace=True)

    df = df.resample('1D').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    })

    df = df.dropna(subset=['Open'])
    logger.info("\n" + str(df))

    # 計算均線
    indicators.set_ma(df)

    # 聚集
    indicators.set_concentrated(df)
    logger.info("聚集日期:\n" +
                str(df[df['Concentrated']].index))

    # 聚集 突破
    indicators.set_breakthrough(df)
    logger.info("突破聚集日期:\n" +
                str(df[df['Breakthrough']].index))

    # 張嘴排列
    indicators.set_expansion(df)
    logger.info("張嘴排列的日期:\n" +
                str(df[df['Expansion']].index))

    # 閉合排列
    indicators.set_clogging(df)
    logger.info("閉合排列的日期:\n" +
                str(df[df['Clogging']].index))

    # 區間高點
    indicators.set_range_high(df)
    logger.info("區間高點的日期:\n" +
                str(df[df['Range High']].index))

    high_indices = df.index[df['Range High']]

    # 區間低點
    indicators.set_range_low(df)
    logger.info("區間低點日期:\n" +
                str(df[df['Range Low']].index))

    high_indices = df.index[df['Range Low']]

    # 前高
    indicators.set_high_and_high(df)

    # 前低
    indicators.set_low_and_low(df)

    df_without_nan = df.dropna(subset=['Pre High', 'High and High'])
    my_index = df_without_nan[(
        df_without_nan['Close'] > df_without_nan['Pre High']) & df_without_nan['High and High']].index
    tmpstr = ""
    for i in my_index:
        tmpstr += f"Data: {i}, Close: {df.loc[i, 'Close']}, Pre High: {df.loc[i, 'Pre High']}, Pre High Index: {df.loc[i, 'Pre High Index']}\n"

    logger.info(f"過前高: {tmpstr}\n")
    logger.info("過前高日期:\n" + str(df[df['High and High']].index))

    # 試算
    num = 0
    amount = args.amount
    tot_per_time = int(amount/3)

    logger.info(f"每次購買金額 {tot_per_time}")
    hold = 0
    for i in df.index[1:]:
        if (df.loc[i, 'High and High'] and amount >= tot_per_time and (df.loc[i, 'Close']*1000 <= tot_per_time)):
            num_per_time = int(tot_per_time/df.loc[i, 'Close']/1000)
            hold += num_per_time
            amount -= int(num_per_time * (df.loc[i, 'Close']*1000))
            logger.info(f"=======================")
            logger.info(f"買入")
            logger.info(f"-----------------------")
            logger.info(f"張數： {num_per_time} 張")
            logger.info(f"單價： {df.loc[i, 'Close']} 元")
            logger.info(f"總價： {(num_per_time * (df.loc[i, 'Close']*1000))} 元")
            logger.info(f"-----------------------")
            logger.info(f"總持有： {amount} 元")
            logger.info(f"總持有： {hold} 張")
            logger.info(f"總資產： {amount+(hold * (df.loc[i, 'Close']*1000))} 張")
            logger.info(f"=======================")
            logger.info(f"")
        if (df.loc[i, 'Low and Low'] and hold > 0):
            amount += int(hold * (df.loc[i, 'Close']*1000))
            logger.info(f"=======================")
            logger.info(f"賣出")
            logger.info(f"-----------------------")
            logger.info(f"張數： {hold} 張")
            logger.info(f"單價： {df.loc[i, 'Close']} 元")
            logger.info(f"總價： {(hold * (df.loc[i, 'Close']*1000))} 元")
            logger.info(f"-----------------------")
            logger.info(f"總持有： {amount} 元")
            logger.info(f"=======================")
            logger.info(f"")
            hold = 0

    # 回傳預期報酬

    # 寫入 csv
    df.to_csv('result.csv', index=True)
    exit()
