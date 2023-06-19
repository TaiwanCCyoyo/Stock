#!/usr/bin/python3

import shioaji as sj
import pandas as pd
import argparse
import os
import pickle
import mplfinance as mpf
import datetime
import user_logger.user_logger


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
                        default=False, help='Update from Shioaji even if there is *.pkl')
    parser.add_argument('--stock', dest='stock', type=str,
                        metavar='CODE', default="2330", help='The stock code to test')
    parser.add_argument('-l', '--log', dest='log', type=str,
                        metavar='*.log', default="shioaji_test.log", help='log file name')

    # 解析參數
    return parser.parse_args()
# End of arg_parse


def get_sma(df):
    """
    用來算SMA

    """
    # 計算二十日均線
    df['MA20'] = df['Close'].rolling(window=20).mean()

    # 計算六十日均線
    df['MA60'] = df['Close'].rolling(window=60).mean()

    # 計算一百二十日均線
    df['MA120'] = df['Close'].rolling(window=120).mean()
# End of get_slope


if __name__ == '__main__':
    args = arg_parse()  # 命令參數解析
    logger = user_logger.user_logger.get_logger(args.log)  # 取得logger

    # 設定股票代碼
    stock_code = args.stock

    # 設定本地暫存檔名稱
    cache_dir = 'stock_cache'
    cache_file = f'{cache_dir}/{stock_code}_cache.pkl'

    if (os.path.isfile(cache_file) and not args.update):
        logger.info('讀取本地暫存檔資料')
        # 嘗試從本地讀取暫存資料
        with open(cache_file, 'rb') as f:
            try:
                df = pickle.load(f)
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
        accounts= api.login(
            api_key = api_key,
            secret_key = secret_key
        )
        if not (accounts):
            logger.critical("登入失敗")
            exit
        logger.info('登入成功')

        # 取得 K 棒資料
        kbars = api.kbars(api.Contracts.Stocks[stock_code], start="1962-02-09", end=datetime.date.today().strftime("%Y-%m-%d"))

        # 將資料轉換成 DataFrame
        df = pd.DataFrame({**kbars})
        logger.info(df)

        # 將資料存儲到本地暫存檔
        logger.info('將 Shioaji 獲取的資料存儲到本地暫存檔')

        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(df, f)
        except:
            logger.warning(f"{cache_file} 儲存失敗")
            try:
                os.remove(cache_file)
            except OSError:
                pass

    # 設定日期為索引欄位
    df.ts = pd.to_datetime(df.ts)
    df.set_index('ts', inplace=True)

    #
    get_sma(df)

    #
    addplot_list = []
    addplot_list.append(mpf.make_addplot(df['MA20']))
    addplot_list.append(mpf.make_addplot(df['MA60']))
    addplot_list.append(mpf.make_addplot(df['MA120']))

    # 將 DataFrame 轉換為 mplfinance 需要的格式
    quotes = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    quotes.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

    # 繪製蠟燭圖
    mpf.plot(quotes, type='candle', style='yahoo',
             title=('Stock Chart ' + stock_code), ylabel='Price', volume=True,
             addplot=addplot_list, warn_too_much_data=200000)