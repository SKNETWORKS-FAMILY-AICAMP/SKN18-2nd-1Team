import os
import numpy as np
import pandas as pd
import streamlit as st
from streamlit import column_config as cc
from streamlit_modal import Modal
from sqlalchemy import create_engine, text
from utils.ui.ui_tools import metric_with_tooltip, render_segment_kpis, show_table_data_by_view_mode, seg_label, seg_label_without_icon
from utils.llm.llm_ui import show_RFM_LLM_strategy
from pages.app_bootstrap import render_sidebar  # 필수

# =========================
# 공통 페이지 설정
# =========================
render_sidebar()
st.set_page_config(page_title="고객 그룹", layout="wide")
st.title("👥 고객 그룹(RFM)")

# =========================
# DB 연결 설정
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
    2) 없으면 rfm_result_once + stg_churn_score 즉시 조인
    2) 없으면 rfm_result_once + stg_churn_score 즉시 조인
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
        "VIP": "#2563eb",
        "LOYAL": "#059669",
        "AT_RISK": "#dc2626",
        "LOW": "#6b7280",
    }.get(seg, "#6b7280")

def seg_color_alpha(seg):
    colors = {
        "VIP": (37, 99, 235),
        "LOYAL": (5, 150, 105),
        "AT_RISK": (220, 38, 38),
        "LOW": (107, 114, 128),
    }
    r, g, b = colors.get(seg, (107, 114, 128))
    return f"rgba({r}, {g}, {b}, 0.3)"

def metric_block(container, title, df_seg):
    n = len(df_seg)
    m_avg = df_seg["m_score"].mean() if n else np.nan
    r_avg = df_seg["r_score"].mean() if n else np.nan
    f_avg = df_seg["f_score"].mean() if n else np.nan
    risk_avg = df_seg["churn_probability"].mean() if n else np.nan

    container.markdown(
        # <div style="font-weight:700; font-size:18px; margin-bottom:6px;">{title}</div>
        f"""
        <div style="border-radius:16px; padding:16px; background:rgba(0,0,0,0.03);">
          
          <div style="display:flex; gap:30px; flex-wrap:wrap;">
            <div><span style="opacity:.7;">고객수</span><br><b>{n:,}</b></div>
            <div><span style="opacity:.7;">평균 R/F/M</span><br><b>{r_avg:.1f} / {f_avg:.1f} / {m_avg:.1f}</b></div>
            <div><span style="opacity:.7;">평균 Churn</span><br><b>{fmt_pct(risk_avg)}</b></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================
# 데이터/전역 KPI
# =========================
df = load_rfm_joined()
if df.empty:
    st.warning("데이터가 없습니다. rfm_result_once / stg_churn_score를 확인하세요.")
    st.stop()

k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_tooltip("총 고객 수", f"{len(df):,}", tooltip="데이터셋에 포함된 전체 고객 수입니다.")
with k2:
    metric_with_tooltip("평균 R/F/M",
                        f"{df['r_score'].mean():.1f} / {df['f_score'].mean():.1f} / {df['m_score'].mean():.1f}",
                        tooltip="Recency/ Frequency/ Monetary 평균")
with k3:
    metric_with_tooltip("고가치(M≥4)",
                        f"{(df['m_score']>=4).sum():,}",
                        delta=f"{(df['m_score']>=4).mean()*100:.1f}%",
                        tooltip="Monetary 점수 4 이상 고객 수 / 비율")
with k4:
    metric_with_tooltip("Churn≥0.6",
                        f"{(df['churn_probability'].fillna(0)>=0.6).sum():,}",
                        tooltip="예측 이탈확률 0.6 이상 고객 수")

st.divider()

# 세그먼트별 DF
vip_df   = df[df["segment_code"] == "VIP"].copy()
loyal_df = df[df["segment_code"] == "LOYAL"].copy()
risk_df  = df[df["segment_code"] == "AT_RISK"].copy()
low_df   = df[df["segment_code"] == "LOW"].copy()

if "selected_segment" not in st.session_state:
    st.session_state.selected_segment = None

def make_layout(seg, df_seg):
    color = seg_color_alpha(seg)
    st.markdown(
        f"""
        <div style="background:{color}; border-radius:12px; padding:16px; margin-bottom:12px; color:white;">
            <div style="font-weight:800; font-size:20px;">{seg_label(seg)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    metric_block(st, f"{seg_label(seg)}", df_seg)
    if st.button(f"🔍 {seg_label_without_icon(seg)} 상세 보기", use_container_width=True, key=f"btn_{seg}"):
        st.session_state.selected_segment = seg

# 4영역 레이아웃
c1, c2 = st.columns(2)
c3, c4 = st.columns(2)
with c1: make_layout("VIP", vip_df)
with c2: make_layout("LOYAL", loyal_df)
with c3: make_layout("AT_RISK", risk_df)
with c4: make_layout("LOW", low_df)

st.divider()

# ==================================
# 선택된 세그먼트 사용자 목록
# ==================================
# 모달 생성
# modal = Modal("🧠 AI 고객 이탈 방지 전략", key="ai_strategy_modal", max_width=1280)
modal = Modal("🧠 AI 고객 이탈 방지 전략", key="ai_strategy_modal")

# 세그먼트 선택        
seg = st.session_state.selected_segment
if seg:
    # 제목 (한글 라벨 사용)
    st.subheader(f"{seg_label(seg)} 목록")

    seg_df = {"VIP": vip_df, "LOYAL": loyal_df, "AT_RISK": risk_df, "LOW": low_df}[seg].copy()

    # 안전 캐스팅
    for col in ["r_score", "f_score", "m_score", "churn_probability", "monetary_90d", "recency_days", "frequency_90d"]:
        if col in seg_df.columns:
            seg_df[col] = pd.to_numeric(seg_df[col], errors="coerce")

    # KPIs
    render_segment_kpis(seg_df)

    # 표 데이터
    show_cols = [
        "customer_id", "surname",
        "r_score", "f_score", "m_score", 
        "churn_probability", "monetary_90d", "recency_days", "frequency_90d",
    ]
    for c in show_cols:
        if c not in seg_df.columns:
            seg_df[c] = pd.NA
    seg_df = (
        seg_df.assign(_m=seg_df["m_score"].fillna(-1), _cp=seg_df["churn_probability"].fillna(0.0))
              .sort_values(["_m", "_cp"], ascending=[False, False])
              .drop(columns=["_m", "_cp"])
              .reset_index(drop=True)
    )

    #보기 모드 버튼: 전체 / 고위험 비율 / Churn 상위 10명
    btn_all, btn_risky, btn_top, btn_ai = st.columns([1,1,1,1])

    state_key = f"view_mode_{seg}"
    if state_key not in st.session_state:
        st.session_state[state_key] = "all"

    with btn_all:
        if st.button("📃 전체 보기", use_container_width=True, key=f"{seg}_all"):
            st.session_state[state_key] = "all"
    with btn_risky:
        if st.button("🧯 고위험 비율 목록", use_container_width=True, key=f"{seg}_risky"):
            st.session_state[state_key] = "risky"
    with btn_top:
        if st.button("🔥 Churn 상위 10명", use_container_width=True, key=f"{seg}_top10"):
            st.session_state[state_key] = "top10"
    with btn_ai:
        # 모달 열기 버튼
        if st.button("🧠 AI 고객 이탈 방지 전략", use_container_width=True, key=f"{seg}_llm_ai"
            , type="primary"
            ,help=(
                f"{seg_label(seg)} 그룹에 이탈 방지 전략을 AI가 추천합니다\n"
                "- 상위 리스크 고객 분석\n- 주요 이탈 요인\n- 권장 액션"
            )
        ):
            modal.open()
            st.session_state[state_key] = "llm_ai"

    # 모드별 데이터 선택
    view_mode = st.session_state[state_key]
    view_df = show_table_data_by_view_mode(view_mode, seg_df)

    # 인덱스 조정 
    view_df.index = range(1, len(view_df) + 1)
    # 이탈 확률 백분위
    view_df["churn_probability"] = view_df["churn_probability"] * 100
    
    # 표 렌더
    # st.dataframe(display_df, use_container_width=True, height=520)
    st.dataframe(
        view_df[show_cols],
        use_container_width=True,
        height=520,
        column_config={
            "customer_id": cc.Column("고객ID"),
            "surname": cc.Column("이름(성)"),
            "r_score": cc.NumberColumn("R 점수", format="%.1f"),
            "f_score": cc.NumberColumn("F 점수", format="%.1f"),
            "m_score": cc.NumberColumn("M 점수", format="%.1f"),
            "churn_probability": cc.NumberColumn("이탈확률", format="%.2f %%"),
            "monetary_90d": cc.NumberColumn("최근 잔액", format="€%.2f"),
            "recency_days": cc.NumberColumn("최근 거래일", format="%d"),
            "frequency_90d": cc.NumberColumn("가입 상품", format="%d"),
        }
    )

    # 다운로드
    file_suffix = "top10" if view_mode == "top10" else "all"
    st.download_button(
        "⬇️ CSV 다운로드",
        data=view_df[show_cols].to_csv(index=False).encode("utf-8"),
        file_name=f"{seg.lower()}_{file_suffix}_customers.csv",
        mime="text/csv",
    )
                
    # # LLM 요약/플레이북
    # show_RFM_LLM_strategy(seg_df=seg_df, seg=seg)
    
    # 모달 컨테이너 안에 LLM 플레이북 실행
    if modal.is_open():
        with modal.container():
            # st.subheader("📝 LLM 요약/플레이북")
            # 👉 여기서 LLM 함수 실행
            show_RFM_LLM_strategy(seg_df=seg_df, seg=seg)
            # 닫기 버튼
            if st.button("닫기", key="close_modal"):
                modal.close()