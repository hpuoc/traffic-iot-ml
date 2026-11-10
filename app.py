"""
app.py - Giao diện Web Dashboard Tìm lộ trình và Dự báo giao thông
Thiết kế tối giản, không dùng Sidebar, tự động đồng bộ MQTT ngầm 100%.
"""

import copy
import importlib
import streamlit as st
import pandas as pd
import plotly.express as px
import config
import collector
import ml_engine
import mqtt_handler

importlib.reload(config)
importlib.reload(collector)
importlib.reload(ml_engine)
importlib.reload(mqtt_handler)

from config import NODES
from collector import collect_all_routes
from ml_engine import TrafficPredictor
from mqtt_handler import sync_mqtt_batch

st.set_page_config(
    page_title="Hệ thống Dự báo Giao thông & Khuyến nghị Lộ trình",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Ẩn hoàn toàn nút mở Sidebar và định dạng các thẻ lộ trình sạch sẽ
st.markdown(
    """
    <style>
    [data-testid="collapsedControl"] { display: none; }
    section[data-testid="stSidebar"] { display: none; }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2.5rem;
        max-width: 1120px;
    }
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 4px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-right: 8px;
    }
    .badge-green { background-color: #e6f4ea; color: #137333; }
    .badge-amber { background-color: #fef7e0; color: #b06000; }
    .badge-red   { background-color: #fce8e6; color: #c5221f; }
    .badge-blue  { background-color: #e8f0fe; color: #1967d2; }

    .hero-card {
        background-color: #f8faf9;
        border: 1px solid #cce8d6;
        border-left: 5px solid #1e8e3e;
        border-radius: 8px;
        padding: 18px 22px;
        margin-bottom: 24px;
    }
    .route-time-big {
        font-size: 1.65rem;
        font-weight: 700;
        color: #202124;
        line-height: 1.2;
    }
    .route-meta {
        font-size: 0.9rem;
        color: #5f6368;
        margin-top: 2px;
    }
    .route-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #202124;
        margin-bottom: 6px;
    }
    .warning-text-red {
        color: #c5221f;
        font-size: 0.9rem;
        font-weight: 500;
    }
    .warning-text-amber {
        color: #b06000;
        font-size: 0.9rem;
        font-weight: 500;
    }
    .warning-text-green {
        color: #137333;
        font-size: 0.9rem;
        font-weight: 500;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Khởi tạo trạng thái kiểm thử giờ cao điểm (mặc định False -> luôn lấy 100% dữ liệu thật từ HERE API)
if "rush_hour_demo" not in st.session_state:
    st.session_state.rush_hour_demo = False

# Tiêu đề trang chính
st.markdown("## Hệ thống Dự báo Giao thông và Khuyến nghị Lộ trình")
st.caption("Thu thập dữ liệu thời gian thực từ HERE Traffic API v7, truyền tin tự động qua giao thức IoT MQTT và dự báo tắc nghẽn bằng mô hình Random Forest.")

# Khu vực chọn Điểm xuất phát - Điểm đích nằm ngang ngay đầu trang chính
node_keys = list(NODES.keys())
with st.container(border=True):
    col_orig, col_dest, col_btn = st.columns([4.2, 4.2, 1.6], vertical_alignment="bottom")
    with col_orig:
        origin_node = st.selectbox(
            "Điểm xuất phát",
            options=node_keys,
            index=0,
            format_func=lambda k: NODES[k]
        )
    with col_dest:
        dest_node = st.selectbox(
            "Điểm đích",
            options=node_keys,
            index=6,
            format_func=lambda k: NODES[k]
        )
    with col_btn:
        st.button("Tìm lộ trình", type="primary", use_container_width=True)

if origin_node == dest_node:
    st.warning("Điểm xuất phát và Điểm đích đang trùng nhau. Vui lòng chọn hai địa điểm khác nhau.")
    st.stop()

# 1. Thu thập dữ liệu thời gian thực từ HERE API v7
predictor = TrafficPredictor()
use_demo = st.session_state.rush_hour_demo
raw_payloads = collect_all_routes(save_csv=(not use_demo))

if use_demo:
    raw_payloads = copy.deepcopy(raw_payloads)
    severe_ids = {"route_01", "route_03", "route_11", "route_16", "route_19", "route_25", "route_29"}
    moderate_ids = {"route_04", "route_07", "route_12", "route_15", "route_20", "route_26", "route_30"}
    for p in raw_payloads:
        p["hour"] = 18
        if p["location_id"] in severe_ids:
            p["jam_factor"] = 8.6
            p["speed"] = round(p["free_flow"] * 0.22, 1)
        elif p["location_id"] in moderate_ids:
            p["jam_factor"] = 5.4
            p["speed"] = round(p["free_flow"] * 0.52, 1)

# 2. Dự báo ML và tìm lộ trình đa chặng
result = predictor.find_routes_between(raw_payloads, origin_node, dest_node, max_segments=4, top_k=6)
ranked_journeys = result["ranked_journeys"]
best_journey = result["best_journey"]
all_segments = result["all_segments"]

# 3. Tự động đồng bộ ngầm 100% qua MQTT Broker (ả Telemetry và Alert Mức 2)
mqtt_report = sync_mqtt_batch(raw_payloads, all_segments)

if not ranked_journeys:
    st.error("Không tìm thấy lộ trình phù hợp giữa hai địa điểm này.")
    st.stop()

worst_journey = ranked_journeys[-1]
time_saved = round(worst_journey["total_travel_time_min"] - best_journey["total_travel_time_min"], 1)
saved_note = f"Tiết kiệm {time_saved} phút so với tuyến chậm nhất" if time_saved > 0 else "Tuyến đường có thời gian di chuyển tối ưu nhất"

# ==================== 1. THẺ KHUYẾN NGHỊ LỘ TRÌNH TỐI ƯU NHẤT ====================
st.markdown(
    f"""
    <div class="hero-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 280px; padding-right: 16px;">
                <div>
                    <span class="badge badge-green">Lộ trình khuyến nghị</span>
                    <span style="font-size: 0.88rem; color: #137333; font-weight: 500;">{saved_note}</span>
                </div>
                <div style="font-size: 1.18rem; font-weight: 600; color: #202124; margin-top: 10px; margin-bottom: 6px;">
                    Qua {best_journey['journey_name']}
                </div>
                <div style="font-size: 0.92rem; color: #3c4043;">
                    {best_journey['bottleneck_warning']}
                </div>
            </div>
            <div style="text-align: right; min-width: 140px;">
                <div class="route-time-big" style="color: #137333;">{best_journey['total_travel_time_min']} phút</div>
                <div class="route-meta">{best_journey['total_length_km']} km • {best_journey['num_segments']} chặng</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ==================== 2. DANH SÁCH SO SÁNH CÁC LỘ TRÌNH THAY THẾ ====================
st.markdown(f"#### Các lộ trình từ {result['origin_name']} đến {result['dest_name']}")

for j in ranked_journeys:
    rank = j["rank"]
    lvl = j["worst_congestion_level"]

    if lvl == 0:
        status_badge = '<span class="badge badge-green">Thông thoáng</span>'
        warn_class = "warning-text-green"
    elif lvl == 1:
        status_badge = '<span class="badge badge-amber">Đông chậm</span>'
        warn_class = "warning-text-amber"
    else:
        status_badge = '<span class="badge badge-red">Có đoạn ùn tắc</span>'
        warn_class = "warning-text-red"

    rank_badge = '<span class="badge badge-blue">Khuyên đi</span>' if rank == 1 else ""
    diff_str = "Nhanh nhất" if rank == 1 else f"Chậm hơn {j['extra_time_min']} phút"

    with st.container(border=True):
        c_left, c_right = st.columns([3.6, 1.2], vertical_alignment="center")
        with c_left:
            st.markdown(
                f"""
                <div class="route-title">
                    Phương án {rank}: Qua {j['journey_name']}
                </div>
                <div style="margin-top: 4px;">
                    {rank_badge}{status_badge}
                    <span class="{warn_class}">{j['bottleneck_warning']}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
        with c_right:
            st.markdown(
                f"""
                <div style="text-align: right;">
                    <div class="route-time-big">{j['total_travel_time_min']} phút</div>
                    <div class="route-meta">{j['total_length_km']} km • {diff_str}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with st.expander(f"Xem chi tiết {j['num_segments']} chặng đường của Phương án {rank}"):
            seg_rows = []
            for s_idx, seg in enumerate(j["segments"], start=1):
                seg_rows.append({
                    "Chặng": f"Chặng {s_idx}",
                    "Đoạn đường": seg["route_name"],
                    "Quãng đường": f"{seg['length_km']} km",
                    "Tốc độ hiện tại": f"{seg['speed']} km/h",
                    "Thời gian qua chặng": f"{seg['travel_time_min']} phút",
                    "Trạng thái dự báo": seg["congestion_label"]
                })
            st.dataframe(pd.DataFrame(seg_rows), use_container_width=True, hide_index=True)

st.write("")

# ==================== 3. TAB BIỂU ĐỒ & THÔNG SỐ KỸ THUẬT Ở CUỐI TRANG ====================
tab_chart, tab_mqtt, tab_tech = st.tabs([
    "Biểu đồ so sánh thời gian lộ trình",
    "Nhật ký truyền tin IoT (MQTT Broker)",
    "Thông số kỹ thuật & Kiểm thử hệ thống"
])

with tab_chart:
    df_journeys = pd.DataFrame([
        {
            "Lộ trình": f"Phương án {j['rank']}: {j['journey_name']}",
            "Thời gian dự kiến (phút)": j["total_travel_time_min"],
            "Quãng đường (km)": j["total_length_km"],
            "Trạng thái": j["worst_congestion_label"]
        }
        for j in ranked_journeys
    ])
    fig = px.bar(
        df_journeys,
        x="Thời gian dự kiến (phút)",
        y="Lộ trình",
        color="Trạng thái",
        orientation="h",
        text="Thời gian dự kiến (phút)",
        color_discrete_map={
            "Thông thoáng": "#1e8e3e",
            "Đông chậm": "#f9ab00",
            "Ùn tắc nghiêm trọng": "#d93025"
        }
    )
    fig.update_layout(
        height=360,
        yaxis={"categoryorder": "total ascending"},
        margin={"l": 10, "r": 10, "t": 20, "b": 10},
        legend_title_text="Trạng thái"
    )
    st.plotly_chart(fig, use_container_width=True)

with tab_mqtt:
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("Trạng thái MQTT Broker", mqtt_report["broker_status"])
    m_col2.metric("Bản tin Telemetry đã đồng bộ", f"{mqtt_report['telemetry_count']} gói tin")
    m_col3.metric("Bản tin Cảnh báo (traffic/alert/#)", f"{mqtt_report['alert_count']} cảnh báo")
    st.caption("Danh sách các gói tin JSON vừa được truyền tự động qua topic chuẩn `traffic/telemetry/{location_id}` và `traffic/alert/{location_id}`:")
    st.dataframe(pd.DataFrame(mqtt_report["logs"]), use_container_width=True, hide_index=True)

with tab_tech:
    st.checkbox(
        "Bật chế độ dữ liệu kiểm thử giờ cao điểm (Dùng khi bảo vệ đồ án vào khung giờ vắng xe để minh họa tính năng né đoạn đường ùn tắc)",
        key="rush_hour_demo"
    )
    st.caption("Bảng dữ liệu Telemetry thời gian thực từ HERE Traffic API v7 và kết quả phân loại của mô hình Random Forest trên toàn bộ 30 đoạn đường:")
    df_all_seg = pd.DataFrame(all_segments)
    df_tech = df_all_seg[[
        "location_id", "route_name", "length_km", "speed", "free_flow",
        "jam_factor", "congestion_label", "travel_time_min", "ml_confidence_pct", "timestamp"
    ]].rename(columns={
        "location_id": "Mã trạm (Topic ID)",
        "route_name": "Tên đoạn đường",
        "length_km": "Độ dài (km)",
        "speed": "Tốc độ thực tế (km/h)",
        "free_flow": "Tốc độ lý tưởng (km/h)",
        "jam_factor": "Chỉ số Jam Factor (0-10)",
        "congestion_label": "Dự báo ML",
        "travel_time_min": "Thời gian (phút)",
        "ml_confidence_pct": "Độ tin cậy ML (%)",
        "timestamp": "Thời gian ghi nhận (UTC)"
    })
    st.dataframe(df_tech, use_container_width=True, hide_index=True)
