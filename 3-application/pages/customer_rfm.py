import os
import numpy as np
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from utils.ui.ui_tools import metric_with_tooltip, ensure_ui_css, render_segment_kpis
from pages.app_bootstrap import hide_builtin_nav, render_sidebar  # 필수

# ───────────────────────────────────────────────────────────────
# LLM 추천 래퍼
try:
    from utils.llm.reco_templates import recommend_for_segment, SEGMENT_BUNDLES, PRODUCT_CATALOG
    _PROD_MAP = {p["code"]: p for p in PRODUCT_CATALOG}
except Exception:
    recommend_for_segment = None
    SEGMENT_BUNDLES = {}
    PRODUCT_CATALOG = []
    _PROD_MAP = {}

# ───────────────────────────────────────────────────────────────
hide_builtin_nav()
render_sidebar()
ensure_ui_css()

st.set_page_config(page_title="고객 그룹", layout="wide")
st.title("👥 고객 그룹")

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
    2) 없으면 rfm_result_once ⟂ stg_churn_score 즉시 조인
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
    return f"rgba({r}, {g}, {b}, 0.4)"

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

SEGMENT_LABELS = {
    "VIP": "핵심 고객 (VIP)",
    "LOYAL": "충성 고객 (LOYAL)",
    "AT_RISK": "위험 고객 (RISK)",
    "LOW": "저활성 고객 (LOW)",
}
def seg_label(code: str) -> str:
    return SEGMENT_LABELS.get(code, code)

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
    if st.button(f"🔍 {seg_label(seg)} 사용자 보기", use_container_width=True, key=f"btn_{seg}"):
        st.session_state.selected_segment = seg

# 4영역
c1, c2 = st.columns(2)
c3, c4 = st.columns(2)
with c1: make_layout("VIP", vip_df)
with c2: make_layout("LOYAL", loyal_df)
with c3: make_layout("AT_RISK", risk_df)
with c4: make_layout("LOW", low_df)

st.divider()

# 선택된 세그먼트 목록 + LLM 요약/플레이북
seg = st.session_state.selected_segment
if seg:
    st.subheader(f"📄 {seg_label(seg)} 목록")

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
        "segment_code",
        "r_score", "f_score", "m_score", "rfm_code",
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

    # 보기 모드
    b1, b2 = st.columns([1, 1])
    if f"view_mode_{seg}" not in st.session_state:
        st.session_state[f"view_mode_{seg}"] = "all"
    with b1:
        if st.button("📃 전체 보기", use_container_width=True, key=f"{seg}_all"):
            st.session_state[f"view_mode_{seg}"] = "all"
    with b2:
        if st.button("🔥 Churn 상위 10명", use_container_width=True, key=f"{seg}_top10"):
            st.session_state[f"view_mode_{seg}"] = "top10"
    view_mode = st.session_state[f"view_mode_{seg}"]

    if view_mode == "top10":
        view_df = (
            seg_df.assign(_cp=seg_df["churn_probability"].fillna(0.0))
                  .sort_values("_cp", ascending=False)
                  .drop(columns=["_cp"])
                  .head(10)
                  .reset_index(drop=True)
        )
        st.caption("※ 이 세그먼트에서 예측 이탈확률이 가장 높은 10명")
    else:
        view_df = seg_df

    st.dataframe(view_df[show_cols], width="stretch", height=520)

    file_suffix = "top10" if view_mode == "top10" else "all"
    st.download_button(
        "⬇️ CSV 다운로드",
        data=view_df[show_cols].to_csv(index=False).encode("utf-8"),
        file_name=f"{seg.lower()}_{file_suffix}_customers.csv",
        mime="text/csv",
    )

    # ── 세그먼트 대표 추천/플레이북 (래퍼 사용: 키 없으면 폴백)
    st.markdown("---")
    st.subheader("🤖 세그먼트 대표 추천 & 플레이북")

    stats = {
        "count": len(seg_df),
        "avg_churn": round(seg_df["churn_probability"].mean() if len(seg_df) else float("nan"), 4),
        "avg_r": round(seg_df["r_score"].mean() if len(seg_df) else float("nan"), 2),
        "avg_f": round(seg_df["f_score"].mean() if len(seg_df) else float("nan"), 2),
        "avg_m": round(seg_df["m_score"].mean() if len(seg_df) else float("nan"), 2),
    }

    if recommend_for_segment is not None:
        seg_reco = recommend_for_segment(seg, stats)
    else:
        bundle = SEGMENT_BUNDLES.get(seg, [])
        seg_reco = {
            "segment": seg,
            "summary": "LLM 모듈이 없어 정책 번들을 표시합니다.",
            "recommended_bundle": [{"code": c, "reason": "세그먼트 표준 번들"} for c in bundle],
            "playbook": ["표준 오퍼 발송", "A/B 테스트로 캠페인 최적화"],
        }

    st.info(seg_reco.get("summary", "요약 없음"))

    bundle = seg_reco.get("recommended_bundle", [])
    if bundle:
        st.markdown("**추천 번들**")
        for b in bundle:
            code = b.get("code", "")
            name = _PROD_MAP.get(code, {}).get("name", code)
            reason = b.get("reason", "")
            st.markdown(
                f"""
                <div style="border:1px solid #e5e7eb; border-radius:10px; padding:10px; margin-bottom:6px;">
                  <div style="font-weight:700;">{name} <span style="opacity:.6">({code})</span></div>
                  <div style="opacity:.85;">{reason}</div>
                </div>
                """, unsafe_allow_html=True
            )

    acts = seg_reco.get("playbook", [])
    if acts:
        st.markdown("**플레이북**")
        st.markdown("\n".join([f"- {a}" for a in acts]))

    if not os.getenv("OPENAI_API_KEY"):
        st.caption("※ LLM 키가 없어 정책 기반 폴백으로 동작 중입니다. (.env: OPENAI_API_KEY)")
else:
    st.info("상단의 각 세그먼트 카드에서 **사용자 보기** 버튼을 눌러 목록을 확인하세요.")
