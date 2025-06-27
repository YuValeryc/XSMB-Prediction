# app/data_loader.py

import pandas as pd
from pathlib import Path

# Trạng thái dữ liệu được lưu trong bộ nhớ
_data_cache = {
    "sparse": None,
    "history": None,
}

DATA_DIR = Path(__file__).parent.parent / 'data'

def _load_data():
    """Hàm nội bộ để tải hoặc tải lại dữ liệu từ file."""
    print("Loading data from files...")
    try:
        sparse_path = DATA_DIR / 'xsmb-sparse.csv'
        history_path = DATA_DIR / 'xsmb.csv'
        
        df_sparse = pd.read_csv(sparse_path, parse_dates=['date'])
        df_sparse.set_index('date', inplace=True)
        # Đảm bảo các cột loto là string để khớp với logic sau này
        df_sparse.columns = df_sparse.columns.astype(str)
        _data_cache["sparse"] = df_sparse
        print(f"Loaded sparse data with {len(df_sparse)} records.")
        
        df_history = pd.read_csv(history_path, parse_dates=['date'])
        _data_cache["history"] = df_history.sort_values(by='date', ascending=False)
        print(f"Loaded history data with {len(df_history)} records.")

    except FileNotFoundError as e:
        print(f"Error loading data: {e}. Please run the scraper first.")
        # Khởi tạo DataFrame rỗng để tránh lỗi
        _data_cache["sparse"] = pd.DataFrame()
        _data_cache["history"] = pd.DataFrame()


def get_sparse_data() -> pd.DataFrame:
    """Lấy dữ liệu tần suất (sparse). Tải nếu chưa có trong cache."""
    if _data_cache["sparse"] is None:
        _load_data()
    return _data_cache["sparse"]

def get_history_data() -> pd.DataFrame:
    """Lấy dữ liệu lịch sử. Tải nếu chưa có trong cache."""
    if _data_cache["history"] is None:
        _load_data()
    return _data_cache["history"]

def reload_data():
    """Buộc tải lại dữ liệu từ file. Dùng sau khi scraper chạy."""
    print("Reloading data...")
    _load_data()