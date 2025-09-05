import os
import numpy as np
import pandas as pd
import streamlit as st
from utils.ui.ui_tools import metric_with_tooltip, ensure_ui_css, render_segment_kpis
from sqlalchemy import create_engine, text
from pages.app_bootstrap import hide_builtin_nav, render_sidebar # 필수 
hide_builtin_nav()
render_sidebar()
ensure_ui_css()

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
        "VIP": "#2563eb",        # blue-600
        "LOYAL": "#059669",      # emerald-600
        "AT_RISK": "#dc2626",    # red-600
        "LOW": "#6b7280",        # gray-500
    }.get(seg, "#6b7280")
def seg_color_alpha(seg):
    # 각 세그먼트별로 alpha=0.5인 rgba 색상 반환
    colors = {
        "VIP": (37, 99, 235),      # blue-600
        "LOYAL": (5, 150, 105),    # emerald-600
        "AT_RISK": (220, 38, 38),  # red-600
        "LOW": (107, 114, 128),    # gray-500
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
# UI
# =========================
st.set_page_config(page_title="고객 그룹", layout="wide")
st.title("👥 고객 그룹")

# 세그먼트 한글 라벨
SEGMENT_LABELS = {
    # "VIP": "핵심 고객 (VIP)",
    # "LOYAL": "충성 고객 (LOYAL)",
    # "AT_RISK": "위험 고객 (RISK)",
    # "LOW": "저활성 고객 (LOW)",
    "VIP": "👑 핵심 고객(VIP)",
    "LOYAL": "🤝 충성 고객(LOYAL)",
    "AT_RISK": "⚠️ 위험 고객(RISK)",
    "LOW": "💤 저활성 고객(LOW)",
}

def seg_label(code: str) -> str:
    """라벨만 (아이콘 제거)"""
    label = SEGMENT_LABELS.get(code)
    if label:
        return label.lstrip("👑🤝⚠️💤 ").strip()
    return code
def seg_label_with_icon(code: str) -> str:
    return SEGMENT_LABELS.get(code, code)

df = load_rfm_joined()
if df.empty:
    st.warning("데이터가 없습니다. rfm_result_once / stg_churn_score를 확인하세요.")
    st.stop()

# 전역 KPI
k1, k2, k3, k4 = st.columns(4) 
with k1:
    metric_with_tooltip(
        "총 고객 수",
        f"{len(df):,}",
        tooltip="데이터셋에 포함된 전체 고객 수입니다."
    )
with k2:
    metric_with_tooltip(
        "평균 R/F/M",
        f"{df['r_score'].mean():.1f} / {df['f_score'].mean():.1f} / {df['m_score'].mean():.1f}",
        tooltip="Recency(최근성), Frequency(빈도), Monetary(금액)의 평균 점수입니다."
    )
with k3:
    metric_with_tooltip(
        "고가치(M≥4)",
        f"{(df['m_score']>=4).sum():,}",
        delta=f"{(df['m_score']>=4).mean()*100:.1f}%",
        tooltip="Monetary 점수가 4 이상인 고객 수와 전체 비율\r\n구매 금액 기준으로 우수한 상위 고객 집단"
    )
with k4:
    metric_with_tooltip(
        "Churn≥0.6",
        f"{(df['churn_probability'].fillna(0)>=0.6).sum():,}",
        tooltip="예측된 이탈 확률이 0.6 이상인 고객 수입니다."
    )
    
st.divider()

# 세그먼트별 데이터프레임
vip_df = df[df["segment_code"] == "VIP"].copy()
loyal_df = df[df["segment_code"] == "LOYAL"].copy()
risk_df = df[df["segment_code"] == "AT_RISK"].copy()
low_df = df[df["segment_code"] == "LOW"].copy()

# 선택 상태
if "selected_segment" not in st.session_state:
    st.session_state.selected_segment = None
    
# def make_layout(seg, df):
#     st.markdown(f"<div style='color:{seg_color(seg)}; font-weight:800; font-size:20px;'>{seg}</div>", unsafe_allow_html=True)
#     metric_block(st, f"{seg_label(seg)}", df)
#     if st.button(f"🔍 {seg_label((seg))} 사용자 보기", use_container_width=True):
#         st.session_state.selected_segment = seg

def make_layout(seg, df):
    color = seg_color_alpha(seg)
    st.markdown(
        f"""
        <div style="background:{color}; border-radius:12px; padding:16px; margin-bottom:12px; color:white;">
            <div style="font-weight:800; font-size:20px;">{seg_label_with_icon(seg)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    metric_block(st, f"{seg_label(seg)}", df)
    if st.button(f"🔍 {seg_label(seg)} 사용자 보기", use_container_width=True, key=f"btn_{seg}"):
        st.session_state.selected_segment = seg

# 4영역 레이아웃
c1, c2 = st.columns(2)
c3, c4 = st.columns(2)
with c1:
    make_layout('VIP', vip_df)
with c2:
    make_layout('LOYAL', loyal_df)
with c3:
    make_layout('AT_RISK', risk_df)
with c4:
    make_layout('LOW', low_df)

st.divider()

#####################################
# 선택된 세그먼트 사용자 목록
#####################################
st.markdown("""
<style>
.metric-wrap {
  display:grid; grid-template-columns: repeat(4, 1fr);
  gap: 0; align-items: start;
  padding: 8px 0; margin: 8px 0 18px 0;
  border-radius: 14px;
  background: linear-gradient(180deg, rgba(var(--surface-1), var(--panel-a)), rgba(var(--surface-1), var(--panel-b)));
  border: 1px solid rgba(var(--border-rgb), var(--card-border));
}
.metric {
  padding: 14px 18px 16px 18px;
  position: relative;
}
.metric + .metric::before{
  content:""; position:absolute; top:14px; bottom:14px; left:0;
  width:1px; background: rgba(var(--border-rgb), .12); /* 세로 디바이더 */
}

.metric .label {
  font-size: 13px; font-weight: 600; color: rgb(var(--txt-dim));
  display:flex; align-items:center; gap:8px;
}
.metric .value {
  margin-top: 8px; font-size: 34px; font-weight: 800; letter-spacing: -.01em;
  font-variant-numeric: tabular-nums; /* 자리수 정렬 */
}
.metric .sub {
  margin-top: 6px; font-size: 12px; color: rgb(var(--txt-dim));
}

/* 작은 화면에서 2열로 자동 래핑 */
@media (max-width: 1100px){
  .metric-wrap { grid-template-columns: repeat(2, 1fr); }
  .metric + .metric::before{ display:none; }
}
</style>
""", unsafe_allow_html=True)


seg = st.session_state.selected_segment

if seg:
    # 제목 (한글 라벨 사용)
    # st.subheader(f"📄 {seg_label(seg)} 목록")
    st.subheader(f"{seg_label_with_icon(seg)} 목록")

    # 세그먼트별 데이터프레임
    seg_df = {
        "VIP": vip_df,
        "LOYAL": loyal_df,
        "AT_RISK": risk_df,
        "LOW": low_df
    }[seg].copy()

    # 안전 캐스팅
    for col in ["r_score", "f_score", "m_score", "churn_probability", "monetary_90d", "recency_days", "frequency_90d"]:
        if col in seg_df.columns:
            seg_df[col] = pd.to_numeric(seg_df[col], errors="coerce")

    # === (NEW) 상단 KPI 보여주기 ===
    render_segment_kpis(seg_df)

    # 표시 컬럼 구성
    show_cols = [
        "customer_id", "surname",
        "r_score", "f_score", "m_score", 
        "churn_probability", "monetary_90d", "recency_days", "frequency_90d",
    ]
    for c in show_cols:
        if c not in seg_df.columns:
            seg_df[c] = pd.NA

    # 정렬 기준(기본: 고가치/고위험 우선)
    seg_df = (
        seg_df.assign(
            _m_score=seg_df["m_score"].fillna(-1),
            _cp=seg_df["churn_probability"].fillna(0.0),
        )
        .sort_values(["_m_score", "_cp"], ascending=[False, False])
        .drop(columns=["_m_score", "_cp"])
        .reset_index(drop=True)
    )

    # === (NEW) 보기 모드 버튼: 전체 / 고위험 비율 / Churn 상위 10명 ===
    btn_all, btn_risky, btn_top = st.columns([1,1,1])

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

    view_mode = st.session_state[state_key]

    # === (NEW) 모드별 데이터 선택 ===
    cp = pd.to_numeric(seg_df["churn_probability"], errors="coerce").fillna(0.0)

    if view_mode == "top10":
        view_df = (
            seg_df.assign(_cp=cp)
                .sort_values("_cp", ascending=False)
                .drop(columns=["_cp"])
                .head(10)
                .reset_index(drop=True)
        )
        st.markdown(
            '<span style="color:red; font-weight:bold; font-size:14px;">※ 이 세그먼트에서 예측 이탈확률이 가장 높은 10명</span>',
            unsafe_allow_html=True
        )

    elif view_mode == "risky":
        # 고위험: churn_probability ≥ 0.6
        view_df = (
            seg_df.loc[cp >= 0.6]
                .assign(_cp=cp[cp >= 0.6])
                .sort_values("_cp", ascending=False)
                .drop(columns=["_cp"])
                .reset_index(drop=True)
        )
        st.markdown(
            '<span style="color:#ea580c; font-weight:bold; font-size:14px;">※ 고위험(Churn ≥ 0.6) 고객 목록</span>',
            unsafe_allow_html=True
        )

    else:
        view_df = seg_df
        
    # === (NEW) 한글 컬럼명 매핑 ===
    col_labels = {
        "customer_id": "고객ID",
        "surname": "이름(성)",
        "r_score": "R 점수",
        "f_score": "F 점수",
        "m_score": "M 점수",
        "churn_probability": "이탈확률",
        "monetary_90d": "최근 잔액",
        "recency_days": "최근 거래일",
        "frequency_90d": "보유 상품 개수",
    }

    # 인덱스 조정 
    view_df.index = range(1, len(view_df) + 1)
    
    # 금액 표시
    if "monetary_90d" in view_df.columns:
        view_df["monetary_90d"] = (
            pd.to_numeric(view_df["monetary_90d"], errors="coerce")
            .fillna(0.0)
            .apply(lambda x: f"€{x:,.2f}")
        )

    # 이탈확률 퍼센트 변환
    if "churn_probability" in view_df.columns:
        view_df["churn_probability"] = pd.to_numeric(view_df["churn_probability"], errors="coerce").fillna(0.0)
        view_df["churn_probability"] = (view_df["churn_probability"] * 100).round(2).astype(str) + "%"

    # 컬럼명 변경 → show_cols 순서대로
    display_df = view_df[show_cols].rename(columns=col_labels)
    
    # 표 렌더
    st.dataframe(display_df, use_container_width=True, height=520)

    # 다운로드
    file_suffix = "top10" if view_mode == "top10" else "all"
    st.download_button(
        "⬇️ CSV 다운로드",
        data=view_df[show_cols].to_csv(index=False).encode("utf-8"),
        file_name=f"{seg.lower()}_{file_suffix}_customers.csv",
        mime="text/csv"
    )
else:
    st.info("상단의 각 세그먼트 카드에서 **사용자 보기** 버튼을 눌러 목록을 확인하세요.")