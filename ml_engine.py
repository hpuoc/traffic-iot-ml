"""
ml_engine.py - Pipeline Suy luận Học máy & Tìm đường Đa chặng (Origin -> Destination)
Phụ trách: Thành viên 1 (Phước)
"""

import os
import joblib
import pandas as pd
from config import NODES, ROUTES_CONFIG, SLOWDOWN_FACTORS, CONGESTION_LABELS

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")


class TrafficPredictor:
    def __init__(self):
        model_path = os.path.join(MODELS_DIR, "model.pkl")
        scaler_path = os.path.join(MODELS_DIR, "scaler.pkl")
        encoder_path = os.path.join(MODELS_DIR, "encoder.pkl")

        if not (os.path.exists(model_path) and os.path.exists(scaler_path) and os.path.exists(encoder_path)):
            from train_model import train_and_export
            train_and_export()

        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        self.encoder = joblib.load(encoder_path)

        if len(self.encoder.classes_) < len(ROUTES_CONFIG):
            from train_model import train_and_export
            train_and_export()
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            self.encoder = joblib.load(encoder_path)

    def predict_single_segment(self, payload: dict) -> dict:
        """Dự báo mức độ tắc nghẽn và tính thời gian di chuyển cho 1 đoạn đường (segment)."""
        loc_id = payload.get("location_id", "route_01")
        route_cfg = ROUTES_CONFIG.get(loc_id, ROUTES_CONFIG["route_01"])

        if loc_id in self.encoder.classes_:
            loc_encoded = int(self.encoder.transform([loc_id])[0])
        else:
            loc_encoded = 0

        features = pd.DataFrame([{
            "location_encoded": loc_encoded,
            "speed": payload["speed"],
            "free_flow": payload["free_flow"],
            "jam_factor": payload["jam_factor"],
            "hour": payload["hour"],
            "weekday": payload["weekday"]
        }])

        features_scaled = self.scaler.transform(features)
        pred_level = int(self.model.predict(features_scaled)[0])
        probabilities = self.model.predict_proba(features_scaled)[0]
        confidence_ml = round(float(max(probabilities)) * 100, 1)

        length_km = route_cfg["length_km"]
        base_speed = route_cfg["base_speed_kmh"]
        slowdown = SLOWDOWN_FACTORS[pred_level]

        effective_speed = round(base_speed * slowdown, 1)
        travel_time_minutes = round((length_km / effective_speed) * 60, 1)

        return {
            **payload,
            "from_node": route_cfg["from_node"],
            "to_node": route_cfg["to_node"],
            "route_name": route_cfg["name"],
            "length_km": length_km,
            "base_speed_kmh": base_speed,
            "congestion_level": pred_level,
            "congestion_label": CONGESTION_LABELS[pred_level],
            "ml_confidence_pct": confidence_ml,
            "slowdown_factor": slowdown,
            "effective_speed_kmh": effective_speed,
            "travel_time_min": travel_time_minutes,
            "is_severe_alert": pred_level == 2
        }

    def find_routes_between(
        self,
        payloads: list,
        origin_node: str,
        dest_node: str,
        max_segments: int = 4,
        top_k: int = 6
    ) -> dict:
        """
        Tìm và xếp hạng các lộ trình thay thế (mỗi lộ trình ghép từ nhiều đoạn đường)
        nối từ Điểm đi (origin_node) đến Điểm đến (dest_node).
        """
        analyzed_segments = {
            p["location_id"]: self.predict_single_segment(p) for p in payloads
        }

        adj = {node_id: [] for node_id in NODES}
        for seg_id, seg_data in analyzed_segments.items():
            u = seg_data["from_node"]
            v = seg_data["to_node"]
            adj[u].append((v, seg_data))
            adj[v].append((u, seg_data))

        all_candidate_journeys = []

        def dfs(current_node: str, visited_nodes: set, path_segments: list):
            if current_node == dest_node and path_segments:
                all_candidate_journeys.append(list(path_segments))
                return
            if len(path_segments) >= max_segments:
                return

            for neighbor_node, seg_info in adj.get(current_node, []):
                if neighbor_node not in visited_nodes:
                    visited_nodes.add(neighbor_node)
                    path_segments.append(seg_info)
                    dfs(neighbor_node, visited_nodes, path_segments)
                    path_segments.pop()
                    visited_nodes.remove(neighbor_node)

        if origin_node != dest_node:
            dfs(origin_node, {origin_node}, [])

        journey_results = []
        for segments in all_candidate_journeys:
            total_time = round(sum(s["travel_time_min"] for s in segments), 1)
            total_km = round(sum(s["length_km"] for s in segments), 1)
            avg_speed = round(sum(s["speed"] for s in segments) / len(segments), 1)
            max_jam = round(max(s["jam_factor"] for s in segments), 1)
            max_level = max(s["congestion_level"] for s in segments)

            path_title = " → ".join(s["route_name"] for s in segments)
            level2_segments = [s["route_name"] for s in segments if s["congestion_level"] == 2]
            level1_segments = [s["route_name"] for s in segments if s["congestion_level"] == 1]

            if level2_segments:
                bottleneck_warning = f"Cần né: Ùn tắc nghiêm trọng tại {', '.join(level2_segments)}"
            elif level1_segments:
                bottleneck_warning = f"Lưu ý: Đông chậm tại {', '.join(level1_segments)}"
            else:
                bottleneck_warning = "Toàn tuyến thông thoáng"

            journey_results.append({
                "journey_name": path_title,
                "segments": segments,
                "num_segments": len(segments),
                "total_length_km": total_km,
                "total_travel_time_min": total_time,
                "avg_speed_kmh": avg_speed,
                "max_jam_factor": max_jam,
                "worst_congestion_level": max_level,
                "worst_congestion_label": CONGESTION_LABELS[max_level],
                "level2_segments": level2_segments,
                "level1_segments": level1_segments,
                "bottleneck_warning": bottleneck_warning
            })

        ranked_journeys = sorted(
            journey_results,
            key=lambda j: (j["total_travel_time_min"], j["max_jam_factor"], j["total_length_km"])
        )[:top_k]

        best_time = ranked_journeys[0]["total_travel_time_min"] if ranked_journeys else 0.0
        for idx, j in enumerate(ranked_journeys):
            j["rank"] = idx + 1
            j["extra_time_min"] = round(j["total_travel_time_min"] - best_time, 1)

        return {
            "origin_node": origin_node,
            "origin_name": NODES.get(origin_node, origin_node),
            "dest_node": dest_node,
            "dest_name": NODES.get(dest_node, dest_node),
            "best_journey": ranked_journeys[0] if ranked_journeys else None,
            "ranked_journeys": ranked_journeys,
            "all_segments": list(analyzed_segments.values())
        }
