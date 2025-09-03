# 3-application/app_bootstrap.py
import streamlit as st

def hide_builtin_nav():
    """Streamlit 기본 멀티페이지 네비(상단 자동 목록) 숨김"""
    st.markdown("""
    <style>
      [data-testid="stSidebarNav"] { display: none !important; }
      section[data-testid="stSidebar"] { padding-top: .5rem; } /* optional */
    </style>
    """, unsafe_allow_html=True)

def render_sidebar():
    """BCMS 공통 사이드바"""
    with st.sidebar:
        st.header("BCMS")
        st.page_link("main.py", label="홈", icon="🏠")
        # st.page_link("pages/temp.py", label="머신러닝", icon="🤖")
        # st.page_link("pages/temp.py", label="고객 이탈율", icon="📉")
        st.page_link("pages/customer_rfm.py", label="고객 그룹(RFM)", icon="👥")
        st.page_link("pages/data_tool.py", label="데이터 도구", icon="🧰")
        st.write("---")
        st.caption("© 2025 BCMS")
