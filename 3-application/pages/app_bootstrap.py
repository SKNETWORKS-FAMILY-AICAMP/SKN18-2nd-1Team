# 3-application/pages/app_bootstrap.py
import streamlit as st
from utils.ui.style import apply_inline_css


def _hide_builtin_nav():
    """Streamlit 기본 멀티페이지 네비(상단 자동 목록) 숨김 + 사이드바 정돈"""
    st.markdown(
        """
        <style>
          [data-testid="stSidebarNav"] { display: none !important; }
          section[data-testid="stSidebar"] { padding-top: .5rem; }
          /* 사이드바 링크 간격/호버 */
          [data-testid="stSidebar"] a { padding: .35rem .25rem !important; border-radius: 8px; }
          [data-testid="stSidebar"] a:hover { background: rgba(255,255,255,.06); }
        </style>
    """,
        unsafe_allow_html=True,
    )


def render_sidebar():
    st.markdown("""
    <style>
      .block-container { padding-top: 1.25rem !important; }
    </style>
    """, unsafe_allow_html=True)
    # 전체 css 로드
    apply_inline_css()
    # 기본 네비게이션 숨김
    _hide_builtin_nav()

    """BCMS 공통 사이드바"""
    with st.sidebar:
        st.header("BCMS")
        st.page_link("main.py", label="홈", icon="🏠")
        st.page_link("pages/page01_visualization.py", label="ML시각화", icon="📊")
        st.page_link("pages/user_list.py", label="고객 이탈률", icon="📉")
        st.page_link("pages/customer_rfm.py", label="고객 그룹(RFM)", icon="👥")
        st.page_link("pages/data_tool.py", label="데이터 도구", icon="🧰")
        st.write("---")
        st.caption("© 2025 BCMS")
