# utils/ui/ui_tools.py
import streamlit as st
import pandas as pd
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
    
# 그룹별 지표 영역
# def render_segment_kpis(seg_df):
#   c1, c2, c3, c4 = st.columns(4)
#   with c1:
#       st.metric("고객 수", f"{len(seg_df):,}")
#   with c2:
#       st.metric(
#           "평균 R/F/M",
#           f"{seg_df['r_score'].mean():.1f} / {seg_df['f_score'].mean():.1f} / {seg_df['m_score'].mean():.1f}"
#       )
#   with c3:
#       st.metric("평균 Churn", f"{(seg_df['churn_probability'].astype(float)).mean():.3f}")
#   with c4:
#       risky_ratio = (seg_df["churn_probability"].astype(float).fillna(0) >= 0.6).mean() * 100
#       st.metric("고위험 비율(≥0.6)", f"{risky_ratio:.1f}%")

if "_seg_metric_css" not in st.session_state:
    st.markdown("""
    <style>
    .metric-wrap {
      display:grid; grid-template-columns: repeat(4, 1fr);
      gap: 0; align-items: start;
      padding: 8px 0; margin: 10px 0 18px 0;
      border-radius: 14px;
      background: linear-gradient(180deg, rgba(var(--surface-1), var(--panel-a)), rgba(var(--surface-1), var(--panel-b)));
      border: 1px solid rgba(var(--border-rgb), var(--card-border));
    }
    .metric {
      padding: 14px 18px 16px 18px;
      position: relative;
    }
    .metric + .metric::before{
      content:""; position:absolute; top:14px; bottom:14px; left:0;
      width:1px; background: rgba(var(--border-rgb), .12);
    }
    .metric .label {
      font-size: 13px; font-weight: 600; color: rgb(var(--txt-dim));
      display:flex; align-items:center; gap:8px;
    }
    .metric .value {
      margin-top: 8px; font-size: 34px; font-weight: 800; letter-spacing: -.01em;
      font-variant-numeric: tabular-nums;
    }
    .metric .sub {
      margin-top: 6px; font-size: 12px; color: rgb(var(--txt-dim));
    }
    @media (max-width: 1100px){
      .metric-wrap { grid-template-columns: repeat(2, 1fr); }
      .metric + .metric::before{ display:none; }
    }
    </style>
    """, unsafe_allow_html=True)
    st.session_state._seg_metric_css = True

# === KPI 렌더 함수 ===
def render_segment_kpis(seg_df):
    df = seg_df.copy()

    # 숫자 컬럼 안전 캐스팅
    for col in ["r_score", "f_score", "m_score", "churn_probability"]:
        if col in df.columns:
            # 퍼센트 문자열일 수도 있으니 정리
            if col == "churn_probability":
                s = df[col].astype(str).str.strip()
                # 끝에 % 있으면 제거
                s = s.str.rstrip("%")
                cp = pd.to_numeric(s, errors="coerce")
                # 값이 1보다 크면 0~100로 판단 → 0~1로 환산
                if (cp.dropna() > 1).any():
                    cp = cp / 100.0
                df[col] = cp
            else:
                df[col] = pd.to_numeric(df[col], errors="coerce")

    risk_count = len(df)
    avg_r = df.get("r_score", pd.Series(dtype=float)).mean()
    avg_f = df.get("f_score", pd.Series(dtype=float)).mean()
    avg_m = df.get("m_score", pd.Series(dtype=float)).mean()

    avg_churn = df.get("churn_probability", pd.Series(dtype=float)).mean()
    avg_churn = 0.0 if pd.isna(avg_churn) else float(avg_churn)

    risky_ratio = (df.get("churn_probability", pd.Series(dtype=float)).fillna(0) >= 0.6).mean()
    risky_ratio = 0.0 if pd.isna(risky_ratio) else float(risky_ratio)

    st.markdown(f"""
    <div class="metric-wrap">
      <div class="metric">
        <div class="label">고객 수</div>
        <div class="value">{risk_count:,}</div>
      </div>
      <div class="metric">
        <div class="label">평균 R/F/M</div>
        <div class="value">{avg_r:.1f} / {avg_f:.1f} / {avg_m:.1f}</div>
        <div class="sub">스케일 1~5</div>
      </div>
      <div class="metric">
        <div class="label">평균 Churn</div>
        <div class="value">{avg_churn*100:.2f}%</div>
        <div class="sub">예측 이탈확률(평균)</div>
      </div>
      <div class="metric">
        <div class="label">고위험 비율(≥0.6)</div>
        <div class="value">{risky_ratio*100:.1f}%</div>
        <div class="sub">고객 중 Churn≥0.6 비중</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

