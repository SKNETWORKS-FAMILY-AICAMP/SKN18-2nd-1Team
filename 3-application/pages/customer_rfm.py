# test_app2.py
import os
import numpy as np
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

# =========================
# DB 연결 설정 (환경변수로 오버라이드 가능)
# =========================
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "root1234")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "sknproject2")

ENGINE = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    pool_pre_ping=True
)

# =========================
# Data Access
# =========================
@st.cache_data(show_spinner=False)
def load_rfm_joined():
    """
    1) vw_rfm_for_app 뷰가 있으면 사용
    2) 없으면 rfm_result_once ⟂ stg_churn_score 즉시 조인
    (기존 앱 로딩 방식과 동일)
    """
    with ENGINE.begin() as conn:
        has_view = conn.execute(
            text("""
                SELECT COUNT(*) FROM information_schema.views
                WHERE table_schema=:db AND table_name='vw_rfm_for_app'
            """),
            {"db": DB_NAME}
        ).scalar() > 0

        if has_view:
            sql = "SELECT * FROM vw_rfm_for_app"
        else:
            sql = """
            SELECT r.customer_id, r.surname, r.recency_days, r.frequency_90d, r.monetary_90d,
                   r.r_score, r.f_score, r.m_score, r.rfm_code, r.segment_code,
                   s.churn_probability
            FROM rfm_result_once r
            LEFT JOIN stg_churn_score s
              ON s.customer_id = r.customer_id
            """
        df = pd.read_sql(text(sql), conn)

    if "churn_probability" not in df.columns:
        df["churn_probability"] = np.nan
    return df

# =========================
# Utils
# =========================
def fmt_pct(x):
    return "N/A" if pd.isna(x) else f"{x*100:.1f}%"

def seg_color(seg):
    return {
        "VIP": "#2563eb",        # blue-600
        "LOYAL": "#059669",      # emerald-600
        "AT_RISK": "#dc2626",    # red-600
        "LOW": "#6b7280",        # gray-500
    }.get(seg, "#6b7280")

def metric_block(container, title, df_seg):
    n = len(df_seg)
    m_avg = df_seg["m_score"].mean() if n else np.nan
    r_avg = df_seg["r_score"].mean() if n else np.nan
    f_avg = df_seg["f_score"].mean() if n else np.nan
    risk_avg = df_seg["churn_probability"].mean() if n else np.nan

    container.markdown(
        f"""
        <div style="border-radius:16px; padding:16px; background:rgba(0,0,0,0.03);">
          <div style="font-weight:700; font-size:18px; margin-bottom:6px;">{title}</div>
          <div style="display:flex; gap:16px; flex-wrap:wrap;">
            <div><span style="opacity:.7;">수량</span><br><b>{n:,}</b></div>
            <div><span style="opacity:.7;">평균 R/F/M</span><br><b>{r_avg:.1f} / {f_avg:.1f} / {m_avg:.1f}</b></div>
            <div><span style="opacity:.7;">평균 Churn</span><br><b>{fmt_pct(risk_avg)}</b></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================
# UI
# =========================
st.set_page_config(page_title="은행 고객 RFM 그룹화", layout="wide")
st.title("👥 은행 고객 RFM 그룹화 (VIP / LOYAL / AT_RISK / LOW)")

df = load_rfm_joined()
if df.empty:
    st.warning("데이터가 없습니다. rfm_result_once / stg_churn_score를 확인하세요.")
    st.stop()

# 전역 KPI
k1, k2, k3, k4 = st.columns(4)
k1.metric("총 고객 수", f"{len(df):,}")
k2.metric("평균 R/F/M", f"{df['r_score'].mean():.1f} / {df['f_score'].mean():.1f} / {df['m_score'].mean():.1f}")
k3.metric("고가치(M≥4)", f"{(df['m_score']>=4).sum():,}", delta=f"{(df['m_score']>=4).mean()*100:.1f}%")
k4.metric("Churn≥0.6", f"{(df['churn_probability'].fillna(0)>=0.6).sum():,}")

# 세그먼트별 데이터프레임
vip_df = df[df["segment_code"] == "VIP"].copy()
loyal_df = df[df["segment_code"] == "LOYAL"].copy()
risk_df = df[df["segment_code"] == "AT_RISK"].copy()
low_df = df[df["segment_code"] == "LOW"].copy()

# 선택 상태
if "selected_segment" not in st.session_state:
    st.session_state.selected_segment = None

# 4영역 레이아웃
c1, c2 = st.columns(2)
c3, c4 = st.columns(2)

with c1:
    st.markdown(f"<div style='color:{seg_color('VIP')}; font-weight:800; font-size:20px;'>VIP</div>", unsafe_allow_html=True)
    metric_block(st, "라벨: VIP", vip_df)
    if st.button("🔍 VIP 사용자 보기", use_container_width=True):
        st.session_state.selected_segment = "VIP"

with c2:
    st.markdown(f"<div style='color:{seg_color('LOYAL')}; font-weight:800; font-size:20px;'>LOYAL</div>", unsafe_allow_html=True)
    metric_block(st, "라벨: LOYAL", loyal_df)
    if st.button("🔍 LOYAL 사용자 보기", use_container_width=True):
        st.session_state.selected_segment = "LOYAL"

with c3:
    st.markdown(f"<div style='color:{seg_color('AT_RISK')}; font-weight:800; font-size:20px;'>AT_RISK</div>", unsafe_allow_html=True)
    metric_block(st, "라벨: AT_RISK", risk_df)
    if st.button("🔍 AT_RISK 사용자 보기", use_container_width=True):
        st.session_state.selected_segment = "AT_RISK"

with c4:
    st.markdown(f"<div style='color:{seg_color('LOW')}; font-weight:800; font-size:20px;'>LOW</div>", unsafe_allow_html=True)
    metric_block(st, "라벨: LOW", low_df)
    if st.button("🔍 LOW 사용자 보기", use_container_width=True):
        st.session_state.selected_segment = "LOW"

st.divider()

# 선택된 세그먼트 사용자 목록
seg = st.session_state.selected_segment
title_map = {
    "VIP": "VIP 사용자 목록",
    "LOYAL": "LOYAL 사용자 목록",
    "AT_RISK": "AT_RISK 사용자 목록",
    "LOW": "LOW 사용자 목록",
}
if seg:
    st.subheader(f"📄 {title_map.get(seg, seg)}")

    seg_df = {
        "VIP": vip_df,
        "LOYAL": loyal_df,
        "AT_RISK": risk_df,
        "LOW": low_df
    }[seg].copy()

    # 정렬 및 표시 컬럼
    show_cols = ["customer_id", "surname", "r_score", "f_score", "m_score", "rfm_code",
                 "segment_code", "churn_probability", "monetary_90d", "recency_days", "frequency_90d"]
    for c in show_cols:
        if c not in seg_df.columns:
            seg_df[c] = np.nan

    # 정렬: 고가치/고위험 우선
    # seg_df = seg_df.sort_values(["m_score", seg_df["churn_probability"].fillna(0)], ascending=[False, False]).reset_index(drop=True)

    # NaN을 0으로, 문자열이면 숫자로 강제 변환 후 정렬
    seg_df = (
        seg_df.assign(
            _m_score = pd.to_numeric(seg_df.get("m_score"), errors="coerce").fillna(-1),
            _churn_prob = pd.to_numeric(seg_df.get("churn_probability"), errors="coerce").fillna(0),
        )
        .sort_values(["_m_score", "_churn_prob"], ascending=[False, False])
        .drop(columns=["_m_score", "_churn_prob"])
        .reset_index(drop=True)
    )


    st.dataframe(seg_df[show_cols], use_container_width=True, height=500)

    # 다운로드
    st.download_button(
        "⬇️ 이 세그먼트 CSV 다운로드",
        data=seg_df[show_cols].to_csv(index=False).encode("utf-8"),
        file_name=f"{seg.lower()}_customers.csv",
        mime="text/csv"
    )
else:
    st.info("상단의 각 세그먼트 카드에서 **사용자 보기** 버튼을 눌러 목록을 확인하세요.")
