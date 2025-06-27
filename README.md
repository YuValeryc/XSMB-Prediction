# AI Soi Cầu - Hệ Thống Dự Đoán XSMB bằng Deep Learning

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.19+-orange.svg)](https://tensorflow.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Hệ thống phân tích và dự đoán xổ số miền Bắc (XSMB) sử dụng trí tuệ nhân tạo, bao gồm web scraper, mô hình LSTM, và giao diện web tương tác.

## Demo
![Demo](frontend/demo.gif)

## Tính Năng Chính

### AI Prediction
- **Mô hình LSTM**: Dự đoán số có khả năng về cao nhất
- **Deep Learning**: Sử dụng TensorFlow/Keras
- **Backtesting**: Kiểm tra độ chính xác trong quá khứ

### Phân Tích Dữ Liệu
- **Thống kê tần suất**: Phân tích xu hướng số
- **Hot/Cold Numbers**: Số nóng và lô gan
- **Biểu đồ trực quan**: Heatmap, Bar chart, Distribution

### Web Interface
- **Dashboard**: Bảng điều khiển tổng quan
- **Real-time**: Cập nhật dữ liệu theo thời gian thực
- **Responsive**: Tương thích mobile và desktop

## Cấu Trúc Dự Án

```
XSMB Prediction/
├── app/                    # Backend API
│   ├── main.py            # FastAPI server
│   ├── predictor.py       # LSTM prediction model
│   ├── data_loader.py     # Data management
│   ├── analysis.py        # Statistical analysis
│   ├── chart_generator.py # Chart data generation
│   └── model/             # Trained LSTM model
├── frontend/              # Web interface
│   ├── index.html         # Main page
│   ├── script.js          # Frontend logic
│   └── style.css          # Styling
├── data/                  # Lottery data
│   ├── xsmb.csv           # Raw lottery data
│   ├── xsmb-sparse.csv    # Processed frequency data
│   └── xsmb-2-digits.csv  # 2-digit results
├── scripts/               # Data collection
│   └── scraper.py         # Web scraper
├── train_model.py         # Model training script
├── requirements.txt       # Python dependencies
└── Dockerfile            # Container configuration
```

## Cài Đặt

### Bước 1: Clone Repository
```bash
git clone https://github.com/YuValeryc/XSMB-Prediction/
cd xsmb-prediction
```

### Bước 2: Tạo Virtual Environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

### Bước 3: Cài Đặt Dependencies
```bash
pip install -r requirements.txt
```

### Bước 4: Thu Thập Dữ Liệu
```bash
python scripts/scraper.py
```

### Bước 5: Huấn Luyện Mô Hình
```bash
python train_model.py
```

### Bước 6: Khởi Chạy Ứng Dụng
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Truy cập: http://localhost:8000

## Hướng Dẫn Sử Dụng

### Dashboard
- **Dự đoán AI**: Xem các số được AI gợi ý
- **Thống kê nóng/lạnh**: Số về nhiều và lô gan
- **Kết quả mới nhất**: Cập nhật real-time

### Phân Tích Biểu Đồ
- **Lô Gan**: Heatmap và bar chart số ngày chưa về
- **Tần Suất**: Phân tích xuất hiện trong khoảng thời gian
- **Tùy chỉnh**: Chọn số ngày phân tích (30-2000 ngày)

### Phân Tích Sâu
- **Soi số**: Chi tiết một con số cụ thể
- **Lịch sử xuất hiện**: Các ngày đã về
- **Thống kê chi tiết**: Tần suất theo thời gian

### Kiểm Tra AI
- **Backtesting**: Đánh giá độ chính xác
- **Chọn ngày**: Kiểm tra dự đoán trong quá khứ
- **So sánh**: AI prediction vs kết quả thực tế

### Lịch Sử
- **Tra cứu**: Xem kết quả các ngày trước
- **Tùy chỉnh**: Số ngày muốn xem (1-100)
- **Chi tiết**: Đầy đủ các giải thưởng

## API Endpoints

### Prediction
- `GET /predict?top_n=10` - Dự đoán AI
- `GET /predict/backtest?date=2024-01-01` - Kiểm tra dự đoán

### Statistics
- `GET /stats/frequency?days=30` - Thống kê tần suất
- `GET /stats/hot-cold?days=100&top_n=10` - Số nóng/lạnh
- `GET /stats/number-details/{number}` - Chi tiết một số

### Data
- `GET /history?limit=10` - Lịch sử kết quả
- `GET /charts/gan?days=365` - Dữ liệu biểu đồ lô gan
- `GET /charts/frequency?days=365` - Dữ liệu biểu đồ tần suất

## Mô Hình AI

### Kiến Trúc LSTM
```python
Sequential([
    LSTM(128, return_sequences=True),
    Dropout(0.3),
    LSTM(64, return_sequences=False),
    Dropout(0.3),
    Dense(32, activation='relu'),
    Dense(100, activation='sigmoid')
])
```

### Tham Số Huấn Luyện
- **Sequence Length**: 30 ngày
- **Epochs**: 50
- **Batch Size**: 32
- **Validation Split**: 10%
- **Early Stopping**: Patience = 5

### Dữ Liệu Đầu Vào
- **Format**: Sparse matrix (100 cột cho số 00-99)
- **Preprocessing**: Normalize về binary (0/1)
- **Augmentation**: Sliding window với sequence length

## Dữ Liệu

### Nguồn Dữ Liệu
- **Tham khảo**: https://github.com/khiemdoan/vietnam-lottery-xsmb-analysis/blob/main/src/analyze.py
- **Website**: xoso.com.vn
- **Thời gian**: Từ 2010 đến hiện tại
- **Format**: CSV/JSON

### Cấu Trúc Dữ Liệu
```csv
date,special,prize1,prize2_1,prize2_2,...
2024-01-01,12345,67890,1234,5678,...
```

### Xử Lý Dữ Liệu
- **Raw Data**: Dữ liệu gốc từ website
- **2-Digits**: Chỉ lấy 2 chữ số cuối
- **Sparse**: Ma trận tần suất xuất hiện

## Docker Deployment

### Build Image
```bash
docker build -t xsmb-prediction .
```

### Run Container
```bash
docker run -p 8000:8000 xsmb-prediction
```

## Disclaimer
- **Cảnh bảo**: Không khuyến khích chơi lô đề. Mọi con số chỉ mang tính chất tham khảo.

**Lưu ý quan trọng**: Dự án này chỉ mang tính chất nghiên cứu và giải trí. Dự đoán xổ số không đảm bảo kết quả chính xác. Không nên sử dụng để đánh bạc hoặc đặt cược thực tế.
