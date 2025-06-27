# evaluate_model.py

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import precision_score, recall_score, f1_score, multilabel_confusion_matrix
from app.data_loader import get_sparse_data, reload_data
from train_model import create_sequences, SEQUENCE_LENGTH, MODEL_PATH

# --- Cấu hình đánh giá ---
PREDICTION_THRESHOLD = 0.1

def evaluate_model():
    """Hàm chính để tải mô hình và đánh giá chi tiết trên tập dữ liệu kiểm tra."""
    print("--- BẮT ĐẦU QUÁ TRÌNH ĐÁNH GIÁ MÔ HÌNH ---")

    print("\n[BƯỚC 1/4] Tải dữ liệu và mô hình đã huấn luyện...")
    if not MODEL_PATH.exists():
        print(f"LỖI: Không tìm thấy file mô hình tại {MODEL_PATH}. Vui lòng chạy train_model.py trước.")
        return
    model = tf.keras.models.load_model(MODEL_PATH)
    reload_data()
    df_sparse = get_sparse_data()
    print(" -> Chuẩn hóa tên cột dữ liệu...")
    rename_map = {}
    for col in df_sparse.columns:
        try:
            num = int(col)
            if 0 <= num <= 99:
                new_name = f"{num:02d}"
                if col != new_name:
                    rename_map[col] = new_name
        except (ValueError, TypeError): continue
    if rename_map:
        df_sparse.rename(columns=rename_map, inplace=True)
    df_loto = df_sparse[[f"{i:02d}" for i in range(100)]]
    
    print("\n[BƯỚC 2/4] Chuẩn bị tập dữ liệu kiểm tra (Test Set)...")
    df_loto_binary = (df_loto > 0).astype(np.int8)
    test_split_index = int(len(df_loto_binary) * 0.9)
    test_data = df_loto_binary.iloc[test_split_index - SEQUENCE_LENGTH:]
    X_test, y_test_binary = create_sequences(test_data, SEQUENCE_LENGTH)
    if len(X_test) == 0:
        print("LỖI: Không đủ dữ liệu để tạo tập kiểm tra.")
        return
    print(f" -> Tập kiểm tra có {len(X_test)} mẫu.")

    print("\n[BƯỚC 3/4] Thực hiện dự đoán trên tập kiểm tra...")
    y_pred_proba = model.predict(X_test)

    print("\n[BƯỚC 4/4] Tính toán và phân tích kết quả:")

    print("-" * 50)
    print("--- ĐÁNH GIÁ HIỆU SUẤT DỰA TRÊN XẾP HẠNG (TOP N) ---")

    print("\n--- 4.1. ĐÁNH GIÁ HIT RATE (Tỷ lệ có ít nhất 1 số trúng) ---")
    top_n_values_hr = [1, 5, 10, 15]
    for n in top_n_values_hr:
        hits = 0
        for i in range(len(y_pred_proba)):
            top_n_indices = np.argsort(y_pred_proba[i])[-n:]
            actual_results = np.where(y_test_binary[i] == 1)[0]
            if len(set(top_n_indices) & set(actual_results)) > 0:
                hits += 1
        hit_rate = hits / len(y_test_binary)
        if n == 1:
            print(f"  - Tỷ lệ trúng Bạch Thủ Lô (Top 1): {hit_rate:.2%}")
        else:
            print(f"  - Hit Rate @ Top {n}: {hit_rate:.2%}")

    print("\n--- 4.2. ĐÁNH GIÁ CHI TIẾT CHO CHIẾN LƯỢC CHƠI DÀN TOP 10 ---")
    N = 10
    total_true_positives = 0
    total_predicted_positives = len(y_test_binary) * N
    total_actual_positives = np.sum(y_test_binary)
    
    for i in range(len(y_pred_proba)):
        top_n_indices = np.argsort(y_pred_proba[i])[-N:]
        actual_indices = np.where(y_test_binary[i] == 1)[0]
        hits = set(top_n_indices) & set(actual_indices)
        total_true_positives += len(hits)
        
    precision_at_n = total_true_positives / total_predicted_positives if total_predicted_positives > 0 else 0
    recall_at_n = total_true_positives / total_actual_positives if total_actual_positives > 0 else 0
    f1_at_n = 2 * (precision_at_n * recall_at_n) / (precision_at_n + recall_at_n) if (precision_at_n + recall_at_n) > 0 else 0

    print(f"  - Precision @ Top {N}: {precision_at_n:.2%}")
    print(f"    (Nếu ngày nào cũng chọn {N} số, tỷ lệ các số dự đoán là trúng thực sự)")
    print(f"  - Recall @ Top {N}:    {recall_at_n:.2%}")
    print(f"    (Chiến lược này đã tìm thấy được {recall_at_n:.2%} trong tổng số các kết quả về)")
    print(f"  - F1-Score @ Top {N}:  {f1_at_n:.2f}")

    print("-" * 50)
    
    print("--- PHÂN TÍCH MỘT VÀI NGÀY DỰ ĐOÁN CỤ THỂ ---")
    for i in range(min(3, len(X_test))):
        print(f"\n--- Ngày kiểm tra thứ {i+1} ---")
        actual_labels = [f"{idx:02d}" for idx, val in enumerate(y_test_binary[i]) if val == 1]
        top_1_index = np.argmax(y_pred_proba[i])
        top_1_prediction = f"{top_1_index:02d}"
        top_10_indices = np.argsort(y_pred_proba[i])[-10:][::-1]
        top_10_predictions = [f"{idx:02d}" for idx in top_10_indices]
        print(f"  - Kết quả thực tế: {', '.join(actual_labels)}")
        print(f"  - Dự đoán Bạch Thủ (Top 1): {top_1_prediction} (Xác suất: {y_pred_proba[i][top_1_index]:.2%})")
        print(f"  - Dự đoán Dàn Lô (Top 10): {', '.join(top_10_predictions)}")
        hit_in_top1 = "Trúng" if top_1_prediction in actual_labels else "Trượt"
        hits_in_top10 = set(actual_labels) & set(top_10_predictions)
        print(f"  => Kết quả Bạch Thủ: {hit_in_top1}")
        print(f"  => Trúng trong Top 10: {', '.join(sorted(list(hits_in_top10))) or 'Không có'}")

    print("\n--- QUÁ TRÌNH ĐÁNH GIÁ KẾT THÚC ---")

if __name__ == '__main__':
    evaluate_model()