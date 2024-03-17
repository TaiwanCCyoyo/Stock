import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__+"/..")))  # noqa
from shioaji_stock_prices.config import config as cg  # noqa

# DEFAULT_LOG_DIR 是用於定義預設的 Log 檔緩存目錄。
DEFAULT_LOG_DIR = "log"

# DATA_DIR 是用於定義預設的資料緩存目錄。
# 在整個專案中，這個目錄的名稱應該保持一致，以確保各個部分都能正確引用相同的目錄。
DATA_DIR = f"shioaji_stock_prices/{cg.DATA_DIR}"

# STOCK_CATEGORY 用於定義預設的股票類型對照表
STOCK_CATEGORY = f"shioaji_stock_prices/{cg.STOCK_CATEGORY}"

# SHIOAJI_START_DATE 用於定義 shioaji 資料的起始日期
SHIOAJI_START_DATE = cg.SHIOAJI_START_DATE

# STOCK_SYMBOL_MAPPING 用於定義預設的股票鼓號對照表
STOCK_SYMBOL_MAPPING = f"shioaji_stock_prices/{cg.STOCK_SYMBOL_MAPPING}"
