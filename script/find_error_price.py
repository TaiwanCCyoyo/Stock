#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
描述: 這個檔案用來找尋是否有錯誤的股票資料

Copyright (c) 2023-2024 李沿槱

Shioaji 台灣股市資料下載與 K 線分析專案

作者: 李沿槱
電子郵件: your.email@example.com

許可證: GNU General Public License v3.0

本程式碼是根據 GNU General Public License v3.0 授權的開源軟體。
你可以在以下的條件下自由使用、修改、合併、出版、分發、再許可和/或販售本軟體的副本：

1. 你必須在所有的副本或實質性交付品中保留上述的版權聲明、本條款列表和以下的免責聲明。

2. 如果本軟體被修改而不再是原始的 GNU General Public License v3.0 版本，
   你必須清楚標明這一點，不得宣稱或暗示它仍然是原始的 GNU General Public License v3.0。

本軟體是基於「現狀」提供的，沒有任何形式的明示或暗示保證，包括但不限於對特定用途的適用性的暗示保證。
在任何情況下，作者或版權持有人均不對任何索賠、損害或其他責任負責，無論是在合同、侵權或其他方面引起的（包括但不限於疏忽或其他方式）。

你可以在軟體的使用中，不論是否修改，都必須保留以上版權聲明、本條款列表和以下的免責聲明。

免責聲明：

本軟體受版權法保護。未經許可，不得在未經授權的情況下使用、修改、或分發本軟體或其任何衍生作品。

"""
import os
import argparse
import pandas as pd
from concurrent.futures import ProcessPoolExecutor

DEFAULT_CACHE_DIR = "stock_cache"
args = None


def parse_arguments():
    """
    解析參數並回傳解析結果。

    Returns:
        argparse.Namespace: 解析後的參數。
    """
    parser = argparse.ArgumentParser(
        description='找尋錯誤股價的腳本')
    parser.add_argument('--cache_dir', dest='cache_dir', type=str,
                        metavar='*', default=DEFAULT_CACHE_DIR, help='本地資料緩存目錄')
    parser.add_argument('--suffix', dest='suffix', type=str,
                        metavar='*', default="", help='<>.csv <>這段後贅字')
    return parser.parse_args()


def check_stock_data(file_path):
    """
    檢查 CSV 檔案中是否存在股價資料錯誤，並列印出符合條件的行。

    Args:
        file_path (str): CSV 檔案的路徑。
    """
    df = pd.read_csv(file_path)
    error_row = None

    for i in range(len(df)):
        if df.loc[i, "Volume"] != 0:
            if df.loc[i, "Low"] == 0 or df.loc[i, "Close"] == 0 or df.loc[i, "High"] == 0 or df.loc[i, "Open"] == 0:
                error_row = i
                break

    if error_row is not None:
        print(f"{file_path}: {error_row}")


def find_all_error_stock_data(cache_dir):
    """
    找出 cache_dir 中 Low、Close、High 或 Open 為 0 的 CSV 檔案。

    Args:
        cache_dir (str): CSV 檔案所在的資料夾。
    """
    # 檢查資料夾是否存在
    if not os.path.exists(cache_dir):
        print(f"找不到資料夾: {cache_dir}")
        return

    # 列出資料夾中的所有 CSV 檔案
    file_paths = [os.path.join(cache_dir, filename) for filename in os.listdir(
        cache_dir) if filename.endswith(f"{args.suffix}.csv")]

    with ProcessPoolExecutor() as executor:
        # 將任務提交到進程池中執行
        executor.map(check_stock_data, file_paths)


if __name__ == "__main__":
    args = parse_arguments()  # 命令參數解析
    find_all_error_stock_data(args.cache_dir)
