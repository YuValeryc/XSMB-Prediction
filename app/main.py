# app/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from fastapi import Query
from app.data_loader import get_sparse_data, get_history_data, reload_data
from app.analysis import get_frequency_stats, get_hot_cold_numbers
# Thay đổi import
from app.predictor import predict_with_lstm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.chart_generator import get_gan_chart_data, get_frequency_chart_data
from app.data_loader import get_sparse_data # Đảm bảo đã import

# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title="Lottery Analysis & Prediction API",
    description="API cung cấp dữ liệu phân tích và dự đoán xổ số bằng Deep Learning.",
    version="2.0.0",
)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend"), name="static")

# 2. Tạo một endpoint gốc để tự động chuyển hướng đến index.html
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/static/index.html")

@app.on_event("startup")
def on_startup():
    """Hành động khi server khởi động: chỉ cần tải dữ liệu."""
    print("Server is starting up...")
    reload_data()  # Tải dữ liệu lần đầu

@app.get("/", tags=["General"])
def read_root():
    return {"message": "Welcome to the Lottery Analysis & Prediction API!"}

# --- Các endpoint /stats/frequency và /history giữ nguyên như cũ ---

@app.get("/stats/frequency", tags=["Statistics"])
def get_frequency_endpoint(days: int = 30):
    df_sparse = get_sparse_data()
    if df_sparse.empty:
        raise HTTPException(status_code=404, detail="Data not found. Please run scraper.")
    return get_frequency_stats(df_sparse, days)

@app.get("/stats/hot-cold", tags=["Statistics"])
def get_hot_cold_endpoint(days: int = 100, top_n: int = 10):
    df_sparse = get_sparse_data()
    if df_sparse.empty:
        raise HTTPException(status_code=404, detail="Data not found. Please run scraper.")
    return get_hot_cold_numbers(df_sparse, days, top_n)

@app.get("/history", tags=["Data"])
def get_history_endpoint(limit: int = 10):
    df_history = get_history_data()
    if df_history.empty:
        raise HTTPException(status_code=404, detail="Data not found. Please run scraper.")
    return df_history.head(limit).to_dict('records')

# --- Cập nhật endpoint /predict ---
@app.get("/predict", tags=["Prediction"])
def get_prediction_endpoint(top_n: int = 10):
    """
    Lấy gợi ý các con số cho ngày hôm nay từ mô hình Deep Learning (LSTM).
    """
    df_sparse = get_sparse_data()
    if df_sparse.empty:
        raise HTTPException(status_code=404, detail="Data not found. Please run scraper.")
    
    prediction = predict_with_lstm(df_sparse, top_n=top_n)
    if "error" in prediction:
        # Nếu có lỗi (ví dụ: chưa có model), trả về lỗi 503
        raise HTTPException(status_code=503, detail=prediction["error"])
        
    return prediction

@app.get("/history/by-date", tags=["Data"])
def get_history_by_date(date: str = Query(..., description="Ngày cần tìm theo định dạng YYYY-MM-DD")):
    """
    Lấy kết quả xổ số của một ngày cụ thể.
    """
    try:
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Định dạng ngày không hợp lệ. Vui lòng dùng YYYY-MM-DD.")
    
    df_history = get_history_data()
    if df_history.empty:
        raise HTTPException(status_code=404, detail="Không có dữ liệu lịch sử.")
    
    # Chuyển đổi cột 'date' của dataframe sang kiểu date để so sánh
    result = df_history[df_history['date'].dt.date == target_date]
    
    if result.empty:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy kết quả cho ngày {date}.")
        
    # Trả về một danh sách chứa một phần tử (để frontend dễ xử lý)
    return result.to_dict('records')

@app.get("/stats/number-details/{number}", tags=["Statistics"])
def get_number_details(number: int):
    """
    Lấy thông tin chi tiết về một số cụ thể:
    - Ngày về gần nhất (gan)
    - Tần suất trong các khoảng thời gian
    - Lịch sử các ngày đã về
    """
    if not 0 <= number <= 99:
        raise HTTPException(status_code=400, detail="Số phải nằm trong khoảng từ 0 đến 99.")

    df_sparse = get_sparse_data()
    str_number = str(number)
    if df_sparse.empty or str_number not in df_sparse.columns:
        raise HTTPException(status_code=404, detail="Không có dữ liệu hoặc số không hợp lệ.")
    
    series = df_sparse[str_number]
    
    # Tính gan
    gan_days = (series == 0).iloc[::-1].cumprod().sum()
    
    # Lịch sử các ngày đã về
    appearance_dates = series[series > 0].index.strftime('%Y-%m-%d').tolist()
    
    # Tần suất
    freq_30d = df_sparse.tail(30)[str_number].sum()
    freq_90d = df_sparse.tail(90)[str_number].sum()
    freq_365d = df_sparse.tail(365)[str_number].sum()
    total_freq = series.sum()

    return {
        "number": number,
        "last_appearance_days_ago": int(gan_days),
        "frequency": {
            "last_30_days": int(freq_30d),
            "last_90_days": int(freq_90d),
            "last_365_days": int(freq_365d),
            "total": int(total_freq)
        },
        "appearance_history": appearance_dates
    }

@app.get("/predict/backtest", tags=["Prediction"])
def backtest_prediction(date: str = Query(..., description="Ngày cần kiểm tra theo định dạng YYYY-MM-DD")):
    """
    Kiểm tra lại dự đoán của AI cho một ngày trong quá khứ.
    """
    from app.predictor import predict_with_lstm # Import local để tránh circular dependency
    
    try:
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Định dạng ngày không hợp lệ. Vui lòng dùng YYYY-MM-DD.")

    df_history = get_history_data()
    df_sparse = get_sparse_data()

    # Lấy dữ liệu thực tế của ngày đó
    actual_result_row = df_sparse[df_sparse.index.date == target_date]
    if actual_result_row.empty:
        raise HTTPException(status_code=404, detail=f"Không có dữ liệu cho ngày {date}.")
    
    actual_numbers = [col for col in actual_result_row.columns if actual_result_row.iloc[0][col] > 0]

    # Lấy dữ liệu để dự đoán (tất cả các ngày TRƯỚC ngày target)
    prediction_data = df_sparse[df_sparse.index.date < target_date]

    # Thực hiện dự đoán
    prediction_result = predict_with_lstm(prediction_data, top_n=15)
    if "error" in prediction_result:
        raise HTTPException(status_code=500, detail=prediction_result["error"])

    predicted_numbers = list(prediction_result.get("predictions", {}).keys())
    
    # So sánh kết quả
    hits = set(actual_numbers) & set(predicted_numbers)

    return {
        "date": date,
        "ai_prediction": predicted_numbers,
        "actual_result": actual_numbers,
        "hits": sorted(list(hits)),
        "hit_count": len(hits)
    }
    
@app.get("/charts/gan", tags=["Charts"])
def get_gan_charts(days: int = 365):
    """Lấy dữ liệu cho biểu đồ Lô Gan trong N ngày gần nhất."""
    df_raw = get_history_data() # Hàm này đã có trong data_loader
    if df_raw.empty:
        raise HTTPException(status_code=404, detail="Không có dữ liệu gốc.")
    
    # Lọc dữ liệu trong khoảng thời gian
    df_period = df_raw.tail(days)
    return get_gan_chart_data(df_period)


@app.get("/charts/frequency", tags=["Charts"])
def get_frequency_charts(days: int = 365):
    """Lấy dữ liệu cho biểu đồ Tần Suất trong N ngày gần nhất."""
    df_sparse = get_sparse_data()
    if df_sparse.empty:
        raise HTTPException(status_code=404, detail="Không có dữ liệu sparse.")
        
    df_period = df_sparse.tail(days)
    return get_frequency_chart_data(df_period)