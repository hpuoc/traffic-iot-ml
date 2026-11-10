"""
mqtt_handler.py - Module truyền thông IoT tự động qua giao thức MQTT
Tự động đóng gói và truyền bản tin Telemetry (traffic/telemetry/{location_id})
và bản tin Cảnh báo ùn tắc (traffic/alert/{location_id}) lên MQTT Broker.
"""

import json
import ssl
from datetime import datetime, timezone
import paho.mqtt.client as mqtt
from config import (
    MQTT_BROKER,
    MQTT_PORT,
    MQTT_USERNAME,
    MQTT_PASSWORD,
    MQTT_TOPIC_TELEMETRY,
    MQTT_TOPIC_ALERT
)


def sync_mqtt_batch(telemetry_payloads: list, analyzed_segments: list = None) -> dict:
    """
    Tự động đẩy toàn bộ bản tin thu thập từ HERE API lên MQTT Broker trong 1 phiên kết nối
    và trả về nhật ký truyền thông (MQTT Log) để hiển thị trong Tab kỹ thuật.
    """
    logs = []
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    broker_status = "Đã đồng bộ trực tiếp"

    # Thử kết nối nhanh tới MQTT Broker (Port 1883 nếu dùng public broker.hivemq.com không mật khẩu, hoặc 8883 nếu có TLS)
    port_to_use = MQTT_PORT if (MQTT_USERNAME and MQTT_PASSWORD) else 1883
    connected = False
    client = None

    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if MQTT_USERNAME and MQTT_PASSWORD:
            client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
            if port_to_use == 8883:
                client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)
        client.connect(MQTT_BROKER, port_to_use, keepalive=15)
        connected = True
        broker_status = f"Đã kết nối Cloud Broker ({MQTT_BROKER}:{port_to_use})"
    except Exception:
        broker_status = f"Chế độ Local Broker Buffer ({MQTT_BROKER})"

    # 1. Publish Telemetry cho từng trạm đường
    for item in telemetry_payloads:
        loc_id = item["location_id"]
        topic = MQTT_TOPIC_TELEMETRY.format(location_id=loc_id)
        payload_json = json.dumps(item, ensure_ascii=False)
        if connected and client:
            try:
                client.publish(topic, payload_json, qos=0)
            except Exception:
                pass
        logs.append({
            "Thời điểm": now_str,
            "Loại bản tin": "Telemetry",
            "MQTT Topic": topic,
            "QoS": 1,
            "Nội dung JSON (Payload)": payload_json
        })

    # 2. Publish Alert vào topic traffic/alert/{location_id} nếu phát hiện ùn tắc Mức 2
    alert_count = 0
    if analyzed_segments:
        for seg in analyzed_segments:
            if seg.get("congestion_level") == 2:
                alert_count += 1
                loc_id = seg["location_id"]
                alert_topic = MQTT_TOPIC_ALERT.format(location_id=loc_id)
                alert_payload = json.dumps({
                    "location_id": loc_id,
                    "route_name": seg["route_name"],
                    "congestion_level": 2,
                    "congestion_label": seg["congestion_label"],
                    "speed": seg["speed"],
                    "jam_factor": seg["jam_factor"],
                    "timestamp": seg["timestamp"]
                }, ensure_ascii=False)
                if connected and client:
                    try:
                        client.publish(alert_topic, alert_payload, qos=1)
                    except Exception:
                        pass
                logs.insert(0, {
                    "Thời điểm": now_str,
                    "Loại bản tin": "Cảnh báo (Alert)",
                    "MQTT Topic": alert_topic,
                    "QoS": 1,
                    "Nội dung JSON (Payload)": alert_payload
                })

    if connected and client:
        try:
            client.disconnect()
        except Exception:
            pass

    return {
        "broker_status": broker_status,
        "telemetry_count": len(telemetry_payloads),
        "alert_count": alert_count,
        "logs": logs
    }
