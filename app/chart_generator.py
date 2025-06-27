# app/chart_generator.py (Phiên bản mới, theo sát logic gốc)
import pandas as pd
import numpy as np

def pivot_to_chartjs_data(pivot_df):
    """
    Hàm tiện ích để chuyển đổi một DataFrame đã được pivot
    thành định dạng mà Chart.js heatmap có thể đọc.
    """
    chart_data = []
    for y_index, row in pivot_df.iterrows():
        for x_index, value in row.items():
            chart_data.append({
                'x': int(x_index), # Cột
                'y': int(y_index), # Dòng
                'v': int(value)    # Giá trị
            })
    return chart_data

def get_gan_chart_data(df_raw: pd.DataFrame):
    """
    Tái cấu trúc từ hàm last_appearing_loto của bạn.
    """
    try:
        # ----- BẮT ĐẦU LOGIC GIỐNG HỆT CỦA BẠN -----
        numbers = df_raw.drop(columns=['date'], errors='ignore').copy()
        numbers.reset_index(inplace=True)
        # Sử dụng 'index' từ DataFrame gốc làm số thứ tự ngày
        predict_index = numbers['index'].max() + 1
        numbers = numbers.melt(id_vars='index', var_name='prize', value_name='value')
        numbers['value'] = numbers['value'] % 100
        
        last_appearing = numbers.groupby('value')['index'].max()
        last_appearing = last_appearing.to_frame()
        last_appearing.reset_index(inplace=True)
        # last_appearing giờ có cột 'value' và 'index'
        
        last_appearing.rename(columns={'value': 'number'}, inplace=True)
        last_appearing['gan'] = predict_index - last_appearing['index']
        last_appearing.drop('index', axis=1, inplace=True)
        
        # Thêm các số chưa từng xuất hiện
        all_lotos = pd.DataFrame({'number': range(100)})
        last_appearing = pd.merge(all_lotos, last_appearing, on='number', how='left').fillna(predict_index)

        # 1. HEATMAP: Dùng logic pivot của bạn
        heatmap_df = last_appearing.copy()
        heatmap_df['tens'] = heatmap_df['number'] // 10
        heatmap_df['ones'] = heatmap_df['number'] % 10
        heatmap_df = heatmap_df.pivot(index='tens', columns='ones', values='gan').fillna(0).astype(int)
        
        # 2. BAR CHART: Dùng logic của bạn
        barchart_df = last_appearing.sort_values('gan', ascending=False).head(15)
        # ----- KẾT THÚC LOGIC CỦA BẠN -----

        # ----- BƯỚC CHUYỂN ĐỔI SANG JSON CHO WEB -----
        heatmap_data_json = pivot_to_chartjs_data(heatmap_df)
        barchart_data_json = {
            'labels': [f"{n:02d}" for n in barchart_df['number']],
            'data': [int(v) for v in barchart_df['gan']]
        }
        
        return {"heatmap": heatmap_data_json, "barchart": barchart_data_json}

    except Exception as e:
        print(f"ERROR in get_gan_chart_data: {e}")
        return {"error": str(e)}


def get_frequency_chart_data(df_sparse: pd.DataFrame):
    """
    Tái cấu trúc từ logic phân tích tần suất của bạn.
    """
    try:
        # ----- BẮT ĐẦU LOGIC GIỐNG HỆT CỦA BẠN -----
        df_lotos = df_sparse.drop(columns=['date'], errors='ignore')
        counts = df_lotos.sum(axis=0)
        counts = counts.reset_index()
        counts.columns = ['number', 'freq']
        counts['number'] = counts['number'].astype(int)

        # 1. HEATMAP: Dùng logic pivot của bạn
        heatmap_df = counts.copy()
        heatmap_df['tens'] = heatmap_df['number'] // 10
        heatmap_df['ones'] = heatmap_df['number'] % 10
        heatmap_df = heatmap_df.pivot(index='tens', columns='ones', values='freq').fillna(0).astype(int)

        # 2. BAR CHART: Dùng logic của bạn
        barchart_df = counts.sort_values('freq', ascending=False).head(15)
        
        # 3. DISTRIBUTION: Dùng logic của bạn
        freq_values = counts['freq'].values
        hist, bin_edges = np.histogram(freq_values, bins='auto')
        # ----- KẾT THÚC LOGIC CỦA BẠN -----

        # ----- BƯỚC CHUYỂN ĐỔI SANG JSON CHO WEB -----
        heatmap_data_json = pivot_to_chartjs_data(heatmap_df)
        barchart_data_json = {
            'labels': [f"{n:02d}" for n in barchart_df['number']],
            'data': [int(v) for v in barchart_df['freq']]
        }
        distribution_data_json = {
            'labels': [f"{int(edge)}" for edge in bin_edges[:-1]],
            'data': [int(v) for v in hist]
        }
        
        return {
            "heatmap": heatmap_data_json, 
            "barchart": barchart_data_json, 
            "distribution": distribution_data_json
        }
        
    except Exception as e:
        print(f"ERROR in get_frequency_chart_data: {e}")
        return {"error": str(e)}