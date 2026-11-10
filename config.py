"""
config.py - Cấu hình trung tâm cho hệ thống Giám sát & Dự báo Giao thông IoT
Quy mô: Mạng lưới 10 Địa điểm đầu mối (Nodes) & 30 Đoạn đường thực tế (Segments) tại TP.HCM.
"""

import os

# 1. Cấu hình HERE Traffic API v7
HERE_API_KEY = os.getenv(
    "HERE_API_KEY",
    "RbnM9vxHn6UW-LBxvK2Du-ILMo_9eCKPgtk6ObD0Aws"
)
HERE_FLOW_API_URL = "https://data.traffic.hereapi.com/v7/flow"

# Khung chữ nhật (Bounding Box) bao trùm toàn bộ khu vực nội thành & cửa ngõ TP.HCM
HCMC_BBOX = "106.5800,10.7000,106.8200,10.8800"

# 2. Danh sách 10 Địa điểm / Nút giao thông trọng điểm tại TP.HCM
NODES = {
    "NODE_TSN": "Sân bay Tân Sơn Nhất (Tân Bình)",
    "NODE_GV":  "Ngã sáu Gò Vấp (Gò Vấp)",
    "NODE_TD":  "Cửa ngõ TP. Thủ Đức (Xa lộ Hà Nội)",
    "NODE_HX":  "Ngã tư Hàng Xanh (Bình Thạnh)",
    "NODE_PN":  "Ngã tư Phú Nhuận (Phú Nhuận)",
    "NODE_DC":  "Vòng xoay Dân Chủ (Quận 3 / Quận 10)",
    "NODE_BT":  "Chợ Bến Thành (Trung tâm Quận 1)",
    "NODE_TT":  "Khu đô thị Thủ Thiêm (TP. Thủ Đức)",
    "NODE_CL":  "Khu Chợ Lớn – Bến xe Miền Tây (Quận 5 / Quận 6)",
    "NODE_Q7":  "Khu đô thị Phú Mỹ Hưng (Quận 7)"
}

# 3. Danh sách 30 Đoạn đường thực tế (Segments) nối giữa 10 Địa điểm trên
ROUTES_CONFIG = {
    "route_01": {
        "from_node": "NODE_TSN", "to_node": "NODE_PN",
        "name": "Trường Sơn – Nguyễn Văn Trỗi",
        "lat": 10.8015, "lng": 106.6695, "radius": 800,
        "length_km": 2.4, "base_speed_kmh": 45.0
    },
    "route_02": {
        "from_node": "NODE_TSN", "to_node": "NODE_PN",
        "name": "Phổ Quang – Hoàng Minh Giám – Đào Duy Anh",
        "lat": 10.8068, "lng": 106.6728, "radius": 800,
        "length_km": 2.8, "base_speed_kmh": 42.0
    },
    "route_03": {
        "from_node": "NODE_TSN", "to_node": "NODE_DC",
        "name": "Cộng Hòa – Hoàng Văn Thụ – Lê Văn Sỹ",
        "lat": 10.7965, "lng": 106.6615, "radius": 800,
        "length_km": 3.8, "base_speed_kmh": 40.0
    },
    "route_04": {
        "from_node": "NODE_TSN", "to_node": "NODE_DC",
        "name": "Cộng Hòa – Trường Chinh – Cách Mạng Tháng Tám",
        "lat": 10.7915, "lng": 106.6545, "radius": 800,
        "length_km": 4.3, "base_speed_kmh": 40.0
    },
    "route_05": {
        "from_node": "NODE_TSN", "to_node": "NODE_GV",
        "name": "Bạch Đằng – Hồng Hà – Nguyễn Thái Sơn",
        "lat": 10.8155, "lng": 106.6755, "radius": 800,
        "length_km": 2.7, "base_speed_kmh": 45.0
    },
    "route_06": {
        "from_node": "NODE_TSN", "to_node": "NODE_GV",
        "name": "Phạm Văn Bạch – Quang Trung",
        "lat": 10.8285, "lng": 106.6585, "radius": 800,
        "length_km": 3.6, "base_speed_kmh": 40.0
    },
    "route_07": {
        "from_node": "NODE_GV", "to_node": "NODE_PN",
        "name": "Nguyễn Kiệm – Công viên Gia Định – Hồ Văn Huê",
        "lat": 10.8105, "lng": 106.6785, "radius": 800,
        "length_km": 2.6, "base_speed_kmh": 42.0
    },
    "route_08": {
        "from_node": "NODE_GV", "to_node": "NODE_HX",
        "name": "Đại lộ Phạm Văn Đồng – Cầu Bình Lợi – Nguyễn Xí",
        "lat": 10.8215, "lng": 106.7015, "radius": 800,
        "length_km": 4.1, "base_speed_kmh": 55.0
    },
    "route_09": {
        "from_node": "NODE_GV", "to_node": "NODE_HX",
        "name": "Phan Văn Trị – Lê Quang Định – Bạch Đằng",
        "lat": 10.8125, "lng": 106.6945, "radius": 800,
        "length_km": 3.8, "base_speed_kmh": 40.0
    },
    "route_10": {
        "from_node": "NODE_GV", "to_node": "NODE_TD",
        "name": "Phạm Văn Đồng – Hiệp Bình – Linh Đông",
        "lat": 10.8385, "lng": 106.7285, "radius": 800,
        "length_km": 5.2, "base_speed_kmh": 55.0
    },
    "route_11": {
        "from_node": "NODE_TD", "to_node": "NODE_HX",
        "name": "Võ Nguyên Giáp – Xa lộ Hà Nội – Cầu Sài Gòn",
        "lat": 10.8005, "lng": 106.7315, "radius": 800,
        "length_km": 3.5, "base_speed_kmh": 55.0
    },
    "route_12": {
        "from_node": "NODE_TD", "to_node": "NODE_HX",
        "name": "Quốc lộ 13 – Cầu Bình Triệu – Đinh Bộ Lĩnh",
        "lat": 10.8185, "lng": 106.7145, "radius": 800,
        "length_km": 4.2, "base_speed_kmh": 42.0
    },
    "route_13": {
        "from_node": "NODE_TD", "to_node": "NODE_TT",
        "name": "Nút giao An Phú – Đại lộ Mai Chí Thọ",
        "lat": 10.7885, "lng": 106.7415, "radius": 800,
        "length_km": 3.9, "base_speed_kmh": 55.0
    },
    "route_14": {
        "from_node": "NODE_TD", "to_node": "NODE_TT",
        "name": "Trần Não – Lương Định Của",
        "lat": 10.7855, "lng": 106.7285, "radius": 800,
        "length_km": 3.4, "base_speed_kmh": 45.0
    },
    "route_15": {
        "from_node": "NODE_HX", "to_node": "NODE_PN",
        "name": "Bạch Đằng – Phan Đăng Lưu",
        "lat": 10.8035, "lng": 106.6955, "radius": 800,
        "length_km": 2.7, "base_speed_kmh": 40.0
    },
    "route_16": {
        "from_node": "NODE_HX", "to_node": "NODE_BT",
        "name": "Điện Biên Phủ – Đinh Tiên Hoàng",
        "lat": 10.7925, "lng": 106.7015, "radius": 800,
        "length_km": 3.2, "base_speed_kmh": 45.0
    },
    "route_17": {
        "from_node": "NODE_HX", "to_node": "NODE_BT",
        "name": "Xô Viết Nghệ Tĩnh – Cầu Thị Nghè – Nguyễn Thị Minh Khai",
        "lat": 10.7885, "lng": 106.7055, "radius": 800,
        "length_km": 3.1, "base_speed_kmh": 42.0
    },
    "route_18": {
        "from_node": "NODE_HX", "to_node": "NODE_TT",
        "name": "Nguyễn Hữu Cảnh – Cầu Thủ Thiêm 1",
        "lat": 10.7905, "lng": 106.7186, "radius": 800,
        "length_km": 2.6, "base_speed_kmh": 50.0
    },
    "route_19": {
        "from_node": "NODE_PN", "to_node": "NODE_BT",
        "name": "Nam Kỳ Khởi Nghĩa – Võ Thị Sáu",
        "lat": 10.7865, "lng": 106.6885, "radius": 800,
        "length_km": 3.0, "base_speed_kmh": 42.0
    },
    "route_20": {
        "from_node": "NODE_PN", "to_node": "NODE_BT",
        "name": "Phan Đình Phùng – Cầu Kiệu – Hai Bà Trưng",
        "lat": 10.7895, "lng": 106.6915, "radius": 800,
        "length_km": 3.2, "base_speed_kmh": 40.0
    },
    "route_21": {
        "from_node": "NODE_PN", "to_node": "NODE_DC",
        "name": "Út Tịch – Hoàng Sa / Trường Sa (Kênh Nhiêu Lộc)",
        "lat": 10.7855, "lng": 106.6785, "radius": 800,
        "length_km": 2.8, "base_speed_kmh": 45.0
    },
    "route_22": {
        "from_node": "NODE_TT", "to_node": "NODE_BT",
        "name": "Hầm Thủ Thiêm – Đại lộ Võ Văn Kiệt",
        "lat": 10.7705, "lng": 106.7085, "radius": 800,
        "length_km": 2.5, "base_speed_kmh": 55.0
    },
    "route_23": {
        "from_node": "NODE_TT", "to_node": "NODE_BT",
        "name": "Cầu Ba Son – Tôn Đức Thắng – Lê Duẩn",
        "lat": 10.7782, "lng": 106.7115, "radius": 800,
        "length_km": 2.3, "base_speed_kmh": 50.0
    },
    "route_24": {
        "from_node": "NODE_TT", "to_node": "NODE_Q7",
        "name": "Vành Đai Đông – Cầu Phú Mỹ – Nguyễn Văn Linh",
        "lat": 10.7455, "lng": 106.7355, "radius": 800,
        "length_km": 5.0, "base_speed_kmh": 55.0
    },
    "route_25": {
        "from_node": "NODE_DC", "to_node": "NODE_BT",
        "name": "Cách Mạng Tháng Tám – Nguyễn Thị Nghĩa",
        "lat": 10.7735, "lng": 106.6895, "radius": 800,
        "length_km": 2.4, "base_speed_kmh": 40.0
    },
    "route_26": {
        "from_node": "NODE_DC", "to_node": "NODE_CL",
        "name": "Đường 3 Tháng 2 – Nguyễn Tri Phương – Hồng Bàng",
        "lat": 10.7665, "lng": 106.6695, "radius": 800,
        "length_km": 3.5, "base_speed_kmh": 42.0
    },
    "route_27": {
        "from_node": "NODE_CL", "to_node": "NODE_Q7",
        "name": "Nguyễn Văn Cừ – Dương Bá Trạc – Cầu Him Lam",
        "lat": 10.7485, "lng": 106.6885, "radius": 800,
        "length_km": 4.1, "base_speed_kmh": 42.0
    },
    "route_28": {
        "from_node": "NODE_BT", "to_node": "NODE_CL",
        "name": "Đại lộ Võ Văn Kiệt – Bến Chương Dương",
        "lat": 10.7555, "lng": 106.6785, "radius": 800,
        "length_km": 3.8, "base_speed_kmh": 52.0
    },
    "route_29": {
        "from_node": "NODE_BT", "to_node": "NODE_Q7",
        "name": "Hoàng Diệu – Cầu Kênh Tẻ – Nguyễn Hữu Thọ",
        "lat": 10.7515, "lng": 106.7015, "radius": 800,
        "length_km": 3.7, "base_speed_kmh": 42.0
    },
    "route_30": {
        "from_node": "NODE_BT", "to_node": "NODE_Q7",
        "name": "Nguyễn Tất Thành – Cầu Tân Thuận – Huỳnh Tấn Phát",
        "lat": 10.7565, "lng": 106.7185, "radius": 800,
        "length_km": 4.2, "base_speed_kmh": 42.0
    }
}

# 4. Hệ số làm chậm (Slowdown Factor) theo mức độ tắc nghẽn của mô hình ML
SLOWDOWN_FACTORS = {
    0: 1.0,   # Thông thoáng: giữ nguyên tốc độ cơ sở
    1: 0.65,  # Đông chậm: tốc độ giảm còn 65%
    2: 0.30   # Ùn tắc nghiêm trọng: tốc độ giảm còn 30%
}

CONGESTION_LABELS = {
    0: "Thông thoáng",
    1: "Đông chậm",
    2: "Ùn tắc nghiêm trọng"
}

# 5. Cấu hình MQTT Broker
MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
MQTT_PORT = int(os.getenv("MQTT_PORT", "8883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_TOPIC_TELEMETRY = "traffic/telemetry/{location_id}"
MQTT_TOPIC_ALERT = "traffic/alert/{location_id}"

# 6. Cấu hình Telegram Bot
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
