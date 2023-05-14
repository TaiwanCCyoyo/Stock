#!/usr/bin/python3

import argparse
import logging

# basic
import numpy as np
import pandas as pd

# get data
import pandas_datareader as pdr

# visual
import matplotlib.pyplot as plt
import matplotlib as mpf
import seaborn as sns

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


if __name__ == '__main__':
    start = datetime.datetime(2023, 4, 1)
    end = datetime.datetime(2023, 5, 14)

    df_2330 = pdr.DataReader('2330.TW', 'yahoo', start=start)
