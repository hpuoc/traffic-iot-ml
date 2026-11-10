"""
train_model.py - Huấn luyện và đóng gói mô hình Machine Learning (.pkl)
Phụ trách: Thành viên 1 (Phước)

Cơ chế Hybrid thông minh (2 giai đoạn):
- Ngày 1: Khởi tạo 1.500 dòng dữ liệu giả lập chuẩn (data/simulated_traffic.csv) + gộp dữ liệu thật đã có
          trong data/real_here_traffic.csv để có ngay model.pkl chạy toàn hệ thống.
- Ngày 3: Khi đã cắm máy thu thập đủ dữ liệu thật vào data/real_here_traffic.csv, chỉ cần chạy lại
          file này (hoặc thêm cờ --real-only) để cập nhật model.pkl từ dữ liệu thật!
"""

import os
import sys
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from config import ROUTES_CONFIG

BASE_DIR = os.path.dirname(__file__)
MODELS_DIR = os.path.join(BASE_DIR, "models")
DATA_DIR = os.path.join(BASE_DIR, "data")
SIMULATED_CSV_PATH = os.path.join(DATA_DIR, "simulated_traffic.csv")
REAL_CSV_PATH = os.path.join(DATA_DIR, "real_here_traffic.csv")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)


def generate_training_data(n_samples: int = 3000) -> pd.DataFrame:
    """Tạo dữ liệu huấn luyện chuẩn hóa theo đặc trưng giao thông thực tế."""
    np.random.seed(42)
    route_ids = list(ROUTES_CONFIG.keys())

    records = []
    for _ in range(n_samples):
        loc_id = np.random.choice(route_ids)
        base_free_flow = ROUTES_CONFIG[loc_id]["base_speed_kmh"]
        free_flow = round(np.random.normal(base_free_flow, 3.0), 1)
        hour = np.random.randint(0, 24)
        weekday = np.random.randint(0, 7)

        # Giờ cao điểm (7-9h sáng, 17-19h chiều) dễ kẹt xe hơn
        is_rush_hour = hour in [7, 8, 9, 17, 18, 19] and weekday < 6
        if is_rush_hour:
            jam_factor = round(np.random.uniform(3.5, 10.0), 1)
        else:
            jam_factor = round(np.random.uniform(0.0, 7.5), 1)

        # Tốc độ thực tế tỷ lệ nghịch với jam_factor (0 -> 10)
        speed_ratio = max(0.1, 1.0 - (jam_factor / 11.0) + np.random.normal(0, 0.05))
        speed = round(max(3.0, min(free_flow, free_flow * speed_ratio)), 1)

        # Gán nhãn mục tiêu (0: Thấp, 1: Vừa, 2: Cao)
        if jam_factor < 4.0 and speed >= 0.65 * free_flow:
            label = 0  # Mức 0: Lưu thông bình thường
        elif jam_factor < 7.0 and speed >= 0.35 * free_flow:
            label = 1  # Mức 1: Chậm, mật độ tăng
        else:
            label = 2  # Mức 2: Ùn tắc nghiêm trọng

        records.append({
            "location_id": loc_id,
            "speed": speed,
            "free_flow": free_flow,
            "jam_factor": jam_factor,
            "hour": hour,
            "weekday": weekday,
            "congestion_level": label
        })

    df_sim = pd.DataFrame(records)
    df_sim.to_csv(SIMULATED_CSV_PATH, index=False, encoding="utf-8")
    return df_sim


def load_training_dataset(real_only: bool = False) -> pd.DataFrame:
    """
    Nạp dữ liệu huấn luyện:
    - Kết hợp dữ liệu giả lập chuẩn + dữ liệu thật thu từ HERE API (mặc định).
    - Hoặc chỉ dùng 100% dữ liệu thật nếu chạy với tham số --real-only.
    """
    cols = ["location_id", "speed", "free_flow", "jam_factor", "hour", "weekday", "congestion_level"]

    df_real = pd.DataFrame(columns=cols)
    if os.path.exists(REAL_CSV_PATH):
        df_real_raw = pd.read_csv(REAL_CSV_PATH)
        if not df_real_raw.empty:
            df_real = df_real_raw[cols]
            print(f"-> Đã tìm thấy {len(df_real)} mẫu dữ liệu THẬT từ HERE API trong: {REAL_CSV_PATH}")

    if real_only:
        if len(df_real) < 30:
            raise ValueError(
                f"Hiện mới có {len(df_real)} mẫu thật (cần tối thiểu 30 mẫu để chạy --real-only). "
                "Hãy chạy chế độ kết hợp mặc định trước!"
            )
        print("-> Đang huấn luyện 100% trên dữ liệu THẬT từ HERE API!")
        return df_real

    df_sim = generate_training_data(3000)
    print(f"-> Đã tạo và lưu 3.000 mẫu dữ liệu chuẩn (cho 30 tuyến đường) tại: {SIMULATED_CSV_PATH}")

    if not df_real.empty:
        df_combined = pd.concat([df_sim, df_real], ignore_index=True)
        print(f"-> Tổng số mẫu đưa vào huấn luyện (Chuẩn + Thật): {len(df_combined)} mẫu")
        return df_combined

    return df_sim


def train_and_export(real_only: bool = False):
    print("=== BẮT ĐẦU QUY TRÌNH HUẤN LUYỆN MÔ HÌNH HỌC MÁY ===")
    df = load_training_dataset(real_only=real_only)

    # Bước 1: LabelEncoder cho location_id
    encoder = LabelEncoder()
    df["location_encoded"] = encoder.fit_transform(df["location_id"])

    feature_cols = ["location_encoded", "speed", "free_flow", "jam_factor", "hour", "weekday"]
    X = df[feature_cols]
    y = df["congestion_level"].astype(int)

    # Bước 2: StandardScaler chuẩn hóa đặc trưng
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )

    # Bước 3: Huấn luyện Random Forest Classifier
    print("\nĐang huấn luyện mô hình Random Forest Classifier...")
    model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"-> Độ chính xác trên tập kiểm thử (Accuracy): {acc * 100:.2f}%\n")
    print(classification_report(y_test, y_pred, target_names=["Mức 0 (Thấp)", "Mức 1 (Vừa)", "Mức 2 (Cao)"]))

    # Bước 4: Xuất file .pkl bằng joblib
    model_path = os.path.join(MODELS_DIR, "model.pkl")
    scaler_path = os.path.join(MODELS_DIR, "scaler.pkl")
    encoder_path = os.path.join(MODELS_DIR, "encoder.pkl")

    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    joblib.dump(encoder, encoder_path)

    print(f"=== ĐÃ XUẤT THÀNH CÔNG 3 FILE MÔ HÌNH (.PKL) TẠI: {MODELS_DIR} ===")
    print(f"  1. {model_path}")
    print(f"  2. {scaler_path}")
    print(f"  3. {encoder_path}")


if __name__ == "__main__":
    use_real_only = "--real-only" in sys.argv
    train_and_export(real_only=use_real_only)
