#!/usr/bin/python3

import argparse
import logging
import twstock
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
import json
import pandas as pd
import pickle
import os

# time
import datetime as datetime


args = None
logger = None


def arg_parse():
    """
    解析參數設定並回傳解析結果。

    Returns:
        argparse.Namespace: 解析後的參數設定。
    """

    parser = argparse.ArgumentParser(description='twstock test script')
    # 設定參數選項
    parser.add_argument('--version', action='version', version='%(prog)s 0.1')
    parser.add_argument('-v', '--verbose', action='count', default=0)
    parser.add_argument('-u', '--update', dest='update',
                        action='store_true', help='twstock update codes')
    parser.add_argument('-l', '--log', dest='log', type=str,
                        metavar='LOG_FILE', default="twstock_test.log", help='log file name')

    # 解析參數
    return parser.parse_args()
# End of arg_parse


def get_logger():
    """
    用來設定 logging。

    這個程式會修改全域變數logger，使他成為logging的logger，
    並會使log輸出到終端機並導到twstock_test.log

    Returns:
        logging.Logger
    """

    # 設定日誌格式
    formatter = logging.Formatter('[%(levelname)s] %(message)s')

    # 設定輸出到 console 的 handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    # 設定輸出到檔案的 handler
    file_handler = logging.FileHandler(args.log, 'w', 'utf-8')
    file_handler.setFormatter(formatter)

    # 設定 logger，並加入 handlers
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    return logger
# End of log_setting


def get_top():

    pass

# End of get_top


def get_sma(df):
    """
    用來算SMA

    """
    # 計算二十日均線
    df['MA20'] = df['close'].rolling(window=20).mean()

    # 計算六十日均線
    df['MA60'] = df['close'].rolling(window=60).mean()

    # 計算一百二十日均線
    df['MA120'] = df['close'].rolling(window=120).mean()
# End of get_slope


def get_ema():

    df['EMA5'] = df['close'].ewm(span=5, adjust=False).mean()

# End of get_slope


if __name__ == '__main__':
    args = arg_parse()  # 命令參數解析
    logger = get_logger()  # 取得logger

    # 更新股票代號
    if (args.update):
        logger.info("更新股票代號...")
        twstock.__update_codes()
        logger.info("完成")
        exit()

    # 取得上市櫃代號的相關資訊
    # stock_dict = twstock.codes
    # new_stock_dict = {}
    # for key, value in stock_dict.items():
    #     if (value[0] == "股票"):
    #         new_stock_dict[key] = value

    # stock_dict = new_stock_dict
    # logger.info("所有台股資訊")
    # logger.info(json.dumps(stock_dict, indent=4, ensure_ascii=False))

    # 設定股票代碼
    stock_code = '2330'

    # 設定本地暫存檔名稱
    cache_file = f'stock_cache/{stock_code}_cache.pkl'

    if (os.path.exists(cache_file)):
        logger.info('讀取本地暫存檔資料')
        # 嘗試從本地讀取暫存資料
        with open(cache_file, 'rb') as f:
            df = pickle.load(f)
        logger.info('從本地暫存檔讀取資料成功')
    else:
        logger.info('讀取TWSE資料')
        # 如果本地暫存檔不存在，則從 TWSE 獲取資料
        stock = twstock.Stock(stock_code)
        data = stock.fetch_from(2022, 1)

        # 將資料轉換成 DataFrame
        df = pd.DataFrame(data)

        # 將資料存儲到本地暫存檔
        with open(cache_file, 'wb') as f:
            pickle.dump(df, f)
        logger.info('從 TWSE 獲取資料並存儲到本地暫存檔')

    # 設定日期為索引欄位
    df.set_index('date', inplace=True)

    #
    get_sma(df)

    #
    addplot_list = []
    addplot_list.append(mpf.make_addplot(df['MA20']))
    addplot_list.append(mpf.make_addplot(df['MA60']))
    addplot_list.append(mpf.make_addplot(df['MA120']))

    # 將 DataFrame 轉換為 mplfinance 需要的格式
    quotes = df[['open', 'high', 'low', 'close', 'capacity']]
    quotes.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

    # 繪製蠟燭圖
    mpf.plot(quotes, type='candle', style='yahoo',
             title=('Stock Chart ' + stock_code), ylabel='Price', volume=True,
             addplot=addplot_list, warn_too_much_data=1000)

# fig = plt.figure(figsize=(24, 8))

# ax = fig.add_subplot(1, 1, 1)
# ax.set_xticks(range(0, len(stock.index), 10))
# ax.set_xticklabels(df_2330.index[::10])
# mpf.plot(ax, stock.open, stock.close, stock.high,
#   stock.low, width=0.6, colorup='r', colordown='g', alpha=0.75)


# 获取台股所有股票资讯
# stock_info = twstock.all

# # 遍历所有股票，获取当前股票的资讯
# for stock in stock_info:
#     sid = stock_info[stock]['code']
#     stock_price = twstock.realtime.get(sid)
#     ma_5 = twstock.indicator.calculate_ma(twstock.Stock(sid).close, 5)[-1]

#     # 判断当前股票是否在 5 日均线上
#     if stock_price and float(stock_price['realtime']['latest_trade_price']) >= ma_5:
#         print(sid, 'is on 5MA')
