import os
import numpy as np
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from pathlib import Path
from pages.app_bootstrap import hide_builtin_nav, render_sidebar # 필수 

st.set_page_config(page_title="사용자 이탈율 확인", layout="wide")

hide_builtin_nav()
render_sidebar()

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
        white-space: normal; /* 줄바꿈 허용 */
    }
    </style>
    """, 
    unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="my_button_container">', unsafe_allow_html=True)

# 탭 생성
tab1, tab2 = st.tabs(["1. EDA", "2. Modeling"])

with tab1:
    st.header("EDA 과정")
    st.write("아래 세그먼트 버튼을 눌러 확인하세요.")

    # 세그먼트 정의: 버튼 라벨과 이미지 파일 쌍
    segments = [
        ("show 히스토그램", ("CardType.png", "Complain.png")),
        ("show box plot(이상치)", ("CardType.png", "Complain.png")),
        ("show sharp", ("CardType.png", "Complain.png")),
        ("show 혼동행렬", ("CardType.png", "Complain.png")),
        ("show 그래프", ("CardType.png", "Complain.png")),
    ]

    # 클릭 상태 보관
    if "selected_segment" not in st.session_state:
        st.session_state["selected_segment"] = None

    # 버튼 5개를 한 줄에 배치
    cols = st.columns(5)
    for i, (label, _) in enumerate(segments):
        if cols[i].button(label, key=f"btn_{i}"):
            st.session_state["selected_segment"] = label

    # 클릭된 버튼에 해당하는 이미지 렌더
    selected = st.session_state["selected_segment"]
    if selected is not None:
        # 선택된 세그먼트의 이미지 파일 찾기
        img_pair = dict(segments)[selected]

        st.markdown("---")
        st.subheader(selected)

        c1, c2 = st.columns(2)
        c1.image(IMG_DIR / img_pair[0], caption=f"{selected} - 그래프1", use_container_width=True)
        c2.image(IMG_DIR / img_pair[1], caption=f"{selected} - 그래프2", use_container_width=True)

with tab2:
    st.header("모델링 과정")
    st.write("여기에 모델링 관련 내용을 추가하세요.")