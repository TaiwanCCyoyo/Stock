#!/usr/bin/python3

import pandas as pd
import numpy as np

#
ma_cols_large = None
ma_cols_little = None
set_ma_done = False
max_ma_large = None
min_ma_large = None
diff_ma_large = None


def set_sma(df, n):
    """
    用來算SMA

    """
    df[f'SMA{n}'] = df['Close'].rolling(window=n).mean().round(2)
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
    df[f'EMA{n}'] = df['Close'].ewm(span=n).mean().round(2)

# End of set_ema


def set_ma(df):
    """
    用來算MA

    """
    global ma_cols_large
    global ma_cols_little
    global set_ma_done
    global max_ma_large
    global min_ma_large
    global diff_ma_large
    global max_ma_mid
    global min_ma_mid
    global diff_ma_mid
    global max_ma_little
    global min_ma_little
    global diff_ma_little
    set_sma(df, 5)
    set_sma(df, 10)
    set_sma(df, 20)
    set_sma(df, 60)
    set_sma(df, 120)
    set_ema(df, 20)
    set_ema(df, 60)
    set_ema(df, 120)

    ma_cols_large = ['Close', 'SMA5', 'SMA10', 'SMA20', 'SMA60', 'SMA120', 'EMA20', 'EMA60', 'EMA120']
    ma_cols_mid = ['Close', 'SMA5', 'SMA10', 'SMA20', 'SMA60', 'EMA20', 'EMA60']
    ma_cols_little = ['Close', 'SMA5', 'SMA10', 'SMA20', 'EMA20']
    max_ma_large = df[ma_cols_large].max(axis=1)
    min_ma_large = df[ma_cols_large].min(axis=1)
    max_ma_mid = df[ma_cols_mid].max(axis=1)
    min_ma_mid = df[ma_cols_mid].min(axis=1)
    max_ma_little = df[ma_cols_little].max(axis=1)
    min_ma_little = df[ma_cols_little].min(axis=1)
    diff_ma_large = max_ma_large - min_ma_large
    diff_ma_mid = max_ma_mid - min_ma_mid
    diff_ma_little = max_ma_little - min_ma_little

    # ma_cols_large = ['SMA5', 'SMA10', 'SMA20', 'SMA60', 'SMA120', 'EMA20', 'EMA60', 'EMA120']
    # ma_cols_mid = ['SMA5', 'SMA10', 'SMA20', 'SMA60', 'EMA20', 'EMA60']
    # ma_cols_little = ['SMA5', 'SMA10', 'SMA20', 'EMA20']
    # max_ma_large = df[ma_cols_large].max(axis=1)
    # max_ma_mid = df[ma_cols_mid].max(axis=1)
    # max_ma_little = df[ma_cols_little].max(axis=1)
    set_ma_done = True
# End of set_sma


def set_concentrated(df):
    """
    用來算聚集

    """
    if not set_ma_done:
        set_ma(df)

    # df['均線聚集'] = (diff_ma_large <= max_ma_large *
    #               0.02) & (~df.isnull().any(axis=1))

    df['均線聚集'] = (~df.isnull().any(axis=1) &
                  (diff_ma_large <= max_ma_large * 0.02))

    df['中均線聚集'] = (~df.isnull().any(axis=1) &
                   ((diff_ma_mid <= max_ma_mid * 0.02) &
                   (df['EMA120'] > df['SMA120'])))
    # df['短均線聚集'] = (~df.isnull().any(axis=1) &
    #                ((diff_ma_little <= max_ma_little * 0.21)))

    df['短均線聚集'] = (~df.isnull().any(axis=1) &
                   ((diff_ma_little <= max_ma_little * 0.02) &
                   (df['EMA20'] > df['EMA60']) & (df['SMA20'] > df['SMA60']) &
                   ((df['EMA60'] > df['EMA120']) | (df['EMA120'] > df['SMA120']))))

# End of set_concentrated


def set_breakthrough(df):
    """
    用來算聚集 突破

    """
    if not set_ma_done:
        set_ma(df)

    df['均線聚集後突破'] = (df['均線聚集']) & (df['Close'] == max_ma_large)

    df['中均線聚集後突破'] = (df['中均線聚集']) & (df['Close'] == max_ma_mid)

    df['短均線聚集後突破'] = (df['短均線聚集']) & (df['Close'] == max_ma_little)

# End of set_breakthrough


def set_expansion(df):
    """
    用來算突破後的張嘴排列

    """
    if not set_ma_done:
        set_ma(df)

    df['Expansion'] = ((df['均線聚集後突破']) &
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

    df['區間高點'] = (df['High'] >= df['High'].rolling(
        window=21, center=True).max())
# End of set_range_high


def set_high_point_connection(df):
    """
    用來算區間高點連線

    """
    df['高點連線'] = pd.NA
    pre_high = 0
    pre_high_diff = 0
    cnt = 0
    pre_cnt = 0
    pre_pre_cnt = 0
    pre_cnt_diff = 0

    for i in df.index[1:]:
        cnt += 1
        if (df.loc[i, '區間高點']):
            pre_high_diff = (df.loc[i, 'High'] - pre_high)
            pre_high = df.loc[i, 'High']
            pre_pre_cnt = pre_cnt
            pre_cnt = cnt
            pre_cnt_diff = pre_cnt - pre_pre_cnt

        if (pre_pre_cnt != 0):
            df.loc[i, '高點連線'] = round(pre_high + (pre_high_diff)/(pre_cnt_diff)*(cnt-pre_cnt), 2)


# End of set_high_point_connection


def set_range_low(df):
    """
    用來算區間低點

    """
    df['區間低點'] = (df['Low'] <= df['Low'].rolling(
        window=21, center=True).min())
# End of set_range_low


def set_over_high(df):
    """
    用來算過前高

    """
    df['前高'] = pd.NA
    df['前高 Index'] = pd.NA
    df['過前高'] = False

    pre_high_idx = np.nan
    pre_high = np.nan
    for i in df.index[1:]:
        df.loc[i, '前高 Index'] = pre_high_idx
        df.loc[i, '前高'] = pre_high

        if (pre_high != np.nan and df.loc[i, 'High'] > pre_high):
            df.loc[i, '過前高'] = True
        else:
            df.loc[i, '過前高'] = False

        if (df.loc[i, '區間高點']):
            pre_high = df.loc[i, 'High']
            pre_high_idx = i.strftime('%Y-%m-%d')


# End of set_over_high


def set_below_low(df):
    """
    用來算破底

    """

    df['前低'] = pd.NA
    df['前低 Index'] = pd.NA
    df['破底'] = False

    pre_low_idx = np.nan
    pre_low = np.nan
    for i in df.index[1:]:
        df.loc[i, '前低 Index'] = pre_low_idx
        df.loc[i, '前低'] = pre_low

        if (pre_low != np.nan and df.loc[i, 'Low'] < pre_low):
            df.loc[i, '破底'] = True
        else:
            df.loc[i, '破底'] = False

        if (df.loc[i, '區間低點']):
            pre_low = df.loc[i, 'Low']
            pre_low_idx = i.strftime('%Y-%m-%d')


# End of set_below_low
