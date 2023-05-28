#!/usr/bin/python3

# basic
import argparse
import logging

# get data
import pandas_datareader as pdr
import pandas_datareader.data as web
import datetime
import os


args = None
logger = None


def arg_parse():
    """
    解析參數設定並回傳解析結果。

    Returns:
        argparse.Namespace: 解析後的參數設定。
    """
    global args

    parser = argparse.ArgumentParser(
        description='pandas_datareader test script')
    # 設定參數選項
    parser.add_argument('--version', action='version', version='%(prog)s 0.1')
    parser.add_argument('-v', '--verbose', action='count', default=0)
    parser.add_argument('-l', '--log', dest='log', type=str,
                        metavar='LOG_FILE', default="pandas_datareader_test.log", help='log file name')

    # 解析參數
    args = parser.parse_args()
# End of arg_parse


def get_logger():
    """
    用來設定 logging。

    這個程式會修改全域變數logger，使他成為logging的logger，
    並會使log輸出到終端機並導到twstock_test.log
    """

    global logger

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

# End of log_setting


if __name__ == '__main__':

    arg_parse()
    get_logger()

    start_date = datetime.datetime(2021, 1, 1)
    end_date = datetime.datetime(2021, 12, 31)

    df = web.DataReader('F', 'morningstar',
                        start='2019-09-10', end='2019-10-09')
    logger.info(df.head())
    # logger.info(df_2330)
