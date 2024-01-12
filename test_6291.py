import os
import pickle
import pandas as pd

import os
import pandas as pd
import datetime


cache_dir = 'stock_cache_date'
cache_file = f'{cache_dir}/6291_cache_min.csv'
cache_file_update = f'{cache_dir}/6291_cache_min_update.csv'
pkl_cache_file = f'{cache_dir}/6291_cache_min.pkl'

df_csv = pd.read_csv(cache_file)
df_pkl = pd.read_pickle(pkl_cache_file)


print(df_csv.loc[769, 'ts'])
# print(df_csv.loc[770, 'ts'])
# print(datetime.datetime.fromtimestamp(df_csv.loc[769, 'ts']))
# print(datetime.datetime.fromtimestamp(df_csv.loc[770, 'ts']))
df_csv.ts = pd.to_datetime(df_csv.ts)
# print(df_csv.loc[769, 'ts'])
# print(df_csv.loc[770, 'ts'])


df_csv.set_index('ts', inplace=True)
# df_pkl.ts = pd.to_datetime(df_pkl.ts)
# df_pkl.set_index('ts', inplace=True)
# df_csv.to_csv(cache_file_update, index=True)

df_csv = df_csv.resample('1D').agg({
    'Open': 'first',
    'High': 'max',
    'Low': 'min',
    'Close': 'last',
    'Volume': 'sum'
})

for i in df_csv.index[1:]:
    print(i)
    print(df_csv.loc[i])
    print("\n")
    # print(type(df_csv.loc[i, 'Close']))
    if df_csv.loc[i, 'Close'] == 0:
        pass
print(df_pkl.loc[981])
