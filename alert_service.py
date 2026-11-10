"""
alert_service.py - Dịch vụ gửi cảnh báo tự động qua Telegram Bot API
Phụ trách: Thành viên 3 (Web Dashboard & Notification Service)
"""

import urllib.request
import urllib.parse
import json
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_telegram_alert(route_result: dict) -> bool:
    """
    Tự động đẩy tin nhắn cảnh báo về điện thoại khi mô hình phát hiện Mức 2 (Ùn tắc nghiêm trọng).
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    message = (
        f"🚨 *CẢNH BÁO ÙN TẮC NGHIÊM TRỌNG (MỨC 2)* 🚨\n"
        f"📍 *Tuyến đường:* {route_result['route_name']}\n"
        f"🚗 *Tốc độ hiện tại:* {route_result['speed']} km/h (Lý tưởng: {route_result['free_flow']} km/h)\n"
        f"📊 *Chỉ số Jam Factor:* {route_result['jam_factor']} / 10.0\n"
        f"⏱ *Thời gian qua tuyến dự kiến:* {route_result['travel_time_min']} phút\n"
        f"🕒 *Thời điểm:* {route_result['timestamp']}"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=payload)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"[Telegram Alert Error] {e}")
        return False
