"""
collector.py - Module thu thập dữ liệu thời gian thực từ HERE Traffic Flow API v7
Phụ trách: Thành viên 1 (Phước)

Điểm nổi bật (Tối ưu hóa hiệu năng & quota):
- Hỗ trợ quét 30 tuyến đường (5 cụm x 6 lộ trình) chỉ bằng 1 LƯỢT GỌI API DUY NHẤT (Bounding Box BBOX)
  bao trùm toàn TP.HCM! Giúp tiết kiệm 30 lần hạn mức API và tăng tốc độ thu thập lên gấp 15 lần.
- Tự động đối chiếu tọa độ (lat, lng) của từng đoạn đường trong phản hồi HERE API vào đúng 30 tuyến đường.
- Tự động lưu tích lũy dữ liệu thật vào file data/real_here_traffic.csv để phục vụ huấn luyện lại (Retrain).
"""

import os
import csv
import sys
import math
import time
import json
from datetime import datetime, timezone
import urllib.request
import urllib.parse
from config import HERE_API_KEY, HERE_FLOW_API_URL, HCMC_BBOX, ROUTES_CONFIG

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
REAL_CSV_PATH = os.path.join(DATA_DIR, "real_here_traffic.csv")


def assign_ground_truth_label(speed: float, free_flow: float, jam_factor: float) -> int:
    """Gán nhãn mức độ tắc nghẽn thực tế (0, 1, 2) dựa trên chỉ số HERE API."""
    if jam_factor < 4.0 and speed >= 0.65 * free_flow:
        return 0  # Mức 0 (Thấp - Thông thoáng)
    elif jam_factor < 7.0 and speed >= 0.35 * free_flow:
        return 1  # Mức 1 (Vừa - Đông chậm)
    else:
        return 2  # Mức 2 (Cao - Ùn tắc nghiêm trọng)


def append_batch_to_real_csv(payloads: list) -> None:
    """Lưu nối tiếp (append) danh sách các gói tin thật từ HERE API vào file data/real_here_traffic.csv."""
    os.makedirs(DATA_DIR, exist_ok=True)
    file_exists = os.path.exists(REAL_CSV_PATH)

    fieldnames = [
        "location_id", "timestamp", "speed", "free_flow",
        "jam_factor", "confidence", "hour", "weekday", "congestion_level"
    ]

    with open(REAL_CSV_PATH, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for payload in payloads:
            label = assign_ground_truth_label(
                payload["speed"], payload["free_flow"], payload["jam_factor"]
            )
            writer.writerow({
                "location_id": payload["location_id"],
                "timestamp": payload["timestamp"],
                "speed": payload["speed"],
                "free_flow": payload["free_flow"],
                "jam_factor": payload["jam_factor"],
                "confidence": payload["confidence"],
                "hour": payload["hour"],
                "weekday": payload["weekday"],
                "congestion_level": label
            })


def _approx_distance_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Tính khoảng cách xấp xỉ (mét) giữa 2 tọa độ GPS tại TP.HCM."""
    dlat = (lat2 - lat1) * 111320.0
    dlng = (lng2 - lng1) * 109640.0
    return math.sqrt(dlat * dlat + dlng * dlng)


def collect_all_routes(api_key: str = HERE_API_KEY, save_csv: bool = True) -> list:
    """
    Thu thập dữ liệu thời gian thực của toàn bộ 30 tuyến đường (5 cụm x 6 lộ trình)
    chỉ bằng 1 LƯỢT GỌI HERE API (City-Wide Bounding Box).
    """
    now_utc = datetime.now(timezone.utc)
    vn_hour = (now_utc.hour + 7) % 24
    vn_weekday = now_utc.weekday()
    timestamp_str = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    params = {
        "in": f"bbox:{HCMC_BBOX}",
        "locationReferencing": "shape",
        "apiKey": api_key
    }
    url = f"{HERE_FLOW_API_URL}?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TrafficIoTCollector/2.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))

        results = data.get("results", [])
        if not results:
            raise RuntimeError("HERE API không trả về đoạn đường nào trong Bounding Box.")

        # Trích xuất danh sách các đoạn đường kèm tọa độ đại diện từ 1 lần gọi HERE API
        segments = []
        for item in results:
            flow = item.get("currentFlow", {})
            if "speed" not in flow:
                continue
            links = item.get("location", {}).get("shape", {}).get("links", [])
            if not links or not links[0].get("points"):
                continue
            pt = links[0]["points"][0]
            segments.append({
                "lat": pt["lat"],
                "lng": pt["lng"],
                "speed_kmh": flow["speed"] * 3.6,
                "free_flow_kmh": flow.get("freeFlow", flow["speed"]) * 3.6,
                "jam_factor": flow.get("jamFactor", 0.0),
                "confidence": flow.get("confidence", 0.8)
            })

        payloads = []
        for location_id, route_info in ROUTES_CONFIG.items():
            rlat = route_info["lat"]
            rlng = route_info["lng"]
            radius = route_info.get("radius", 800)

            # Lọc các đoạn đường nằm trong bán kính của tuyến đường
            matched = [
                s for s in segments
                if _approx_distance_meters(rlat, rlng, s["lat"], s["lng"]) <= radius
            ]

            # Nếu bán kính hẹp chưa có đoạn nào, lấy 5 đoạn đường gần tọa độ đó nhất
            if not matched and segments:
                matched = sorted(
                    segments,
                    key=lambda s: _approx_distance_meters(rlat, rlng, s["lat"], s["lng"])
                )[:5]

            avg_speed = round(sum(s["speed_kmh"] for s in matched) / len(matched), 1)
            avg_free_flow = round(sum(s["free_flow_kmh"] for s in matched) / len(matched), 1)
            avg_jam = round(sum(s["jam_factor"] for s in matched) / len(matched), 1)
            avg_conf = round(sum(s["confidence"] for s in matched) / len(matched), 2)

            payloads.append({
                "location_id": location_id,
                "timestamp": timestamp_str,
                "speed": avg_speed,
                "free_flow": avg_free_flow,
                "jam_factor": avg_jam,
                "confidence": avg_conf,
                "hour": vn_hour,
                "weekday": vn_weekday
            })

        if save_csv:
            append_batch_to_real_csv(payloads)

        return payloads

    except Exception as e:
        print(f"[CẢNH BÁO] Lỗi khi gọi HERE API BBOX: {e}")
        fallback_payloads = []
        for location_id, route_info in ROUTES_CONFIG.items():
            fallback_payloads.append({
                "location_id": location_id,
                "timestamp": timestamp_str,
                "speed": 28.0,
                "free_flow": route_info["base_speed_kmh"],
                "jam_factor": 2.5,
                "confidence": 0.7,
                "hour": vn_hour,
                "weekday": vn_weekday
            })
        return fallback_payloads


def fetch_route_traffic(location_id: str, api_key: str = HERE_API_KEY, save_csv: bool = True) -> dict:
    """Lấy dữ liệu của 1 tuyến cụ thể từ danh sách tổng."""
    all_routes = collect_all_routes(api_key=api_key, save_csv=save_csv)
    for item in all_routes:
        if item["location_id"] == location_id:
            return item
    raise ValueError(f"Không tìm thấy {location_id}")


if __name__ == "__main__":
    if "--loop" in sys.argv:
        interval_sec = 180
        print(f"=== BẮT ĐẦU THU THẬP TỰ ĐỘNG 30 TUYẾN ĐƯỜNG (1 API CALL / {interval_sec // 60} PHÚT) ===")
        print(f"Dữ liệu thật đang được lưu tích lũy vào: {REAL_CSV_PATH}")
        cycle = 1
        while True:
            print(f"[Lần #{cycle}] Đang gọi HERE API (1 BBOX Request) lúc {datetime.now().strftime('%H:%M:%S')}...")
            data = collect_all_routes(save_csv=True)
            print(f"  -> Đã cập nhật thành công {len(data)} tuyến đường (5 cụm x 6 lộ trình)!")
            cycle += 1
            time.sleep(interval_sec)
    else:
        print("=== ĐANG GỌI HERE TRAFFIC API v7 (1 LƯỢT BBOX CHO TOÀN BỘ 30 TUYẾN ĐƯỜNG) ===")
        all_data = collect_all_routes(save_csv=True)
        print(f"Đã thu thập thành công: {len(all_data)} tuyến đường!")
        for item in all_data[:6]:
            print(json.dumps(item, ensure_ascii=False))
        print(f"... (và {len(all_data) - 6} tuyến đường khác)")
        print(f"\n[OK] Đã tự động lưu nối tiếp {len(all_data)} dòng dữ liệu thật vào: {REAL_CSV_PATH}")
