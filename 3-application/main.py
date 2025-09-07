# main.py
import os
import time
import pandas as pd
import streamlit as st
import pymysql
from pages.app_bootstrap import render_sidebar  # 필수

# ---------------------------
# 기본 설정
# ---------------------------
st.set_page_config(
    page_title="BCMS | Bank Customer Management System",
    page_icon="🏦",
    layout="wide",
)
render_sidebar()


# ---------------------------
# DB helpers
# ---------------------------
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "root1234")
DB_NAME = os.getenv("DB_NAME", "sknproject2")

def db_connect():
    return pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS,
                           database=DB_NAME, charset="utf8mb4", autocommit=True)

def try_scalar(sql, default=None):
    try:
        with db_connect() as conn, conn.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()
            return (row[0] if row else default)
    except Exception:
        return default

def try_frame(sql, default_cols=None, limit=10):
    try:
        with db_connect() as conn:
            df = pd.read_sql(sql, conn)
            return df.head(limit)
    except Exception:
        return pd.DataFrame(columns=default_cols or [])

# ---------------------------
# 헤더
# ---------------------------
st.markdown(
    """
    <div class="hero">
      <div class="title">
        🏦 BCMS
        <span style="font-weight:600; font-size:.58em; padding-left:6px; opacity:.9;">Bank Customer Management System</span>
      </div>
      <div class="kicker">
        <span class="badge"><span class="dot"></span> 🌐 SK Networks</span>
        <span class="badge">Prod Console</span>
        <span class="badge">v1.0</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------------------
# 핵심 KPI (더 직관적인 지표)
# ---------------------------

customers = try_scalar("SELECT COUNT(*) FROM bank_customer", 0)
vip_count = try_scalar("SELECT COUNT(*) FROM rfm_result_once WHERE segment_code='VIP'", 0)
highrisk_count = try_scalar("SELECT COUNT(*) FROM stg_churn_score WHERE churn_probability >= 0.6", 0)
avg_churn = try_scalar("SELECT AVG(churn_probability) FROM stg_churn_score", 0.0)
# --- KPI 섹션 시작 (마커) ---
st.markdown('<div class="kpi-anchor"></div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        f"""
        <div class="kpi-card" title="은행 고객 테이블의 전체 행 수">
          <div><span class="kpi-icon">👥</span><span class="kpi-title">전체 고객 수</span></div>
          <div class="kpi-stat">{customers:,}</div>
          <div class="kpi-sub"><span>테이블</span><span>bank_customer</span></div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c2:
    st.markdown(
        f"""
        <div class="kpi-card" title="RFM 세그먼트 중 VIP(최우수) 고객 수">
          <div><span class="kpi-icon">⭐</span><span class="kpi-title">VIP 고객 수</span></div>
          <div class="kpi-stat">{vip_count:,}</div>
          <div class="kpi-sub"><span>세그먼트</span><span>VIP (최우수)</span></div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c3:
    st.markdown(
        f"""
        <div class="kpi-card" title="예측 이탈 확률 0.6 이상 고객 수">
          <div><span class="kpi-icon">⚠️</span><span class="kpi-title">고위험 고객 수 (Churn ≥ 0.6)</span></div>
          <div class="kpi-stat" style="color:#ea580c;">{highrisk_count:,}</div>
          <div class="kpi-sub"><span>모델</span><span>stg_churn_score</span></div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c4:
    st.markdown(
        f"""
        <div class="kpi-card" title="전체 고객 평균 이탈 확률">
          <div><span class="kpi-icon">📈</span><span class="kpi-title">평균 Churn</span></div>
          <div class="kpi-stat">{(avg_churn or 0) * 100:.2f}%</div>
          <div class="kpi-sub"><span>갱신</span><span>{time.strftime('%Y-%m-%d %H:%M:%S')}</span></div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown('</div>', unsafe_allow_html=True)   # KPI 패널 닫기
st.markdown("<div style='height:36px'></div>", unsafe_allow_html=True)  # ✅ 추가 여백
# --- KPI 섹션 끝 ---

# ---------------------------
# 빠른 실행 / 이동
# ---------------------------
st.subheader("빠른 이동")
st.markdown('<div class="quick-anchor"></div>', unsafe_allow_html=True)

q1, q2, q3 = st.columns(3)

with q1:
    st.markdown(
        """
        <div class="quick-card">
          <div class="quick-icon">📉</div>
          <div class="quick-title">고객 이탈율</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.page_link("pages/user_list.py", label="이동", icon="➡️")

with q2:
    st.markdown(
        """
        <div class="quick-card">
          <div class="quick-icon">👥</div>
          <div class="quick-title">고객 그룹 (RFM)</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.page_link("pages/customer_rfm.py", label="이동", icon="➡️")

with q3:
    st.markdown(
        """
        <div class="quick-card">
          <div class="quick-icon">🧰</div>
          <div class="quick-title">데이터 도구</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.page_link("pages/data_tool.py", label="이동", icon="➡️")

st.markdown('</div>', unsafe_allow_html=True)   # KPI 패널 닫기
st.markdown("<div style='height:36px'></div>", unsafe_allow_html=True)  # ✅ 추가 여백

# ---------------------------
# 위험 고객 프리뷰
# ---------------------------
st.subheader("🔥 이탈 고위험 고객 Top 20")

st.markdown('<div class="card table-card">', unsafe_allow_html=True)
# st.markdown('<div class="hd">🔥 위험 고객 Top 10 (Churn 내림차순)</div>', unsafe_allow_html=True)
# preview_df = try_frame("""
#     SELECT r.customer_id, r.surname, r.segment_code,
#             COALESCE(s.churn_probability, 0) AS churn_probability,
#             r.m_score, r.f_score, r.r_score
#     FROM rfm_result_once r
#     LEFT JOIN stg_churn_score s ON s.customer_id = r.customer_id
#     ORDER BY churn_probability DESC
#     LIMIT 10
# """, default_cols=["customer_id","surname","segment_code","churn_probability","m_score","f_score","r_score"], limit=10)
# st.dataframe(preview_df, use_container_width=True, height=340)

preview_df = try_frame("""
    SELECT r.customer_id, r.surname, r.segment_code,
            CONCAT(ROUND(COALESCE(s.churn_probability, 0) * 100, 2), '%') AS churn_probability
    FROM rfm_result_once r
    LEFT JOIN stg_churn_score s ON s.customer_id = r.customer_id
    ORDER BY churn_probability DESC
    LIMIT 20
""", default_cols=["customer_id","surname","segment_code","churn_probability"], limit=20)

# 2) RFM 그룹 한글 매핑
rfm_map = {
    "VIP": "핵심 고객(VIP)",
    "LOYAL": "충성 고객(LOYAL)",
    "AT_RISK": "위험 고객(RISK)",
    "LOW": "저활성 고객(LOW)",
}
preview_df["segment_code"] = preview_df["segment_code"].map(rfm_map).fillna(preview_df["segment_code"])

# 컬럼명 한글로 변경
preview_df = preview_df.rename(columns={
    "customer_id": "고객ID",
    "surname": "이름(성)",
    "segment_code": "RFM 그룹",
    "churn_probability": "이탈확률",
})

# 인덱스 조정 
preview_df.index = range(1, len(preview_df) + 1)

st.dataframe(preview_df, use_container_width=True, height=500)
st.markdown('</div>', unsafe_allow_html=True)

st.write("---")
st.caption("© 2025 BCMS · SK Networks Family AI Camp 18기 - 2nd - 1Team")
