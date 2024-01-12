#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
描述: 這個檔案用來找尋是否有錯誤的股票資料
"""
import os
import argparse
import pandas as pd
import multiprocessing
import user_logger.user_logger

args = None
logger = None


def arg_parse():
    """
    解析參數設定並回傳解析結果。

    Returns:
        argparse.Namespace: 解析後的參數設定。
    """

    parser = argparse.ArgumentParser(
        description='find error stock price script')
    # 設定參數選項
    parser.add_argument('-l', '--log', dest='log', type=str, metavar='*.log',
                        default="log/find_error_price.log", help='log file name')
    parser.add_argument('--cache_dir', dest='cache_dir', type=str,
                        metavar='*', default="stock_cache", help='local data cache directory')

    # 解析參數
    return parser.parse_args()
# End of arg_parse


def find_error_price(cache_dir):
    """
    找出 cache_dir 中 Low、Close、High 或 Open 為 0 的 CSV 檔案。

    Args:
        cache_dir: CSV 檔案所在的資料夾。

    Returns:
        符合條件的 CSV 檔案清單。
    """

    # 檢查資料夾是否存在
    if not os.path.exists(cache_dir):
        logger.info(f"沒找到{args.cache_dir}")
        return

    # 列出資料夾中的所有 CSV 檔案
    files = os.listdir(cache_dir)
    files = [os.path.join(cache_dir, f) for f in files if f.endswith(".csv")]

    # 逐一讀取 CSV 檔案
    for file in files:
        df = pd.read_csv(file)

        # 找出 Low、Close、High 或 Open 為 0 但 Volume 不為 0 的行數
        error_rows = 0
        for i in range(len(df)):
            if df.loc[i, "Volume"] != 0:
                if df.loc[i, "Low"] == 0:
                    error_rows = i
                    break
                if df.loc[i, "Close"] == 0:
                    error_rows = i
                    break
                if df.loc[i, "High"] == 0:
                    error_rows = i
                    break
                if df.loc[i, "Open"] == 0:
                    error_rows = i
                    break

        # 如果有符合條件的行數，則列出該檔案
        if error_rows:
            logger.info(f"{file}: {error_rows}")


if __name__ == "__main__":
    args = arg_parse()  # 命令參數解析
    logger = user_logger.user_logger.get_logger(args.log)  # 取得logger

    find_error_price(args.cache_dir)
