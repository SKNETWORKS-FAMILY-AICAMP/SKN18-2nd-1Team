# streamlit_app.py
import streamlit as st
from pathlib import Path

def render_na_page():
    # -------------------------
    # 0) 페이지 설정
    # -------------------------
    st.set_page_config(page_title="Bank Churn — EDA Summary", layout="wide")

    # (선택) 다크 톤 살짝 정리
    st.markdown("""
    <style>
    :root{ --border: rgba(255,255,255,.12); --muted:#aab3c2; }
    .block-container{ padding-top: 1.2rem; }
    .section{ border:1px solid var(--border); border-radius:14px; padding:16px; background: rgba(20,28,36,.35); margin-bottom:14px; }
    .section h3{ margin:0 0 12px 0; }
    .caption{ color: var(--muted); font-size: 13px; }
    </style>
    """, unsafe_allow_html=True)

    # -------------------------
    # 1) 이미지 주소(여기만 수정)
    # -------------------------
    APP_ROOT = Path(__file__).resolve().parents[1]
    IMG_ROOT = APP_ROOT / "assets" / "img" / "eda" / "na"

    # 번호순으로 URL 생성
    IMG_INFO_URL     = f"{IMG_ROOT}/1.png"   # df.info()
    IMG_TARGET_URL   = f"{IMG_ROOT}/2.png"   # target ratio
    IMG_DESCRIBE_URL = f"{IMG_ROOT}/3-2.png"   # describe
    IMG_FEATURE_URL  = f"{IMG_ROOT}/4.png"   # feature notes
    IMG_HEAD_URL     = f"{IMG_ROOT}/5.png"   # head + shape

    # 참고: 제공된 예시 파일명을 쓰실 거면 CDN/서버에 업로드 후 링크로 교체
    #  - 1) df.info()      -> (예) 1-info.png
    #  - 2) Target ratio   -> (예) 2-target.png
    #  - 3) describe       -> (예) 3-describe.png
    #  - 4) feature 설명   -> (예) 4-feature.png
    #  - 5) head/shape     -> (예) 5-head-shape.png

    # -------------------------
    # 2) 헤더
    # -------------------------
    # st.title("📊 Bank Churn — EDA Summary")
    # st.write("하드코딩된 요약 페이지이며, 그래프/표는 **이미지 URL**로 삽입합니다.")

    # -------------------------
    # 3) 데이터 개요 (df.info)
    # -------------------------
    with st.container():
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown("### 1) Dataset Info (df.info)")
        st.image(IMG_INFO_URL, caption="DataFrame Info", width=600)
        st.markdown('<div class="caption">열 이름, null 여부, dtype 등 기본 구조</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # -------------------------
    # 4) 타깃 분포
    # -------------------------
    left, right = st.columns([6,4], gap="large")
    with left:
        st.markdown('<div class="section">')
        st.markdown("### 2) Target Class Ratio (%)")
        st.image(IMG_TARGET_URL, width=400)
        st.markdown('<div class="caption">Exited 0/1 비율 (예: 80% / 20%)</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown("### Quick Facts (Hard-coded)")
        st.markdown("""
    - Rows: **10,000**  
    - Columns: **18**  
    - Target: **Exited** (0=Stayed, 1=Exited)  
    - Missing values: **None** (예시)  
    - Numeric: CreditScore, Age, Tenure, Balance, NumOfProducts, EstimatedSalary, SatisfactionScore, Point Earned  
    - Categorical: Geography, Gender, HasCrCard, IsActiveMember, Complain, Card Type
        """)
        st.markdown('</div>', unsafe_allow_html=True)

    # -------------------------
    # 5) 수치 요약 (describe)
    # -------------------------
    with st.container():
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown("### 3) Numeric Summary (df.describe)")
        st.image(IMG_DESCRIBE_URL, caption="Summary Statistics", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # -------------------------
    # 6) 변수 설명 이미지 (하드코딩 설명)
    # -------------------------
    with st.container():
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown("### 4) Feature Notes")
        st.image(IMG_FEATURE_URL, width=400)
        st.markdown("""
    **요약**  
    - *Not Important*: RowNumber, CustomerId, Surname  
    - *Numeric*: CreditScore, Age, Tenure, Balance, NumOfProducts, EstimatedSalary, SatisfactionScore, Points Earned  
    - *Categorical*: Geography, Gender, HasCrCard, IsActiveMember, Complain, Card Type
        """)
        st.markdown('</div>', unsafe_allow_html=True)

    # -------------------------
    # 7) 샘플 레코드 & shape
    # -------------------------
    with st.container():
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown("### 5) Head & Shape")
        st.image(IMG_HEAD_URL, width=400)
        st.markdown('</div>', unsafe_allow_html=True)

