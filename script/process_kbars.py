#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
描述: 這個檔案用來讀取記錄分 K 線的 cvs 檔，並新增相對應的日 K 線 cvs 檔

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

import re
import pandas as pd
import os
import datetime
import sys
from concurrent.futures import ProcessPoolExecutor
sys.path.append(os.path.dirname(os.path.abspath(__file__+"/..")))  # noqa
from utils import indicators  # noqa
from utils import config  # noqa


def process_min_file(min_file, data_dir):
    """
    生成單一 _min.csv 檔案對應的日K資料。

    Args:
        min_file (str): 輸入的 _min.csv 檔案名稱。
        data_dir (str): 包含分K資料檔案的資料夾。

    Returns:
        None
    """
    day_file = re.sub(r'_min\.csv$', r'_day.csv', min_file)
    print(f"將{min_file}轉成{day_file}")

    # 讀取分K資料
    min_data = pd.read_csv(os.path.join(data_dir, min_file))
    min_data.ts = pd.to_datetime(min_data.ts)
    min_data.set_index('ts', inplace=True)

    # 捨棄不合理資料
    min_data = min_data[(min_data != 0).all(axis=1)]

    # 生成日K資料
    day_data = min_data.resample('1D').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    })

    day_data = day_data.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])

    # 添加前一个索引值的新列
    pre_idx = day_data.index[0].strftime('%Y-%m-%d')
    day_data['Previous Index'] = pd.NA
    for i in day_data.index[1:]:
        day_data.loc[i, 'Previous Index'] = pre_idx
        pre_idx = i.strftime('%Y-%m-%d')

    # 計算均線
    indicators.set_ma(day_data)

    # 聚集
    indicators.set_concentrated(day_data)

    # 聚集 突破
    indicators.set_breakthrough(day_data)

    # 張嘴排列
    indicators.set_expansion(day_data)

    # 閉合排列
    indicators.set_clogging(day_data)

    # 區間高點
    indicators.set_range_high(day_data)

    # 高點連線
    indicators.set_high_point_connection(day_data)

    # 區間低點
    indicators.set_range_low(day_data)

    # 過前高
    indicators.set_over_high(day_data)

    # 破前低
    indicators.set_below_low(day_data)

    # 將生成的日K資料存儲到 _day.csv 檔案
    day_data.to_csv(os.path.join(data_dir, day_file), index=True)


def generate_day_data(data_dir):
    """
    根據分K資料生成日K資料。

    Args:
        data_dir (str): 包含分K資料檔案的資料夾。

    Returns:
        None
    """
    # 檢查資料夾是否存在
    if not os.path.exists(data_dir):
        print(f"找不到資料夾: {data_dir}")
        return

    # 取得資料夾中的所有 _min.csv 檔案
    min_files = [f for f in os.listdir(data_dir) if f.endswith("_min.csv")]

    # 使用 ProcessPoolExecutor 建立進程池
    with ProcessPoolExecutor() as executor:
        # 將任務提交到進程池中執行
        executor.map(process_min_file, min_files, [data_dir]*len(min_files))


if __name__ == '__main__':
    data_dir = config.DATA_DIR

    if not os.path.exists(data_dir):
        print(f"找不到資料夾: {data_dir}")
        exit()

    # 開始執行時間
    start_time = datetime.datetime.now()
    print(f"開始: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 生成日K資料
    generate_day_data(data_dir)

    # 結束執行時間
    end_time = datetime.datetime.now()
    print(f"結束: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 計算執行時間
    total_time = (end_time - start_time).total_seconds()
    print(f"程式共花費: {total_time} 秒")
