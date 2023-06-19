#!/usr/bin/python3

# 匯入 Shioaji 套件
import shioaji as sj
import pandas as pd
import argparse
import logging
import os
import pickle
import mplfinance as mpf


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
    parser.add_argument('-k', '--key', dest='key', type=str,
                        metavar='KEY_FILE', default="api.key", help='key file name')
    parser.add_argument('-l', '--log', dest='log', type=str,
                        metavar='LOG_FILE', default="shioaji_test.log", help='log file name')

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
    logger = get_logger()  # 取得logger

    # 設定股票代碼
    stock_code = '6217'

    # 設定本地暫存檔名稱
    cache_dir = 'stock_cache'
    cache_file = f'{cache_dir}/{stock_code}_cache.pkl'

    if (os.path.isfile(cache_file)):
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
        kbars = api.kbars(api.Contracts.Stocks[stock_code], start="2020-06-01", end="2020-07-01")

        # 將資料轉換成 DataFrame
        df = pd.DataFrame({**kbars})

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
             addplot=addplot_list, warn_too_much_data=1000)