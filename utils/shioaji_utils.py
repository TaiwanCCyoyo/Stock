# shioaji_utils.py
import os
import datetime

# sj_earliest_date_str: Shioaji 支援的最早日期的字串表示
# 這個變數用來表示 Shioaji 庫存資料支援的最早日期，以字串形式表示。
# 在程式碼中，這是為了方便比較和顯示而將日期表示為字串。

# sj_earliest_date: Shioaji 支援的最早日期
# 這個變數用來表示 Shioaji 庫存資料支援的最早日期，轉換為 datetime.datetime 對象。
# 這使得在程式碼中能夠方便地進行日期比較和操作。
sj_earliest_date_str = '2018-12-07'
sj_earliest_date = datetime.datetime.strptime(sj_earliest_date_str, '%Y-%m-%d')


def login_to_api(api, logger, key_file):
    """
    登入 Shioaji API。

    Args:
        api (Shioaji): Shioaji API 物件。
        logger (Logger): Logger 物件。
        key_file (str): API 金鑰檔案路徑。

    Returns:
        list: 登入成功時返回帳戶清單，否則返回空列表。
    """
    if os.path.isfile(key_file):
        logger.info(f"從{key_file}讀取金鑰")
        try:
            with open(key_file, 'r') as f:
                api_key = f.readline().strip()
                secret_key = f.readline().strip()
        except Exception as e:
            logger.critical("Key 取得失敗。錯誤碼：" + str(e))
            exit()

    else:
        logger.critical(f"遺失{key_file}")
        exit()

    logger.info('登入')
    accounts = api.login(api_key=api_key, secret_key=secret_key)

    return accounts
