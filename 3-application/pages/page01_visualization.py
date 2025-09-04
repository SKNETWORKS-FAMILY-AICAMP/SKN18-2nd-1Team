import os
import numpy as np
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from pathlib import Path
from pages.app_bootstrap import hide_builtin_nav, render_sidebar # 필수 
hide_builtin_nav()
render_sidebar()

st.set_page_config(page_title="사용자 이탈율 확인", layout="wide")
st.title("📊 사용자 이탈율 확인")

# 현재 파일 기준으로 assets 폴더 경로 생성
BASE_DIR = Path(__file__).resolve().parent  # pages 폴더
IMG_DIR = BASE_DIR.parent / "assets" / "img" / "img_list"

st.markdown("""
    <style>
    .my_button_container .stButton > button {
        width: 150px; /* 원하는 너비 설정 */
        height: 100px; /* 원하는 높이 설정 */
        font-size: 20px; /* 원하는 글자 크기 설정 */
    }
    </style>
    """, unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="my_button_container">', unsafe_allow_html=True)

# 탭 생성
tab1, tab2 = st.tabs(["1. EDA", "2. Modeling"])

with tab1:
    st.header("EDA 과정")
    st.write("아래 세그먼트 버튼을 눌러 확인하세요.")

    # 세그먼트 버튼 5개
    segment = st.radio(
        "세그먼트 선택",
        ["show 히스토그램", 
        "show box plot(이상치)", 
        "show sharp", 
        "show 혼동행렬", 
        "show 그래프"],
        horizontal=True,
        format_func=lambda x: x.replace(" ", "<br>")
    )

    # 세그먼트별 이미지 출력
    col1, col2, col3, col4, col5, col6, col7, col8, col9, col10 = st.columns(10)

    segment = None
    with col1:
        if st.button("show 히스토그램"):
            st.image(IMG_DIR / "CardType.png", caption="show 히스토그램 - 그래프1")
    with col2:
            st.image(IMG_DIR / "Complain.png", caption="show 히스토그램 - 그래프1")

    with col3:
        if st.button("show box plot(이상치)"):
            st.image(IMG_DIR / "CardType.png", caption="show box plot(이상치) - 그래프1")
    with col4:
            st.image(IMG_DIR / "Complain.png", caption="show box plot(이상치) - 그래프2")

    with col5:
        if st.button("show sharp"):
            st.image(IMG_DIR / "CardType.png", caption="show sharp - 그래프1")
    with col6:
            st.image(IMG_DIR / "Complain.png", caption="show sharp - 그래프2")

    with col7:
        if st.button("show 혼동행렬"):
            st.image(IMG_DIR / "CardType.png", caption="show 혼동행렬 - 그래프1")
    with col8:
            st.image(IMG_DIR / "Complain.png", caption="show 혼동행렬 - 그래프2")

    with col1:
        if st.button("show 그래프"):
            st.image(IMG_DIR / "CardType.png", caption="show 그래프 - 그래프1")
    with col2:
            st.image(IMG_DIR / "Complain.png", caption="show 그래프 - 그래프2")


with tab2:
    st.header("모델링 과정")
    st.write("여기에 모델링 관련 내용을 추가하세요.")
