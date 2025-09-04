# utils/ui/ui_tools.py
import streamlit as st
from typing import Optional

def ensure_ui_css():
    """툴팁/메트릭 전역 CSS: 매 런마다 주입 (재실행 안정성)."""
    st.markdown("""
    <style>
      .bcms-metric{ display:inline-block; position:relative; margin:8px 16px; }
      .bcms-metric .label{ font-weight:600; }
      .bcms-metric .value{ font-size:24px; font-weight:700; }
      .bcms-metric .delta{ font-size:12px; color:var(--green, #16a34a); }

      .bcms-metric .bcms-tooltip{
        display:none !important;
        position:absolute; z-index:9999;
        top:100%; left:-40%;
        max-width:320px; width:max-content;
        background:rgba(255,255,255,.85); color:#000;
        border-radius:6px; padding:8px 10px;
        box-shadow:0 4px 16px rgba(0,0,0,.2);
        text-align:left; line-height:1.4;
        white-space:normal; cursor: pointer;
      }
      .bcms-metric:hover > .bcms-tooltip{
        display:block !important;
      }
    </style>
    """, unsafe_allow_html=True)

def metric_with_tooltip(label: str, value: str, delta: Optional[str] = None, tooltip: str = ""):
    delta_html = f'<div class="delta">Δ {delta}</div>' if delta else ""
    st.markdown(
        f"""
        <div class="bcms-metric">
          <div class="label">{label}</div>
          <div class="value">{value}</div>
          {delta_html}
          <div class="bcms-tooltip">{tooltip}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
