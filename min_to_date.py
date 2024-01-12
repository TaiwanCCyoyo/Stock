#!/usr/bin/python3

import pandas as pd
import argparse
import os
import datetime
import user_logger.user_logger
import lib.indicators as indicators
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
    parser.add_argument('-l', '--log', dest='log', type=str,
                        metavar='*.log', default="min_to_date.log", help='log file name')
    # 解析參數
    return parser.parse_args()
# End of arg_parse


if __name__ == '__main__':
    args = arg_parse()  # 命令參數解析
    start_time = datetime.datetime.now()
    logger = user_logger.user_logger.get_logger(args.log)  # 取得logger

    # 設定本地暫存檔名稱
    min_dir = 'stock_cache'
    date_dir = 'stock_cache_date'

    # 取得檔案列表
    file_list = os.listdir(min_dir)
    df_dict = {}
    for f in file_list:
        match = re.match(r'(\d+)_cache_min\.csv', f)
        if match:
            code = match.group(1)
            if (int(code) == 6291):
                logger.info(f"讀取 {f} 的資料")
                df = pd.read_csv(f'{min_dir}/{f}')
                logger.info(f"計算 {code} 的資料")
                df.ts = pd.to_datetime(df.ts)
                df.set_index('ts', inplace=True)

                # df = df.resample('1D').agg({
                #     'Open': 'first',
                #     'High': 'max',
                #     'Low': 'min',
                #     'Close': 'last',
                #     'Volume': 'sum'
                # })

                df = df.dropna(subset=['Open'])

                cache_file_date = f"{date_dir}/{code}_cache_date.csv"
                logger.info(f"儲存資料到 {cache_file_date}")
                df.to_csv(cache_file_date, index=True)

                date_str = '2020-05-12'
                my_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                if my_date in df.index:
                    logger.info("hahaha")
                else:
                    logger.info("NONONO")

    end_time = datetime.datetime.now()
    logger.info(f"結束: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

    total_time = (end_time - start_time).total_seconds()
    logger.info(f"程式共花費: {total_time} 秒")
