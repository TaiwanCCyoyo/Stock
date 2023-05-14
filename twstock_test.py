import argparse
import logging
import twstock
import numpy as np
import matplotlib.pyplot as plt
# from twstock import Stock
# import pandas as pd

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
    parser.add_argument('-u', '--update', dest='update',
                        action='store_true', help='twstock update codes')
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
    args = arg_parse()  # 命令參數解析
    logger = get_logger()  # 取得logger

    # 更新股票代號
    if (args.update):
        logger.info("更新股票代號...")
        twstock.__update_codes()
        logger.info("完成")

    # 取得上市櫃代號的相關資訊
    # stock_dict = twstock.codes
    # new_stock_dict = {}
    # for key, value in stock_dict.items():
    #     if (value[0] == "股票"):
    #         new_stock_dict[key] = value

    # stock_dict = new_stock_dict
    # logger.info("所有台股資訊")
    # logger.info(json.dumps(stock_dict, indent=4, ensure_ascii=False))

    key = '3260'
    stock = twstock.Stock(key)
    logger.info(stock.fetch_31()[0].open)


# 获取台股所有股票资讯
# stock_info = twstock.all

# # 遍历所有股票，获取当前股票的资讯
# for stock in stock_info:
#     sid = stock_info[stock]['code']
#     stock_price = twstock.realtime.get(sid)
#     ma_5 = twstock.indicator.calculate_ma(twstock.Stock(sid).close, 5)[-1]

#     # 判断当前股票是否在 5 日均线上
#     if stock_price and float(stock_price['realtime']['latest_trade_price']) >= ma_5:
#         print(sid, 'is on 5MA')
