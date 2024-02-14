#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
描述: 這個檔案使用 shioaji 來下載台股的分K資料到 local 資料夾 (由 --cache_dir 指定)
登入 shioaji 所需要的 key 由 --key 指令
若已經有舊的資料，會查詢 local 端的資料新舊程度，來進行更新
若每日流量已經用完，也會登出結束程式
"""

import shioaji as sj
import pandas as pd
import argparse
import os
import datetime
import re
import json
import config
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__ + "/..")))  # noqa
from utils import stock_category  # noqa
from user_logger import user_logger  # noqa

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
    parser.add_argument('-l', '--log', dest='log', type=str, metavar='*.log',
                        default=f"{config.DEFAULT_LOG_DIR}/download_all_data.log", help='log file name')
    parser.add_argument('--cache_dir', dest='cache_dir', type=str,
                        metavar='*', default="stock_cache", help='local data cache directory')

    # 解析參數
    return parser.parse_args()
# End of arg_parse


if __name__ == '__main__':
    args = arg_parse()  # 命令參數解析
    logger = user_logger.user_logger.get_logger(args.log)  # 取得logger

    # 設定本地暫存檔名稱
    cache_dir = args.cache_dir

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    # 建立 Shioaji api 物件
    api = sj.Shioaji()

    # API key 以檔案形式存在 local
    if (os.path.isfile(args.key)):
        logger.info(f"從{args.key}讀取金鑰")
        try:
            with open(args.key, 'r') as f:
                api_key = f.readline().strip()
                secret_key = f.readline().strip()
        except Exception:
            logger.critical("Key 取得失敗")
            exit

    else:
        logger.critical(f"遺失{args.key}")
        exit

    logger.info('登入')
    accounts = api.login(
        api_key=api_key,
        secret_key=secret_key
    )

    start_time = datetime.datetime.now()
    today_date = datetime.datetime.now()
    today_str = today_date.strftime("%Y-%m-%d")
    today_date = datetime.datetime.strptime(today_str, '%Y-%m-%d')
    logger.info(f"開始: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 取得台股列表
    TSE_contract_list = api.Contracts.Stocks.TSE
    OTC_contract_list = api.Contracts.Stocks.OTC
    all_contracts = []

    # Extend the list with TSE contracts
    all_contracts.extend(TSE_contract_list)

    # Extend the list with OTC contracts
    all_contracts.extend(OTC_contract_list)
    # all_contracts = TSE_contract_list + OTC_contract_list

    # 建立股號股名對照表
    stock_symbol_name_mapping = {item.code: item.name for item in all_contracts}
    stock_symbol_name_mapping = dict(sorted(stock_symbol_name_mapping.items()))

    # 將對照表存儲為 JSON 檔案
    output_file_path = config.STOCK_SYMBOL_NAME_MAPPING
    with open(output_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(stock_symbol_name_mapping, json_file, ensure_ascii=False, indent=4)

    logger.info(f"股號股名對照表已存儲至 {output_file_path}")

    # 取得股票列表
    stock_contract_list = []
    for contract in all_contracts:
        if contract.category != stock_category.tse_stock_category_reverse_dict["期權"] \
                and re.match('^[0-9]+$', contract.code) and contract.update_date != today_str:
            stock_contract_list.append(contract)

    stock_contract_list.sort(key=lambda x: x.code)
    stock_contract_list = filter(lambda x: int(
        x.code) < 10000, stock_contract_list)
    for stock_contract in stock_contract_list:
        # 暫存檔名稱
        cache_file = f'{cache_dir}/{stock_contract.code}_cache_min.csv'

        start_date_str = '2018-12-07'
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
        if (os.path.isfile(cache_file)):
            # 讀取本地暫存檔
            logger.info(f"讀取{stock_contract.name} ({stock_contract.code}) 的資料")
            try:
                df = pd.read_csv(cache_file)
                df.ts = pd.to_datetime(df.ts)
                if not df.empty:
                    start_date = df.iloc[-1]['ts'] + \
                        datetime.timedelta(days=1)
                    start_date_str = start_date.strftime("%Y-%m-%d")
            except Exception:
                logger.critical(f"{cache_file}讀取失敗")

        if start_date >= today_date:
            logger.info(
                f"跳過{stock_contract.name} ({stock_contract.code}) 因為已經擁有 {start_date_str} 之前的資料")
            continue

        success = False
        while not success:
            logger.info(
                f"取得{stock_contract.name} ({stock_contract.code}) 從 {start_date_str} 到 {today_str} 的資料")
            # 取得 K 棒資料

            stock_get_start = datetime.datetime.now()
            kbars = api.kbars(
                contract=stock_contract,
                start=start_date_str,
                end=today_str
            )
            stock_get_end = datetime.datetime.now()
            logger.info(
                f"共花費: {(stock_get_end - stock_get_start).total_seconds()} 秒")
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

        if not success:
            logger.info(
                f"跳過{stock_contract.name} ({stock_contract.code}) 因為從 {start_date_str} 到 {today_str} 的資料取得失敗")
            continue

        if (os.path.isfile(cache_file)):
            # 讀取本地暫存檔
            logger.info(
                f"再次讀取{stock_contract.name} ({stock_contract.code}) 的資料")
            try:
                df_old = pd.read_csv(cache_file)
                logger.info("合併資料")
                merged_df = pd.concat([df_old, df], axis=0)
                df = merged_df
            except Exception:
                logger.critical(f"{cache_file}讀取失敗")

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

    api.logout()
    end_time = datetime.datetime.now()
    logger.info(f"結束: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

    total_time = (end_time - start_time).total_seconds()
    logger.info(f"程式共花費: {total_time} 秒")
