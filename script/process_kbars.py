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
import shioaji as sj
import pandas as pd
import argparse
import os
import datetime
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__+"/..")))  # noqa
from unils import shioaji_utils  # noqa
from unils import stock_category  # noqa
from user_logger import user_logger  # noqa
import config  # noqa


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
    parser.add_argument('--code', dest='code', type=str,
                        metavar='CODE', default="6291", help='The stock code to test')
    parser.add_argument('-l', '--log', dest='log', type=str,
                        metavar='*.log', default=f"{config.DEFAULT_LOG_DIR}/refresh_stock_data.log",
                        help='log file name')
    parser.add_argument('--cache_dir', dest='cache_dir', type=str,
                        metavar='*', default=config.DEFAULT_CACHE_DIR, help='本地資料緩存目錄')

    # 解析參數
    return parser.parse_args()


if __name__ == '__main__':
    args = arg_parse()  # 命令參數解析
    logger = user_logger.get_logger(args.log)  # 取得logger
    cache_dir = args.cache_dir

    if not os.path.exists(cache_dir):
        logger.critical(f"找不到資料夾: {cache_dir}")
        exit

    find_all_error_stock_data(args.cache_dir)

    # 建立 Shioaji api 物件
    api = sj.Shioaji()
    accounts = shioaji_utils.login_to_api(api, logger, args.key)

    # 開始
    start_time = datetime.datetime.now()
    logger.info(f"開始: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 取得今日 %Y-%m-%d 的時間格式
    today_date = start_time
    today_str = today_date.strftime("%Y-%m-%d")

    # 從 TSE 和 OTC 列表找到是否有此股票編號，並取得相關物件
    TSE_contract_list = api.Contracts.Stocks.TSE
    OTC_contract_list = api.Contracts.Stocks.OTC
    stock_contract = None
    for contract in TSE_contract_list:
        if contract.category != stock_category.tse_stock_category_reverse_dict["期權"] \
                and re.match(args.code, contract.code):
            stock_contract = contract

    if (stock_contract is None):
        for contract in OTC_contract_list:
            if contract.category != stock_category.tse_stock_category_reverse_dict["期權"]:
                if re.match(args.code, contract.code) and contract.update_date != today_str:
                    stock_contract = contract

    # 暫存檔名稱
    cache_file = f'{cache_dir}/{stock_contract.code}_cache_min.csv'

    # 嘗試取得資料
    success = False
    while not success:
        logger.info(
            f"取得{stock_contract.name} ({stock_contract.code}) 從 {shioaji_utils.sj_earliest_date_str} 到 {today_str} 的資料")

        # 取得 K 棒資料
        kbars = api.kbars(
            contract=stock_contract,
            start=shioaji_utils.sj_earliest_date_str,
            end=today_str
        )

        # 將資料轉換成 DataFrame
        df = pd.DataFrame({**kbars})
        if df.empty:
            usage_bytes = api.usage().bytes
            if usage_bytes < 524288000:
                logger.info(f"今日已使用 {usage_bytes} B")
                break
            else:
                logger.critical(f"今日已使用 {usage_bytes} B")
                api.logout()
                exit()
        else:
            success = True

    # 儲存結果
    if not success:
        logger.info(
            f"跳過{stock_contract.name} ({stock_contract.code}) "
            f"因為從 {shioaji_utils.sj_earliest_date_str} 到 {today_str} 的資料取得失敗"
        )
    else:
        # 將資料存儲到本地暫存檔
        try:
            logger.info('將資料存儲到本地暫存檔')
            df.to_csv(cache_file, index=False)
        except Exception:
            logger.warning(f"{cache_file} 儲存失敗")
            try:
                os.remove(cache_file)
            except OSError:
                pass

    # 登出並顯示結果
    api.logout()
    end_time = datetime.datetime.now()
    logger.info(f"結束: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

    total_time = (end_time - start_time).total_seconds()
    logger.info(f"程式共花費: {total_time} 秒")
