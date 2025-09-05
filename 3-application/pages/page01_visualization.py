import os
import numpy as np
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from pathlib import Path
from pages.app_bootstrap import hide_builtin_nav, render_sidebar # 필수
import plotly.express as px ## 추가
import plotly.graph_objects as go ## 추가

st.set_page_config(page_title="사용자 이탈율 확인", layout="wide")

hide_builtin_nav()
render_sidebar()

st.title("📊 사용자 이탈율 확인")

# 현재 파일 기준으로 assets 폴더 경로 생성
BASE_DIR = Path(__file__).resolve().parent  # pages 폴더
IMG_DIR = BASE_DIR.parent / "assets" / "img" / "img_list"

st.markdown(
    """
    <style>
      /* 1) 탭 라벨(버전별로 p/span/div/button 등)을 전부 커버 */
    .stTabs [role="tab"]        { padding: 14px 26px !important; height: 64px !important; }
    .stTabs [role="tab"] p,
    .stTabs [role="tab"] span,
    .stTabs [role="tab"] div,
    .stTabs [data-baseweb="tab"] p,
    .stTabs [data-baseweb="tab"] span,
    .stTabs [data-baseweb="tab"] div,
    .stTabs [data-baseweb="tab"] button {
        font-size: 33px !important;
        font-weight: 1000 !important;
        line-height: 1.4 !important;
        margin: 0 !important;
    }
    """,
    unsafe_allow_html=True
    )

# 탭 생성
tab1, tab2 = st.tabs(["1. EDA", "2. Modeling"])

with tab1:
    st.header("EDA 과정")
    st.write("아래 세그먼트 버튼을 눌러 확인하세요.")

    # 버튼 라벨 → 이미지 폴더명 매핑
    segment_to_dir = {
        "히스토그램": "Histogram",
        "box plot(이상치)": "Outlier",
        "shap": "Shap",
        "혼동행렬": "Confusion_matrix",
        "그래프": "Graph",
    }
    labels = list(segment_to_dir.keys())

    # 클릭 상태 보관
    if "selected_segment_eda" not in st.session_state:
        st.session_state["selected_segment_eda"] = None

    st.markdown(
    """
        <style>
    /* 세그먼트 버튼을 꽉 차게 */
    .my_button_container .stButton > button {
        width: 100% !important;      /* 컬럼 너비에 꽉 채움 */
        height: 100px !important;    /* 버튼 높이 (원하는 값) */
        font-size: 20px !important;  /* 글자 크기 */
        font-weight: bold !important;
        border-radius: 10px !important; /* 둥근 모서리 */
        border: 1px solid #555 !important;
        background: #222 !important;
        color: #fff !important;
    }

    /* 선택된 버튼 강조 색상 */
        .stButton.selected > button {
        background-color: #FF4B4B !important;  /* 원하는 색상 */
        border-color: #FF0000 !important;
        border: 2px solid #FF0000 !important;
    }
    </style>
        """,
    unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="my_button_container">', unsafe_allow_html=True)

    # 버튼 5개를 한 줄에 배치
    st.markdown('<div class="seg-row">', unsafe_allow_html=True)
    cols = st.columns(5)
    for i, label in enumerate(labels):
        if cols[i].button(label, key=f"btn_{i}", use_container_width=True):
            st.session_state["selected_segment_eda"] = label

    st.markdown("</div>", unsafe_allow_html=True)  # 버튼 컨테이너 닫기

    # 클릭된 버튼의 폴더 내 모든 이미지 렌더링
    selected = st.session_state["selected_segment_eda"]
    if selected is not None:
        subdir = segment_to_dir[selected]
        target_dir = IMG_DIR / subdir

        st.markdown("---")
        st.subheader(f"{selected} ({subdir})")

        if not target_dir.exists():
            st.warning(f"폴더가 없습니다: {target_dir}")
        else:
            # 이미지 파일 모으기
            exts = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
            image_paths = sorted(
                [p for p in target_dir.glob("**/*") if p.suffix.lower() in exts]
            )

            if not image_paths:
                st.info(f"표시할 이미지가 없습니다: {target_dir}")
            else:
                # 2열 그리드로 출력
                col_a, col_b = st.columns(2)
                for idx, img_path in enumerate(image_paths):
                    (col_a if idx % 2 == 0 else col_b).image(
                        img_path, caption=img_path.stem, use_container_width=True
                    )

# --- 탭 2: Modeling ----------------------------------------------------------
with tab2:
    st.header("모델링 과정")
    st.write("여기에 모델링 관련 내용을 추가하세요.")

    st.set_page_config(page_title="OO은행 이탈고객 예측", layout="wide")

    # ---------------------------
    # 스타일 (카드/섹션 타이틀)
    # ---------------------------
    st.markdown("""
    <style>
    .section-title{
    font-size:22px; font-weight:800; margin:8px 0 12px 0;
    }
    .card{
    background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.12);
    padding:14px 16px; border-radius:10px;
    }
    .metric-title{ font-size:14px; opacity:.8; margin-bottom:6px;}
    .metric-value{ font-size:28px; font-weight:800;}
    .small{ font-size:12px; opacity:.8;}
    hr.hr{ border:0; height:1px; background:rgba(255,255,255,0.15); margin:8px 0 18px 0;}
    </style>
    """, unsafe_allow_html=True)

    # ---------------------------
    # (데모) 샘플 데이터 생성
    # -> 실제 데이터로 교체해서 쓰세요
    # ---------------------------
    np.random.seed(42)

    N = 300
    df = pd.DataFrame({
        "CustomerID": np.arange(10000, 10000+N),
        "ChurnProb": np.random.beta(2, 5, size=N),                     # 이탈확률(0~1)
        "Gender": np.random.choice(["남성","여성"], size=N, p=[.45,.55]),
        "Age": np.random.randint(18, 85, size=N),
        "Geography": np.random.choice(["독일","프랑스","스페인"], size=N, p=[.47,.36,.17]),
        "Products": np.random.choice([1,2,3,4], size=N, p=[.65,.22,.10,.03]),
        "CreditScore": np.random.normal(650, 80, size=N).astype(int),
        "Balance": np.random.gamma(2., 5000, size=N).astype(int),
        "Point": np.random.randint(0, 1500, size=N),
        "Tenure": np.random.randint(0, 10, size=N),
        "IsActiveMember": np.random.choice([0,1], size=N, p=[.4,.6]),
        "EstimatedSalary": np.random.normal(50000, 18000, size=N).astype(int)
    })
    # 임계값(예: 0.5)이상 고객을 "이탈위험"으로 분류
    threshold = 0.5
    df["Risk"] = (df["ChurnProb"] >= threshold).astype(int)
    df_risk = df[df["Risk"]==1].copy()

    # (데모) Feature Importance
    fi = pd.DataFrame({
        "Feature": ["Age","Balance","Point","CreditScore","Tenure","NumOfProducts",
                    "Geography","EstimatedSalary","IsActiveMember","Satisfaction_group","Gender"],
        "Importance": [911,439,350,345,239,233,137,130,104,59,53]
    })

    # (데모) 모델 비교/혼동행렬
    model_scores = pd.DataFrame({
        "Model":["LightGBM","RandomForest","XGBoost","SVM"],
        "Accuracy":[0.87,0.85,0.85,0.80]
    })
    report = pd.DataFrame({
        "Class":[0,1],
        "F1-score":[0.92,0.67],
        "Precision":[0.91,0.67],
        "Recall":[0.93,0.64],
        "Support":[2389,611]
    })
    cm = np.array([[2215,174],[219,392]]) # TP, FN / FP, TN (예시)
    cm_pct = (cm / cm.sum())*100

    # ---------------------------
    # 상단 헤더 + KPI 카드
    # ---------------------------
    st.markdown("## OO은행 이탈고객 예측")

    colA, colB, colC, colD = st.columns([1.6,1,1,1])
    with colA:
        st.markdown('<div class="card"><div class="metric-title">최종 선택 모델</div>'
                    f'<div class="metric-value">LightGBM</div></div>', unsafe_allow_html=True)
    with colB:
        st.markdown('<div class="card"><div class="metric-title">예측대상고객수</div>'
                    f'<div class="metric-value">{len(df):,}명</div></div>', unsafe_allow_html=True)
    with colC:
        st.markdown('<div class="card"><div class="metric-title">이탈위험고객</div>'
                    f'<div class="metric-value">{len(df_risk):,}명</div></div>', unsafe_allow_html=True)
    with colD:
        st.markdown('<div class="card"><div class="metric-title">이탈위험률</div>'
                    f'<div class="metric-value">{(len(df_risk)/len(df)*100):.2f}%</div></div>', unsafe_allow_html=True)

    st.markdown('<hr class="hr">', unsafe_allow_html=True)

    # ---------------------------
    # 중단 3열: 좌(Feature Importance) / 중(특성) / 우(리스트)
    # ---------------------------
    left, mid, right = st.columns([1.1,1.3,1.6])

    # 1) Feature Importance (bar)
    with left:
        st.markdown('<div class="section-title">LightGBM 모델 예측 결과</div>', unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.caption("Feature Importance")
        fig_fi = px.bar(fi.sort_values("Importance"),
                        x="Importance", y="Feature", orientation="h",
                        height=400)
        fig_fi.update_layout(margin=dict(l=8,r=8,t=10,b=8))
        st.plotly_chart(fig_fi, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 2) 이탈위험고객 특성(성별/연령/국가/보유상품수/신용등급)
    with mid:
        st.markdown('<div class="section-title">이탈위험고객 특성</div>', unsafe_allow_html=True)
        # 성별
        c1, c2, c3 = st.columns([1,1.2,1])
        with c1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.caption("성별")
            g = df_risk["Gender"].value_counts().rename_axis("Gender").reset_index(name="Count")
            fig_gender = px.pie(g, names="Gender", values="Count", height=220, hole=.35)
            fig_gender.update_layout(margin=dict(l=4,r=4,t=10,b=4))
            st.plotly_chart(fig_gender, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        # 국가(버블 맵: scatter_geo)
        with c2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.caption("국가")
            geo = df_risk["Geography"].value_counts().rename_axis("Country").reset_index(name="Count")
            # 대략적 위경도
            latlon = {"독일":(51.16,10.45), "프랑스":(46.23,2.21), "스페인":(40.46,-3.75)}
            geo["lat"] = geo["Country"].map(lambda x: latlon[x][0])
            geo["lon"] = geo["Country"].map(lambda x: latlon[x][1])
            fig_geo = px.scatter_geo(geo, lat="lat", lon="lon",
                                    size="Count", hover_name="Country",
                                    projection="natural earth", height=220)
            fig_geo.update_layout(margin=dict(l=4,r=4,t=10,b=4))
            st.plotly_chart(fig_geo, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        # 보유상품수 분포(heat 느낌의 bar)
        with c3:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.caption("보유상품수")
            prod = df_risk["Products"].value_counts().sort_index().reset_index()
            prod.columns = ["Products","Count"]
            fig_prod = px.bar(prod, x="Products", y="Count", height=220,
                            color="Count", color_continuous_scale="Reds")
            fig_prod.update_layout(coloraxis_showscale=False, margin=dict(l=6,r=6,t=10,b=6))
            st.plotly_chart(fig_prod, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # 신용등급 (예시: 점수→등급)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.caption("신용등급 분포")
        def band(x):
            if x>=800: return "Excellent"
            if x>=700: return "Good"
            if x>=600: return "Fair"
            if x>=500: return "Poor"
            return "Very Poor"
        cred = df_risk["CreditScore"].apply(band).value_counts().reindex(
            ["Excellent","Good","Fair","Poor","Very Poor"]).fillna(0).reset_index()
        cred.columns = ["Grade","Count"]
        fig_cred = px.bar(cred, x="Grade", y="Count", height=220,
                        color="Count", color_continuous_scale="Reds")
        fig_cred.update_layout(coloraxis_showscale=False, margin=dict(l=6,r=6,t=10,b=6))
        st.plotly_chart(fig_cred, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 3) 이탈 위험 고객 리스트
    with right:
        st.markdown('<div class="section-title">이탈 위험 고객 리스트</div>', unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        # 리스트 예시: 상위 50명
        top = df.sort_values("ChurnProb", ascending=False).head(50).copy()
        top["이탈확률(%)"] = (top["ChurnProb"]*100).round(2)
        view_cols = ["CustomerID","이탈확률(%)","Geography","Age","Gender",
                    "CreditScore","Products","Balance","Point"]
        st.dataframe(top[view_cols], height=360, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ---------------------------
    # 하단: 모델 성능 비교 + 혼동행렬
    # ---------------------------
    st.markdown('<div class="section-title">모델 성능 비교</div>', unsafe_allow_html=True)
    b1, b2, b3 = st.columns([1.0,1.2,1.3])

    with b1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.caption("모델 목록")
        st.dataframe(model_scores, use_container_width=True, height=240)
        st.markdown('</div>', unsafe_allow_html=True)

    with b2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.caption("LightGBM | 최적 모델 선정 과정 (리포트)")
        st.dataframe(report, use_container_width=True, height=240)
        st.markdown('</div>', unsafe_allow_html=True)

    with b3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.caption("LightGBM | 혼동행렬")
        z = cm_pct.round(2)
        fig_cm = go.Figure(data=go.Heatmap(
            z=z,
            x=["Positive","Negative"],
            y=["Positive","Negative"],
            colorscale="Blues",
            text=z.astype(str)+"%",
            texttemplate="%{text}",
            showscale=False,
            hoverinfo="skip",
        ))
        fig_cm.update_layout(height=240, margin=dict(l=10,r=10,t=10,b=10))
        st.plotly_chart(fig_cm, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
