# ui/style.py
import streamlit as st

# 공통 CSS를 문자열로 관리
COMMON_CSS = """
/* 예시 */
    :root{
    --bcms-bg1: 255,255,255;      /* light bg for glass */
    --bcms-txt: 15,23,42;         /* slate-900 */
    --bcms-txt-dim: 71,85,105;    /* slate-600 */
    --bcms-prim: 37,99,235;       /* blue-600 */
    --bcms-acc : 16,185,129;      /* emerald-500 */
    --bcms-warn: 234,88,12;       /* orange-600 */
    }
    @media (prefers-color-scheme: dark) {
    :root{
        --bcms-bg1: 30,41,59;       /* slate-800 */
        --bcms-txt: 241,245,249;    /* slate-100 */
        --bcms-txt-dim: 148,163,184;/* slate-400 */
    }
    }
    * { font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans KR", Apple SD Gothic Neo, "Malgun Gothic", Arial, "Helvetica Neue", sans-serif; }

    .hero {
        padding: 28px 26px;
        border-radius: 20px;
        background:
            radial-gradient(1100px 380px at 10% 20%, rgba(var(--bcms-prim), .14), transparent 60%),
            radial-gradient(900px 320px  at 90% -10%, rgba(var(--bcms-acc),  .18), transparent 60%),
            linear-gradient(180deg, rgba(var(--bcms-bg1), .70), rgba(var(--bcms-bg1), .55));
        backdrop-filter: blur(6px);
        border: 1px solid rgba(255,255,255,.10);
        box-shadow: 0 10px 30px rgba(0,0,0,.06);
        margin-bottom: 18px;
        color: rgb(var(--bcms-txt));
    }

    .hero .title {
        display:flex; align-items:center; gap:12px;
        font-size: 42px; font-weight: 800; letter-spacing: -.02em;
    }
    .hero .kicker {
        margin-top: 6px; display:flex; gap:10px; flex-wrap:wrap;
        color: rgba(var(--bcms-txt-dim), 1);
        font-size: 14px;
    }
    .badge {
        display:inline-flex; align-items:center; gap:8px;
        padding:6px 10px; border-radius: 999px;
        background: rgba(var(--bcms-prim), .10);
        color: rgb(var(--bcms-txt));
        border: 1px solid rgba(var(--bcms-prim), .20);
        font-weight: 600;
    }
    .badge .dot { width:8px; height:8px; border-radius:999px; background: rgba(var(--bcms-prim), .85); }

    .card {
        padding: 18px;
        border: 1px solid rgba(0,0,0,0.06);
        border-radius: 16px;
        background: linear-gradient(180deg, rgba(var(--bcms-bg1), .75), rgba(var(--bcms-bg1), .55));
        backdrop-filter: blur(4px);
        box-shadow: 0 10px 28px rgba(0,0,0,.05);
        transition: transform .15s ease, box-shadow .15s ease;
    }
    .card:hover { transform: translateY(-2px); box-shadow: 0 16px 40px rgba(0,0,0,.07); }
    .stat { font-size: 28px; font-weight: 800; letter-spacing: -.01em; }
    .kv { display:flex; justify-content:space-between; gap:8px; font-size:13px; color: rgb(var(--bcms-txt-dim)); }

    .quick a {
        display:flex; align-items:center; justify-content:center; gap:10px;
        padding: 12px 14px; border-radius: 12px; text-decoration:none;
        border: 1px solid rgba(0,0,0,.08); color: rgb(var(--bcms-txt));
        background: linear-gradient(180deg, rgba(var(--bcms-bg1), .7), rgba(var(--bcms-bg1), .5));
    }
    .quick a:hover { border-color: rgba(var(--bcms-prim), .35); box-shadow: 0 8px 24px rgba(37,99,235,.12); }

    .table-card { padding: 0; overflow:hidden; }
    .table-card .hd { padding: 14px 16px; border-bottom: 1px solid rgba(0,0,0,.06); font-weight:700; }
    .footnote { color: rgb(var(--bcms-txt-dim)); font-size: 12px; }
    
    /* ===== KPI 섹션 (패널) ===== */
    .kpi-anchor + div{
        margin: 14px 0 22px 0;
        padding: 22px 18px;
        border-radius: 18px;
        background:
            radial-gradient(900px 260px at 10% 0%, rgba(37,99,235,.10), transparent 60%),
            radial-gradient(900px 260px at 90% 100%, rgba(16,185,129,.12), transparent 60%),
            linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.03));
        border: 1px solid rgba(255,255,255,.06);
        box-shadow: 0 10px 28px rgba(0,0,0,.05);
    }

    /* 카드 */
    .kpi-card{
        padding:16px; border-radius:14px;
        background: linear-gradient(180deg, rgba(255,255,255,.08), rgba(255,255,255,.02));
        border: 1px solid rgba(255,255,255,.08);
        backdrop-filter: blur(6px);
        transition: transform .12s ease, box-shadow .12s ease;
    }
    .kpi-card:hover{ transform: translateY(-2px); box-shadow: 0 10px 28px rgba(0,0,0,.08); }
    .kpi-icon{ font-size:18px; opacity:.9; }
    .kpi-title{ font-size:13px; opacity:.9; margin-left:8px; }
    .kpi-stat{ font-size:30px; font-weight:800; letter-spacing:-.01em; margin-top:6px; }
    .kpi-sub{ display:flex; justify-content:space-between; gap:8px; font-size:12px; opacity:.85; margin-top:8px; }

    /* KPI 패널 내부 여백 보정 */
    .kpi-anchor + div .stColumn > div{ margin-bottom: 0 !important; }

    /* ===== Quick Action 섹션 ===== */
    .quick-anchor + div{
        margin: 18px 0 22px 0;
        padding: 20px 16px;
        border-radius: 18px;
        background:
            radial-gradient(900px 260px at 10% 0%, rgba(37,99,235,.10), transparent 60%),
            radial-gradient(900px 260px at 90% 100%, rgba(16,185,129,.12), transparent 60%),
            linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.03));
        border: 1px solid rgba(255,255,255,.06);
        box-shadow: 0 10px 28px rgba(0,0,0,.05);
    }

    .quick-card{
        padding: 16px;
        border-radius: 14px;
        background: linear-gradient(180deg, rgba(255,255,255,.08), rgba(255,255,255,.02));
        border: 1px solid rgba(255,255,255,.08);
        backdrop-filter: blur(6px);
        transition: transform .12s ease, box-shadow .12s ease;
        text-align:center;
    }
    .quick-card:hover{ transform: translateY(-2px); box-shadow: 0 10px 28px rgba(0,0,0,.08); }

    .quick-icon{ font-size:28px; display:block; margin-bottom:8px; }
    .quick-title{ font-size:15px; font-weight:600; margin-bottom:6px; }
    .quick-btn{
        display:inline-block; padding:8px 14px;
        border-radius:8px; border:1px solid rgba(255,255,255,.12);
        background: rgba(37,99,235,.15);
        color:inherit; text-decoration:none; font-size:13px; font-weight:500;
    }
    .quick-btn:hover{ background: rgba(37,99,235,.25); }
    
    /* ===== Customer-RFM Metirc, Tooltip ===== */
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
    
     /* ===== Customer-RFM 사용자 보기 Metric ===== */
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
    
     /* ===== 전략 추천 - LLM / 모달 ===== */
     
    /* Grid: 가로 3열 고정 */
    .bundle-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr); /* 3개 가로 */
        gap: 24px;
        margin-top: 20px;
        margin-bottom: 30px;
    }

    /* Card */
    .bundle-card {
        position: relative;
        background: #111418;
        border: 1px solid #252a31;
        border-radius: 16px;
        padding: 38px 28px 30px 28px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.25);
        transition:
            transform 0.15s ease,
            background 0.2s ease,
            border-color 0.2s ease;
    }
    .bundle-card:hover {
        transform: translateY(-2px);
        background: #141820;
        border-color: #2c323b;
    }

    /* 강조 라인 */
    .bundle-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;           /* 가로 전체 */
        height: 5px;        /* 높이 지정 */
        border-radius: 16px 16px 0 0;  /* 상단 모서리만 둥글게 */
        background: linear-gradient(90deg, #3b82f6, #22c55e); /* 좌→우 그라데이션 */
        opacity: 0.9;
    }

    /* Header */
    .bundle-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 10px;
    }
    .icon-badge {
        width: 50px;
        height: 50px;
        display: grid;
        place-items: center;
        border-radius: 10px;
        background: #ffffff;
        border: 1px solid #2a3038;
        font-size: 40px;
        line-height: 1;
    }
    .bundle-title {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    .bundle-title .name {
        font-weight: 700;
        font-size: 20px;
        color: #fff;
    }
    .bundle-title .code {
        font-family: monospace;
        color: #9aa4af;
        font-size: 0.6rem;
    }
    /* 상단 우측 Strategy 뱃지(옵션) */
    .strategy-badge{
        position: absolute;
        top: 10px;
        right: 5px;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: .02em;
        padding: 4px 10px;
        border-radius: 999px;
        background: #0e1a2b;
        border: 1px solid #274569;
        color: #a9c7f3;
    }
    /* Tags */
    .tags {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin: 8px 0 8px;
    }
    .tag {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 999px;
        background: #0e1319;
        border: 1px solid #27303a;
        color: #c8d1db;
        font-size: 0.82rem;
    }

    /* Reason */
    .reason {
        color: #cfd7e2;
        font-size: 0.95rem;
    }

    /* CTA 버튼 */
    .card-actions {
        display: flex;
        gap: 8px;
        margin-top: 14px;
    }
    .btn {
        border: 1px solid #2a323b;
        background: #0f1318;
        color: #e8edf2;
        padding: 6px 10px;
        border-radius: 10px;
        font-size: 0.9rem;
        cursor: pointer;
        transition:
            background 0.15s ease,
            border-color 0.15s ease,
            transform 0.05s ease;
    }
    .btn:hover {
        background: #151a21;
        border-color: #3a424c;
    }
    .btn:active {
        transform: translateY(1px);
    }
    .btn.primary {
        border-color: #2557d6;
        background: #103074;
    }
    .btn.primary:hover {
        background: #143a8f;
    }

    /* Modal */
    div[data-modal-container='true'][key='ai_strategy_modal'] {
        position: fixed !important; /* 뷰포트 기준 */
        z-index: 9999; /* 항상 위로 */
    }
    div[data-modal-container='true'][key='ai_strategy_modal'] > div {
        width: 85% !important;         /* 원하는 기본 폭 */
        max-width: 1280px !important;  /* 최대 폭 */
        min-width: 800px !important;   /* 최소 폭 */
        transition: none !important;   /* 애니메이션 없이 바로 */
    }
    /* 실제 모달 박스 */
    div[data-modal-container='true'][key='ai_strategy_modal'] > div:first-child{
        position: relative !important;
        max-width: 100% !important; /* 최대 너비 */
        border-radius: 12px;
        display: flex;
        align-items: center;
    }
    div[data-modal-container='true'][key='ai_strategy_modal'] > div:first-child > div:first-child {
        margin-top: 80px !important;
        padding: 24px !important;
    }
    div[data-modal-container='true'][key='ai_strategy_modal'] > div:first-child > div:first-child > div:first-child {
        max-width: none !important;
    }

"""
# width: 85% !important; /* 기본 너비 */

def apply_inline_css():
    print("############ APPLY CSS ############")
    if st.session_state.get("_inline_css_applied", False):
        return
    st.markdown(f"<style>{COMMON_CSS}</style>", unsafe_allow_html=True)
