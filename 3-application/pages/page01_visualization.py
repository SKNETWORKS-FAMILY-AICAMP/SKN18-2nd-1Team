import os
import sys
import numpy as np
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from pathlib import Path
from pages.app_bootstrap import render_sidebar  # 필수
from sklearn.metrics import classification_report
import plotly.express as px
import plotly.graph_objects as go

# ─────────────────────────────────────────────────────────────
# 기본 설정
# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="사용자 이탈율 확인", layout="wide")
render_sidebar()
st.title("📊 ML 시각화")

BASE_DIR = Path(__file__).resolve().parent         # pages/
APP_DIR  = BASE_DIR.parent                         # 3-application/
# IMG_DIR  = APP_DIR / "assets" / "img" / "img_list"
IMG_DIR  = APP_DIR / "assets" / "img" / "eda"

# ─────────────────────────────────────────────────────────────
# 공통 스타일
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
:root{
  --bg:#0b0f15;
  --card:#0f1723;
  --glass1: linear-gradient(135deg, rgba(36,64,92,.55) 0%, rgba(16,31,46,.55) 100%);
  --glass2: linear-gradient(135deg, rgba(39,119,197,.18) 0%, rgba(27,50,74,.18) 100%);
  --accent:#3f82ef;
  --accent-2:#39d0ff;
  --text-strong:#e9edf3;
  --text-soft:#aab3c2;
  --ring: rgba(63,130,239,.45);
}

/* 페이지 배경(다크) */
main, .block-container{ background: var(--bg); }

/* ── Hero 카드(유리/그라데/둥근) ───────────────────────── */
.hero {
  position: relative;
  padding: 28px 28px 22px 28px;
  border-radius: 22px;
  background: var(--glass1);
  border: 1px solid rgba(255,255,255,.08);
  box-shadow:
    0 10px 30px rgba(0,0,0,.35),
    inset 0 1px 0 rgba(255,255,255,.08);
  overflow: hidden;
}
.hero:before{ /* 은은한 그라데 오라 */
  content:"";
  position:absolute; inset:-20%;
  background: radial-gradient(1200px 600px at -10% -10%, rgba(57,208,255,.15), transparent 55%),
              radial-gradient(900px 500px at 110% 0%, rgba(63,130,239,.18), transparent 60%);
  pointer-events:none;
}
.hero .title{
  font-size: 40px; line-height: 1.1;
  font-weight: 900; letter-spacing: -0.5px;
  color: var(--text-strong);
  text-shadow: 0 2px 16px rgba(0,0,0,.35);
  margin: 2px 0 14px;
}
.hero .subtitle{
  font-size: 18px; color: var(--text-soft); margin-left: 8px;
}

/* 라벨 배지(반투명 pill) */
.badges{ display:flex; gap:12px; margin-top:10px; flex-wrap:wrap; }
.badge{
  display:inline-flex; align-items:center; gap:8px;
  padding: 8px 14px;
  border-radius: 999px;
  background: var(--glass2);
  border: 1px solid rgba(255,255,255,.12);
  color: var(--text-strong);
  font-weight: 700; letter-spacing:.2px;
  box-shadow: 0 6px 16px rgba(0,0,0,.25), inset 0 1px 0 rgba(255,255,255,.06);
}

/* 섹션 제목 라인 */
.section-title{
  font-size: 20px; font-weight: 800; color: var(--text-strong);
  margin: 18px 0 12px;
  border-left: 4px solid var(--accent);
  padding-left: 10px;
}

/* 이미지 카드(살짝 유리 느낌) */
.img-card{
  background: linear-gradient(180deg, rgba(20,33,49,.55), rgba(12,20,32,.55));
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 14px; padding: 10px; margin-bottom: 14px;
  box-shadow: 0 8px 24px rgba(0,0,0,.3);
}

/* 세그먼트 버튼(시스템 느낌, 선택 상태 지원) */
div.stButton > button {
  height: 72px; width: 100%;
  font-size: 17px; font-weight: 800;
  color: var(--text-strong);
  border-radius: 12px;
  background: linear-gradient(180deg, #1a2333, #121926);
  border: 1px solid rgba(255,255,255,.08);
  box-shadow: 0 8px 22px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.06);
  transition: transform .05s ease, box-shadow .2s ease, border-color .2s ease;
}
div.stButton > button:hover{
  border-color: var(--ring);
  box-shadow: 0 12px 28px rgba(0,0,0,.45), 0 0 0 3px var(--ring);
}
div.stButton > button:active{ transform: translateY(1px) scale(.997); }

/* 선택된 버튼 하이라이트 (컨테이너에 .selected 붙여서 사용) */
.stb-selected > button{
  background: linear-gradient(180deg, rgba(63,130,239,.95), rgba(35,82,201,.95)) !important;
  color:#fff !important;
  border: 1px solid rgba(63,130,239,.9) !important;
  box-shadow: 0 16px 40px rgba(63,130,239,.35), inset 0 1px 0 rgba(255,255,255,.18) !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# 탭
# ─────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["1. EDA", "2. Modeling"])

# ======================================================================
# 1) EDA 탭
# ======================================================================
with tab1:
    st.header("EDA 과정")
    st.write("아래 세그먼트 버튼을 눌러 확인하세요.")

    segment_to_dir = {
        "히스토그램": "Histogram",
        "box plot(이상치)": "Outlier",
        "shap": "Shap",
        "혼동행렬": "Confusion_matrix",
        # "그래프": "Graph",
    }
    labels = list(segment_to_dir.keys())

    if "selected_segment_eda" not in st.session_state:
        st.session_state["selected_segment_eda"] = None

    st.markdown("""
        <style>
        .my_button_container .stButton > button {
            width: 100% !important;
            height: 100px !important;
            font-size: 20px !important;
            font-weight: bold !important;
            border-radius: 10px !important;
            border: 1px solid #555 !important;
            background: #222 !important;
            color: #fff !important;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        # st.markdown('<div class="my_button_container">', unsafe_allow_html=True)
        # st.markdown('<div class="seg-row">', unsafe_allow_html=True)
        # cols = st.columns(5)
        # for i, label in enumerate(labels):
        #     if cols[i].button(label, key=f"btn_{i}"):
        #         st.session_state["selected_segment_eda"] = label
        # st.markdown("</div>", unsafe_allow_html=True)
        cols = st.columns(4, gap="small")  # 4등분
        for i, (col, label) in enumerate(zip(cols, labels)):
            if col.button(label, key=f"btn_{i}", use_container_width=True):
                st.session_state["selected_segment_eda"] = label

        selected = st.session_state["selected_segment_eda"]
        if selected is not None:
            subdir = segment_to_dir[selected]
            target_dir = IMG_DIR / subdir

            st.subheader(f"{selected} ({subdir})")

            if not target_dir.exists():
                st.warning(f"폴더가 없습니다: {target_dir}")
            else:
                exts = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
                image_paths = sorted([p for p in target_dir.glob("**/*") if p.suffix.lower() in exts])
                if not image_paths:
                    st.info(f"표시할 이미지가 없습니다: {target_dir}")
                else:
                    col_a, col_b = st.columns(2)
                    for idx, img_path in enumerate(image_paths):
                        (col_a if idx % 2 == 0 else col_b).image(img_path, width="stretch")

# ======================================================================
# 2) Modeling 탭
# ======================================================================
with tab2:
    st.header("이탈고객 예측 - 모델링 과정")

    # ------------------------------------------------------------
    # 경로/환경, 모듈
    # ------------------------------------------------------------
    MODELS_DIR = APP_DIR / "models"
    ASSETS_DIR = APP_DIR / "assets" / "data"
    CSV_FALLBACK = ASSETS_DIR / "churn_scores.csv"   # full_scoring.py 출력

    # full_scoring.py 와 동일 기본값(환경변수로 오버라이드)
    DB_USER  = os.getenv("DB_USER",  "root")
    DB_PASS  = os.getenv("DB_PASS",  "root1234")
    DB_HOST  = os.getenv("DB_HOST",  "127.0.0.1")
    DB_PORT  = int(os.getenv("DB_PORT",  "3306"))
    DB_NAME  = os.getenv("DB_NAME",  "sknproject2")
    DB_TABLE = os.getenv("DB_TABLE", "stg_churn_score")

    # utils.process (full_scoring 과 동일 파이프라인)
    sys.path.insert(0, str(APP_DIR))
    try:
        from utils.process import load_csv_from_data, engineer_features
    except Exception as e:
        engineer_features = None
        load_csv_from_data = None
        st.warning(f"utils.process 로드 실패: {e}")

    # 학습 때 사용한 피처 목록(순서 중요) — full_scoring.py와 동일
    RECOMMENDED_COLS = [
        "Geography", "Gender", "Age", "Balance", "NumOfProducts", "IsActiveMember",
        "ia_x_card", "geo_x_gender", "agebin_x_salbin", "cardtype_x_ia", "Germany_Flag",
    ]

    # ─────────────────────────────────────────────────────────────
    # Feature Importance 고정 모드 (계산 없이 아래 값으로만 시각화)
    # ─────────────────────────────────────────────────────────────
    USE_FIXED_FI = True  # ← 고정값 사용 여부 스위치
    FIXED_FI = {
        "NumOfProducts": 0.941710,
        "Age": 0.559645,
        "agebin_x_salbin": 0.417479,
        "ia_x_card": 0.376097,
        "Balance": 0.373388,
        "cardtype_x_ia": 0.293891,
        "geo_x_gender": 0.212987,
        "Geography": 0.197032,
        "Gender": 0.115979,
        "IsActiveMember": 0.114176,
        "Germany_Flag": 0.083117,
    }

    # ------------------------------------------------------------
    # 헬퍼
    # ------------------------------------------------------------
    def get_engine():
        try:
            url = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
            eng = create_engine(url, pool_pre_ping=True)
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            return eng
        except Exception as e:
            st.warning(f"DB 연결 실패: {e}")
            return None

    def table_exists(engine, tbl):
        if engine is None:
            return False
        try:
            with engine.connect() as conn:
                q = text("""
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema=:db AND table_name=:tbl
                """)
                r = conn.execute(q, {"db": DB_NAME, "tbl": tbl}).scalar()
                return (r or 0) > 0
        except Exception:
            return False

    def load_scores():
        """우선순위: DB → CSV → None"""
        src = None
        df = None
        eng = get_engine()
        if eng and table_exists(eng, DB_TABLE):
            try:
                df = pd.read_sql(f"SELECT * FROM {DB_TABLE}", eng)
                src = f"DB:{DB_TABLE}"
            except Exception as e:
                st.warning(f"{DB_TABLE} 조회 실패: {e}")

        if df is None and CSV_FALLBACK.exists():
            try:
                df = pd.read_csv(CSV_FALLBACK)
                src = f"CSV:{CSV_FALLBACK.name}"
            except Exception as e:
                st.warning(f"CSV 읽기 실패: {e}")

        return df, src

    def get_latest_model_path():
        if not MODELS_DIR.exists():
            return None
        cands = list(MODELS_DIR.glob("best_model_*.pkl"))
        if not cands:
            return None
        cands.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return cands[0]

    def load_model_pickle(path):
        import pickle
        with open(path, "rb") as f:
            return pickle.load(f)

    # ------------------------------------------------------------
    # 데이터/모델 로드
    # ------------------------------------------------------------
    df_scores, src = load_scores()
    latest_model_path = get_latest_model_path()
    model = None
    if latest_model_path is not None:
        try:
            model = load_model_pickle(latest_model_path)
        except Exception as e:
            st.warning(f"모델 로드 실패({latest_model_path.name}): {e}")

    # 상태
    s1, s2 = st.columns([2, 1])
    with s1:
        st.info(f"스코어 소스: **{src or '없음'}**, 최신 모델: **{latest_model_path.name if latest_model_path else '없음'}**")

    if df_scores is None:
        st.warning("스코어 데이터가 없습니다. 좌측 ‘데이터 도구’에서 **모델 학습/스코어링**을 먼저 실행해 주세요.")
        st.stop()

    # 표준 컬럼명 보정
    cols_low = {c.lower(): c for c in df_scores.columns}
    id_col   = cols_low.get("customer_id")
    prob_col = cols_low.get("churn_probability")
    if id_col is None or prob_col is None:
        st.error("필수 컬럼(customer_id, churn_probability)을 찾지 못했습니다.")
        st.stop()

    df = df_scores.rename(columns={id_col: "customer_id", prob_col: "churn_probability"}).copy()
    df["churn_probability"] = df["churn_probability"].astype(float)

    # Threshold
    thr = st.slider("이탈 분류 임계값(Threshold)", min_value=0.05, max_value=0.95, value=0.50, step=0.01)
    df["Risk"] = (df["churn_probability"] >= thr).astype(int)

    # KPI
    model_name = getattr(getattr(model, "__class__", None), "__name__", "N/A")
    colA, colB, colC, colD = st.columns([1.6, 1, 1, 1])
    with colA:
        st.markdown('<div class="card"><div class="metric-title">최종 선택 모델</div>'
                    f'<div class="metric-value">{model_name}</div></div>', unsafe_allow_html=True)
    with colB:
        st.markdown('<div class="card"><div class="metric-title">예측대상고객수</div>'
                    f'<div class="metric-value">{len(df):,}명</div></div>', unsafe_allow_html=True)
    with colC:
        st.markdown('<div class="card"><div class="metric-title">이탈위험고객</div>'
                    f'<div class="metric-value">{int(df["Risk"].sum()):,}명</div></div>', unsafe_allow_html=True)
    with colD:
        rate = (df["Risk"].mean() * 100) if len(df) else 0
        st.markdown('<div class="card"><div class="metric-title">이탈위험률</div>'
                    f'<div class="metric-value">{rate:.2f}%</div></div>', unsafe_allow_html=True)

    st.markdown('<hr class="hr">', unsafe_allow_html=True)

    # ------------------------------------------------------------
    # 원본 CSV → engineer_features() 재실행 (메타 조인)
    # ------------------------------------------------------------
    df_meta = None
    if load_csv_from_data and engineer_features:
        try:
            raw = load_csv_from_data()            # Customer-Churn-Records.csv 자동 탐색
            meta = engineer_features(raw).copy()  # 학습 파이프라인 동일

            # CustomerId → customer_id 로 안전히 합치기 (중복 방지)
            if "CustomerId" in raw.columns:
                ids = raw[["CustomerId"]].rename(columns={"CustomerId": "customer_id"})
                meta = pd.concat([ids, meta], axis=1)

            if "customer_id" not in meta.columns and "CustomerId" in meta.columns:
                meta["customer_id"] = meta["CustomerId"]

            if "customer_id" in meta.columns:
                df_meta = pd.merge(df, meta, on="customer_id", how="left")
        except Exception as e:
            st.warning(f"메타 생성 실패(원본 CSV/피처엔지니어링): {e}")
            df_meta = None

    # ===================== 1행: Feature 중요도(좌) + 이탈 위험 고객 리스트(우) =====================
    row1_left, row1_right = st.columns([1.0, 2.0])

    # ── 좌: Feature Importance (배경 숨김 → ghost)
    with row1_left:
        st.markdown('<div class="section-title">모델 Feature 중요도</div>', unsafe_allow_html=True)
        st.markdown('<div class="card ghost">', unsafe_allow_html=True)

        if USE_FIXED_FI:
            # 고정 값으로만 표시
            fi = (
                pd.DataFrame({"Feature": list(FIXED_FI.keys()),
                              "Importance": list(FIXED_FI.values())})
                .sort_values("Importance")
            )
            fig_fi = px.bar(fi, x="Importance", y="Feature", orientation="h", height=420)
            fig_fi.update_layout(margin=dict(l=8, r=8, t=6, b=6), showlegend=False)
            st.plotly_chart(fig_fi, use_container_width=True)
        else:
            # 기존 계산 경로(백업)
            fi_ok = False
            if model is not None and df_meta is not None:
                try:
                    from catboost import Pool
                    feature_cols = [c for c in RECOMMENDED_COLS if c in df_meta.columns]
                    if feature_cols:
                        X_tmp = df_meta[feature_cols].copy()
                        cat_cols = X_tmp.select_dtypes(include=["object", "category"]).columns.tolist()
                        for c in cat_cols:
                            X_tmp[c] = X_tmp[c].astype(str).fillna("NA")
                        for c in X_tmp.columns.difference(cat_cols):
                            X_tmp[c] = pd.to_numeric(cast := X_tmp[c], errors="coerce").fillna(0)
                        pool = Pool(X_tmp, cat_features=[X_tmp.columns.get_loc(c) for c in cat_cols])
                        importances = model.get_feature_importance(pool)
                        if len(importances) == len(feature_cols):
                            fi = (pd.DataFrame({"Feature": feature_cols, "Importance": importances})
                                  .sort_values("Importance").tail(20))
                            fig_fi = px.bar(fi, x="Importance", y="Feature", orientation="h", height=420)
                            fig_fi.update_layout(margin=dict(l=8, r=8, t=6, b=6), showlegend=False)
                            st.plotly_chart(fig_fi, use_container_width=True)
                            fi_ok = True
                except Exception:
                    fi_ok = False

            if not fi_ok:
                st.markdown(
                    '<div class="placeholder"><span class="em">💡</span>'
                    '<div>Feature Importance를 표시할 수 없습니다.<br>'
                    '<span class="small">모델과 특성 컬럼이 일치하지 않거나 저장 시 정보가 포함되지 않았습니다.</span></div></div>',
                    unsafe_allow_html=True
                )
        st.markdown('</div>', unsafe_allow_html=True)

    # ── 우: 이탈 위험 고객 리스트 (배경 숨김 → ghost)
    with row1_right:
        st.markdown('<div class="section-title">이탈 위험 고객 리스트 50</div>', unsafe_allow_html=True)
        st.markdown('<div class="card ghost">', unsafe_allow_html=True)

        base_for_table = df_meta if df_meta is not None else df
        top = base_for_table.sort_values("churn_probability", ascending=False).head(50).copy()
        top["이탈확률(%)"] = (top["churn_probability"] * 100).round(2)

        show_cols = ["customer_id", "이탈확률(%)"] + [
            c for c in ["Geography", "Age", "Gender", "CreditScore", "NumOfProducts", "Balance", "Point"]
            if c in top.columns
        ]

        fmt = {"이탈확률(%)": "{:.2f}"}
        for c in ["Age", "CreditScore", "NumOfProducts", "Balance", "Point"]:
            if c in top.columns:
                fmt[c] = "{:,.0f}"

        try:
            st.dataframe(top[show_cols].style.format(fmt), height=420, width="stretch")
        except Exception:
            st.dataframe(top[show_cols], height=420, width="stretch")

        st.markdown('</div>', unsafe_allow_html=True)

    # ===================== 2행: 이탈위험고객 특성(상단) + 신용등급(하단 전폭) =====================
    st.markdown('<div class="section-title">이탈위험고객 특성</div>', unsafe_allow_html=True)

    # 2행 상단 3카드 (배경 숨김 → ghost)
    r2c1, r2c2, r2c3 = st.columns([1, 1.1, 1])
    df_risk = (df_meta if df_meta is not None else df).copy()
    df_risk = df_risk[df_risk["Risk"] == 1]

    # 성별
    with r2c1:
        st.markdown('<div class="card ghost">', unsafe_allow_html=True)
        st.caption("성별")
        gcol = next((c for c in df_risk.columns if c.lower() in ["gender", "sex"]), None)
        if gcol and not df_risk.empty:
            g = df_risk[gcol].astype(str).value_counts().rename_axis("Gender").reset_index(name="Count")
            fig = px.pie(g, names="Gender", values="Count", height=240, hole=.45)
            fig.update_layout(margin=dict(l=6, r=6, t=6, b=6), showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown('<div class="placeholder">🙈 <span class="small">표시할 성별 컬럼이 없습니다.</span></div>',
                        unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 국가/지역
    with r2c2:
        st.markdown('<div class="card ghost">', unsafe_allow_html=True)
        st.caption("국가/지역")
        geocol = next((c for c in df_risk.columns if c.lower() in ["geography", "country", "region"]), None)
        if geocol and not df_risk.empty:
            geo = df_risk[geocol].astype(str).value_counts().rename_axis("Country").reset_index(name="Count")
            latlon = {"Germany":(51.16,10.45), "France":(46.23,2.21), "Spain":(40.46,-3.75),
                      "독일":(51.16,10.45), "프랑스":(46.23,2.21), "스페인":(40.46,-3.75)}
            geo["lat"] = geo["Country"].map(lambda x: latlon.get(x, (0,0))[0])
            geo["lon"] = geo["Country"].map(lambda x: latlon.get(x, (0,0))[1])
            fig = px.scatter_geo(geo, lat="lat", lon="lon", size="Count",
                                 hover_name="Country", projection="natural earth", height=240)
            fig.update_layout(margin=dict(l=6, r=6, t=6, b=6), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown('<div class="placeholder">🗺️ <span class="small">표시할 국가/지역 컬럼이 없습니다.</span></div>',
                        unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 보유상품수
    with r2c3:
        st.markdown('<div class="card ghost">', unsafe_allow_html=True)
        st.caption("보유상품수")
        pcol = next((c for c in df_risk.columns if c.lower() in ["numofproducts", "products", "product_count"]), None)
        if pcol and not df_risk.empty:
            prod = df_risk[pcol].astype(str).value_counts().sort_index().reset_index()
            prod.columns = ["Products", "Count"]
            fig = px.bar(prod, x="Products", y="Count", height=240,
                         color="Count", color_continuous_scale="Reds")
            fig.update_layout(coloraxis_showscale=False, margin=dict(l=8, r=8, t=8, b=8))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown('<div class="placeholder">📦 <span class="small">표시할 보유상품수 컬럼이 없습니다.</span></div>',
                        unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 2행 하단 전폭: 신용등급 (배경 숨김 → ghost)
    st.markdown('<div class="card ghost grid-gap">', unsafe_allow_html=True)
    st.caption("신용등급 분포")
    cs = next((c for c in df_risk.columns if c.lower() in ["creditscore", "credit_score"]), None)
    if cs and not df_risk.empty:
        def band(x):
            try: x = float(x)
            except: return "Unknown"
            if x>=800: return "Excellent"
            if x>=740: return "Good"
            if x>=670: return "Fair"
            if x>=580: return "Poor"
            return "Very Poor"
        cred = df_risk[cs].apply(band).value_counts().reindex(
            ["Excellent","Good","Fair","Poor","Very Poor"]
        ).fillna(0).reset_index()
        cred.columns = ["Grade","Count"]
        fig = px.bar(cred, x="Grade", y="Count", height=260,
                     color="Count", color_continuous_scale="Reds")
        fig.update_layout(coloraxis_showscale=False, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown('<div class="placeholder">💳 <span class="small">표시할 신용점수 컬럼이 없습니다.</span></div>',
                    unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ------------------------------------------------------------
    # 모델 성능(정답 라벨 있을 때만) — 배경 숨김(ghost)
    # ------------------------------------------------------------
    st.markdown('<div class="section-title">모델 성능</div>', unsafe_allow_html=True)
    b1, b2, b3 = st.columns([1.0, 1.2, 1.3])

    from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

    # 라벨 컬럼 찾기
    y_col = None
    if df_meta is not None:
        for k in ["Exited", "label", "y_true", "target", "churned"]:
            if k in df_meta.columns:
                y_col = k
                break

    # 정확도 계산 (있을 때만)
    acc_str = "N/A"
    if y_col:
        df_eval = pd.merge(df, df_meta[["customer_id", y_col]], on="customer_id", how="inner")
        y_true = df_eval[y_col].astype(int)
        y_pred = (df_eval["churn_probability"] >= thr).astype(int)
        acc = accuracy_score(y_true, y_pred)
        acc_str = f"{acc*100:.2f}%"

    # b1: 모델 정보 표
    with b1:
        st.markdown('<div class="card ghost">', unsafe_allow_html=True)
        st.caption("모델 정보")
        info = pd.DataFrame({
            "Model":     [model_name],
            "Path":      [latest_model_path.name if latest_model_path else "N/A"],
            "Accuracy":  [acc_str],
        })
        st.dataframe(info, height=160, width="stretch")
        st.markdown('</div>', unsafe_allow_html=True)

    # b2/b3: 분류 리포트, 혼동행렬
    if y_col:
        target_names = ["정상 고객(0)", "이탈 고객(1)"]
        rep = classification_report(
            y_true, y_pred,
            target_names=target_names,
            output_dict=True,
            zero_division=0
        )
        order = target_names + ["macro avg", "weighted avg"]
        report_df = (
            pd.DataFrame(rep).T
            .reindex(order)
            .reset_index(drop=False)
            .rename(columns={"index": "Class"})
        )

        with b2:
            st.markdown('<div class="card ghost">', unsafe_allow_html=True)
            st.caption("분류 리포트")
            st.dataframe(report_df, height=240, width="stretch")
            st.markdown('</div>', unsafe_allow_html=True)

        cm = confusion_matrix(y_true, y_pred)
        cm_pct = (cm / cm.sum()) * 100
        z = cm_pct.round(2)
        with b3:
            st.markdown('<div class="card ghost">', unsafe_allow_html=True)
            st.caption("혼동행렬(%)")
            fig_cm = go.Figure(data=go.Heatmap(
                z=z, x=["Pred=1", "Pred=0"], y=["True=1", "True=0"],
                colorscale="Blues", text=z.astype(str) + "%", texttemplate="%{text}",
                showscale=False, hoverinfo="skip"
            ))
            fig_cm.update_layout(height=240, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_cm, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        with b2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.caption("정답 라벨이 없어 분류 리포트를 표시할 수 없습니다.")
            st.markdown('</div>', unsafe_allow_html=True)
        with b3:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.caption("정답 라벨이 없어 혼동행렬을 표시할 수 없습니다.")
            st.markdown('</div>', unsafe_allow_html=True)
