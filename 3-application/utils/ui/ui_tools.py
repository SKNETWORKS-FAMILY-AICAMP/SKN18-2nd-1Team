# utils/ui/ui_tools.py
import streamlit as st
import pandas as pd
from typing import Optional

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

# === 세그먼트 한글 라벨 ===
SEGMENT_LABELS = {
    "VIP": "👑 핵심 고객(VIP)",
    "LOYAL": "💎 충성 고객(LOYAL)",
    "AT_RISK": "⚠️ 위험 고객(RISK)",
    "LOW": "💤 저활성 고객(LOW)",
}
def seg_label_without_icon(code: str) -> str:
    """라벨만 (아이콘 제거)"""
    label = SEGMENT_LABELS.get(code)
    if label:
        return label.lstrip("👑💎🤝⚠️💤 ").strip()
    return code
def seg_label(code: str) -> str:
    return SEGMENT_LABELS.get(code, code)

# 전체/고위험/Top20 모드별 데이터 선택
def show_table_data_by_view_mode(view_mode, seg_df):
    cp = pd.to_numeric(seg_df["churn_probability"], errors="coerce").fillna(0.0)

    if view_mode == "top10":
        view_df = (
            seg_df.assign(_cp=cp)
                .sort_values("_cp", ascending=False)
                .drop(columns=["_cp"])
                .head(10)
                .reset_index(drop=True)
        )
        st.markdown(
            '<span style="color:red; font-weight:bold; font-size:14px;">※ 이 세그먼트에서 예측 이탈확률이 가장 높은 10명</span>',
            unsafe_allow_html=True
        )
    elif view_mode == "risky":
        # 고위험: churn_probability ≥ 0.6
        view_df = (
            seg_df.loc[cp >= 0.6]
                .assign(_cp=cp[cp >= 0.6])
                .sort_values("_cp", ascending=False)
                .drop(columns=["_cp"])
                .reset_index(drop=True)
        )
        st.markdown(
            '<span style="color:#ea580c; font-weight:bold; font-size:14px;">※ 고위험(Churn ≥ 0.6) 고객 목록</span>',
            unsafe_allow_html=True
        )
      
    else:
        view_df = seg_df
        
    return view_df