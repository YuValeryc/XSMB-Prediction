import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from app.data_loader import get_sparse_data, reload_data
from pathlib import Path

SEQUENCE_LENGTH = 30
EPOCHS = 50
BATCH_SIZE = 32
MODEL_DIR = Path(__file__).parent / "app" / "model"
MODEL_PATH = MODEL_DIR / "lottery_lstm.h5"

def create_sequences(data: pd.DataFrame, seq_length: int):
    X, y = [], []
    data_np = data.values
    for i in range(len(data_np) - seq_length):
        X.append(data_np[i:(i + seq_length)])
        y.append(data_np[i + seq_length])
    return np.array(X), np.array(y)

def build_model(input_shape):
    model = Sequential([
        LSTM(units=128, return_sequences=True, input_shape=input_shape),
        Dropout(0.3),
        LSTM(units=64, return_sequences=False),
        Dropout(0.3),
        Dense(units=32, activation='relu'),
        Dense(units=100, activation='sigmoid')
    ])
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    model.summary()
    return model

def main():
    print("--- Bắt đầu quá trình huấn luyện mô hình ---")
    print("Bước 1: Tải dữ liệu...")
    reload_data()
    df_sparse = get_sparse_data()
    
    if df_sparse.empty or len(df_sparse) < SEQUENCE_LENGTH + 1:
        print(f"Lỗi: Không đủ dữ liệu để huấn luyện. Cần ít nhất {SEQUENCE_LENGTH + 1} ngày.")
        return

    df_loto = df_sparse[[str(i) for i in range(100)]]
    print(f"Bước 2: Tạo chuỗi dữ liệu với độ dài {SEQUENCE_LENGTH} ngày...")
    X, y = create_sequences(df_loto, SEQUENCE_LENGTH)
    
    if len(X) == 0:
        print("Không thể tạo chuỗi dữ liệu. Kiểm tra lại dữ liệu đầu vào.")
        return
        
    print(f" -> Dữ liệu đầu vào X có shape: {X.shape}")
    print(f" -> Dữ liệu đầu ra y có shape: {y.shape}")
    print("Bước 3: Xây dựng kiến trúc mô hình LSTM...")
    model = build_model(input_shape=(X.shape[1], X.shape[2]))
    print(f"Bước 4: Bắt đầu huấn luyện với {EPOCHS} epochs...")
    history = model.fit(
        X, y,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        validation_split=0.1,
        callbacks=[
            tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
        ]
    )
    print("Bước 5: Huấn luyện hoàn tất. Lưu mô hình...")
    MODEL_DIR.mkdir(exist_ok=True)
    model.save(MODEL_PATH)
    print(f"-> Mô hình đã được lưu tại: {MODEL_PATH}")
    print("--- Quá trình huấn luyện kết thúc ---")

if __name__ == '__main__':
    main()
