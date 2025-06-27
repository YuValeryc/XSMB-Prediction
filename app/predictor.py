# app/predictor.py
import numpy as np
import pandas as pd
import tensorflow as tf
from pathlib import Path

# --- Cấu hình ---
SEQUENCE_LENGTH = 30 
MODEL_PATH = Path(__file__).parent / "model" / "lottery_lstm.h5"

_model = None

def load_model():
    """Tải mô hình LSTM đã được huấn luyện vào bộ nhớ."""
    global _model
    if not MODEL_PATH.exists():
        print(f"Lỗi: Không tìm thấy file mô hình tại {MODEL_PATH}")
        return False
        
    print("Đang tải mô hình LSTM...")
    try:
        _model = tf.keras.models.load_model(MODEL_PATH)
        print("Tải mô hình thành công.")
        return True
    except Exception as e:
        print(f"Đã xảy ra lỗi khi tải mô hình: {e}")
        return False

def predict_with_lstm(df_sparse: pd.DataFrame, top_n: int = 10) -> dict:
    """
    Dự đoán các số có khả năng về cao nhất bằng mô hình LSTM.
    """
    global _model
    if _model is None:
        if not load_model():
            return {"error": f"Không thể tải mô hình. Vui lòng chạy file train_model.py trước."}

    recent_data = df_sparse.tail(SEQUENCE_LENGTH)
    
    if len(recent_data) < SEQUENCE_LENGTH:
        return {
            "error": f"Không đủ dữ liệu để dự đoán. Cần ít nhất {SEQUENCE_LENGTH} ngày dữ liệu lịch sử."
        }
    
    input_data = recent_data[[str(i) for i in range(100)]].values
    
    input_data = np.expand_dims(input_data, axis=0)

    predictions = _model.predict(input_data)[0] 

    top_indices = np.argsort(predictions)[-top_n:][::-1] 

    predicted_numbers = [str(i) for i in top_indices]
    probabilities = [float(predictions[i]) for i in top_indices]
    
    return {
        "description": f"Dự đoán {top_n} số có xác suất về cao nhất từ mô hình Deep Learning (LSTM)",
        "predictions": {
            number: f"{prob:.2%}" for number, prob in zip(predicted_numbers, probabilities)
        }
    }