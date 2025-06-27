# app/analysis.py

import pandas as pd

def get_frequency_stats(df_sparse: pd.DataFrame, days: int) -> dict:
    """Thống kê tần suất xuất hiện của các số trong N ngày gần nhất."""
    if df_sparse.empty or days <= 0:
        return {}
        
    last_n_days = df_sparse.tail(days)
    frequency = last_n_days.sum()
    frequency = frequency[frequency > 0].sort_values(ascending=False)
    return frequency.to_dict()

def get_hot_cold_numbers(df_sparse: pd.DataFrame, days: int, top_n: int) -> dict:
    """
    Lấy các số Nóng (về nhiều) và Lạnh (lô gan - lâu chưa về).
    - Nóng: Tần suất cao nhất trong `days` ngày gần đây.
    - Lạnh: Số ngày chưa về lâu nhất.
    """
    if df_sparse.empty:
        return {"hot": [], "cold": []}

    last_n_days_freq = df_sparse.tail(days).sum()
    hot_numbers = last_n_days_freq.nlargest(top_n).index.tolist()
    
    gan_days = (df_sparse == 0).iloc[::-1].cumprod().sum()
    cold_numbers = gan_days.nlargest(top_n).index.tolist()
    
    return {"hot": hot_numbers, "cold": cold_numbers}