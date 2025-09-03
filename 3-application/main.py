# main.py
import streamlit as st
from pages.app_bootstrap import hide_builtin_nav, render_sidebar  # 필수

st.set_page_config(
    page_title="BCMS | Bank Customer Management System",
    page_icon="🏦",
    layout="wide",
)
hide_builtin_nav()   # 👈 추가: 기본 메뉴 숨김
render_sidebar()     # 👈 추가: 공통 사이드바 렌더

# --- 스타일 ---
st.markdown("""
<style>
.hero {
  padding: 32px 24px;
  border-radius: 18px;
  background: linear-gradient(90deg, rgba(37,99,235,.08), rgba(16,185,129,.08));
  border: 1px solid rgba(0,0,0,0.06);
}
.hero h1 { margin: 0 0 6px 0; font-size: 36px; }
.hero p  { margin: 0; font-size: 16px; opacity: .8; }
.card {
  padding: 18px;
  border: 1px solid rgba(0,0,0,0.06);
  border-radius: 14px;
}
</style>
""", unsafe_allow_html=True)

# --- 헤더(첫 진입 화면) ---
st.markdown(
    '<div class="hero"><h1>🏦 BCMS</h1><p>Bank Customer Management System</p></div>',
    unsafe_allow_html=True
)