#!/usr/bin/python3

import pandas as pd
import numpy as np

#
ma_cols = None
set_ma_done = False
max_ma = None
min_ma = None
diff_ma = None


def set_sma(df, n):
    """
    用來算SMA

    """
    df[f'SMA{n}'] = df['Close'].rolling(window=n).mean()
# End of set_sma


def set_ema(df, n):
    """
    計算指數移動平均 (EMA)

    參數：
    df: 包含價格資料的 DataFrame, 至少包含 'Close' 欄位
    n: 期間長度

    回傳：
    None( 會在原始 DataFrame 中添加一個名為 'EMA{n}' 的新欄位 )
    """
    df[f'EMA{n}'] = df['Close'].ewm(span=n).mean()

# End of set_ema


def set_ma(df):
    """
    用來算MA

    """
    global ma_cols
    global set_ma_done
    global max_ma
    global min_ma
    global diff_ma
    set_sma(df, 20)
    set_sma(df, 60)
    set_sma(df, 120)
    set_ema(df, 20)
    set_ema(df, 60)
    set_ema(df, 120)

    ma_cols = ['SMA20', 'SMA60', 'SMA120', 'EMA20', 'EMA60', 'EMA120']
    max_ma = df[ma_cols].max(axis=1)
    min_ma = df[ma_cols].min(axis=1)
    diff_ma = max_ma - min_ma
    set_ma_done = True
# End of set_sma


def set_concentrated(df):
    """
    用來算聚集

    """
    if not set_ma_done:
        set_ma(df)

    df['Concentrated'] = (diff_ma <= max_ma *
                          0.02) & (~df.isnull().any(axis=1))

# End of set_concentrated


def set_breakthrough(df):
    """
    用來算聚集 突破

    """
    if not set_ma_done:
        set_ma(df)

    df['Breakthrough'] = (df['Concentrated']) & (
        df['EMA20'] == max_ma) & (df['Close'] > df['EMA20'])

# End of set_breakthrough


def set_expansion(df):
    """
    用來算突破後的張嘴排列

    """
    if not set_ma_done:
        set_ma(df)

    df['Expansion'] = ((df['Breakthrough']) &
                       ((df['Close'] * 2 * 1.1) > (df['Close'].shift(20)*3 - df['Close'].shift(60))))

# End of set_expansion


def set_clogging(df):
    """
    用來算閉合排列

    """
    if not set_ma_done:
        set_ma(df)

    df['Clogging'] = (
        ((df['Close'] * 0.9 * 2) < (df['Close'].shift(20)*3 - df['Close'].shift(60))))

# End of set_clogging


def set_range_high(df):
    """
    用來算區間高點

    """

    df['Range High'] = (df['High'] >= df['High'].rolling(
        window=21, center=True).max())
# End of set_range_high


def set_range_low(df):
    """
    用來算區間低點

    """
    df['Range Low'] = (df['Low'] <= df['Low'].rolling(
        window=21, center=True).max())
# End of set_range_low


def set_high_and_high(df):
    """
    用來算過前高

    """
    df['Pre High'] = pd.NA
    df['Pre High Index'] = pd.NA
    df['High and High'] = False

    pre_high_idx = np.nan
    pre_high = np.nan
    high_and_high = False
    for i in df.index[1:]:
        df.loc[i, 'Pre High Index'] = pre_high_idx
        df.loc[i, 'Pre High'] = pre_high
        if (df.loc[i, 'Range High']):
            if (pre_high != np.nan and df.loc[i, 'High'] > pre_high):
                high_and_high = True
            else:
                high_and_high = False
            pre_high = df.loc[i, 'High']
            pre_high_idx = i

        df.loc[i, 'High and High'] = high_and_high
# End of set_high_and_high


def set_low_and_low(df):
    """
    用來算破底

    """

    df['Pre Low'] = pd.NA
    df['Pre Low Index'] = pd.NA
    df['Low and Low'] = False

    pre_low_idx = np.nan
    pre_low = np.nan
    low_and_low = False
    for i in df.index[1:]:
        df.loc[i, 'Pre Low Index'] = pre_low_idx
        df.loc[i, 'Pre Low'] = pre_low
        if (df.loc[i, 'Range Low']):
            if (pre_low != np.nan and df.loc[i, 'Low'] < pre_low):
                low_and_low = True
            else:
                low_and_low = False
            pre_low = df.loc[i, 'Low']
            pre_low_idx = i

        df.loc[i, 'Low and Low'] = low_and_low
# End of set_low_and_low
