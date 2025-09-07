# 3-application/pages/data_tool.py
import os, sys, io, time, contextlib
from pathlib import Path
import streamlit as st
from db.csv_to_db import main as do_csv_to_db
from pages.app_bootstrap import render_sidebar

APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

# ───────────────────────────────────────────────────────────────
# 공통 헤더/사이드바
render_sidebar()

# ───────────────────────────────────────────────────────────────
# 스타일 – 배포용 SaaS 대시보드 톤 (히어로/액션바/카드/칩/입력박스 룩)
st.markdown("""
<style>
:root{
  --bcms-bg:#0d1016;
  --bcms-card:#12161c;
  --bcms-soft:#171c24;
  --bcms-border:rgba(150,160,180,.20);
  --bcms-muted:#9aa3ad;
  --bcms-primary:#4f7cff; /* Primary */
  --bcms-primary-weak:#18233f;
  --bcms-success:#21c17a;
}
section[data-testid="stMain"]>div{padding-top:.5rem}

/* 히어로 */
.hero{display:flex;align-items:center;justify-content:space-between;
  background:var(--bcms-soft);border:1px solid var(--bcms-border);
  border-radius:16px;padding:16px 18px;margin-bottom:12px}
.hero-left{display:flex;gap:12px;align-items:center}
.hero-badge{font-size:22px;background:#1b2332;color:#dfe7ff;padding:.45rem .6rem;border-radius:10px;border:1px solid var(--bcms-border)}
.hero-title{font-size:26px;font-weight:800;margin:0}
.hero-sub{color:var(--bcms-muted);margin-top:-2px;font-size:14px}

/* 액션바 (큰 Primary 버튼 + 토글설명) */
.actionbar{display:flex;gap:14px;align-items:center;background:var(--bcms-card);
  border:1px solid var(--bcms-border);border-radius:14px;padding:14px 16px;margin-bottom:14px}
.actionbar .grow{flex:1}
.btn-primary{
  display:inline-flex;align-items:center;justify-content:center;gap:.5rem;
  background:var(--bcms-primary);color:#fff;border:1px solid rgba(255,255,255,.08);
  padding:.7rem 1rem;border-radius:10px;font-weight:800;letter-spacing:.2px;
}
.btn-primary:hover{filter:brightness(1.05)}
.help{font-size:12.5px;color:var(--bcms-muted)}

/* 카드 공통 */
.card{background:var(--bcms-card);border:1px solid var(--bcms-border);border-radius:14px;padding:16px}
.card h3{margin:0 0 10px 0;font-size:16px}
.hr{height:1px;background:var(--bcms-border);margin:12px 0}

/* 칩 */
.chips{display:flex;gap:8px;align-items:center}
.chip{display:inline-flex;align-items:center;gap:6px;padding:5px 10px;border-radius:999px;border:1px solid var(--bcms-border);font-size:12px;color:#dfe7ff;background:#0f1320}
.chip.ok{background:#0e2a1c;border-color:#1c6a38;color:#b8f5c7}
.chip.warn{background:#3c2f0e;border-color:#84621a;color:#ffd88a}

/* 안내 패널(문서 느낌) */
.guide{background:#0f1320;border:1px dashed var(--bcms-border);border-radius:14px;padding:16px}
.guide h4{margin:.2rem 0 .6rem 0}
.guide li{margin:.18rem 0;color:var(--bcms-muted)}

/* 코드 로그 */
div[data-testid="stCodeBlock"]{max-height:420px;overflow:auto}

/* 모달 폴백용 오버레이 */
.overlay{position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:9999;display:flex;align-items:center;justify-content:center}
.overlay .panel{width:min(920px,92vw);max-height:85vh;overflow:auto;background:#11151c;border:1px solid var(--bcms-border);border-radius:14px;padding:16px}
</style>
""", unsafe_allow_html=True)

# 히어로
st.markdown("""
<div class="hero">
  <div class="hero-left">
    <div class="hero-badge">🧰</div>
    <div>
      <div class="hero-title">데이터 도구</div>
      <div class="hero-sub">모델 학습/스코어링과 CSV 적재를 안전하게 실행합니다.</div>
    </div>
  </div>
  <div class="hero-sub">© 2025 BCMS</div>
</div>
""", unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────────
# 실행 헬퍼: 기존 로직 유지 + (선택) 외부 로그 placeholder
def run_task(label, fn, *args, capture_log=False, hide_log_on_done=False, log_placeholder=None, **kwargs):
    log_box = log_placeholder if capture_log else None
    tee = None; success=False

    if capture_log and log_box is None:
        st.write("🔎 실행 로그")
        log_box = st.empty()

    if capture_log:
        class _Tee(io.TextIOBase):
            def __init__(self, ph): self.ph=ph; self.buf=[]; self.t=0.0
            def write(self, s):
                if not isinstance(s,str): s=s.decode("utf-8","ignore")
                self.buf.append(s); now=time.time()
                if ("\n" in s) or (now-self.t>0.15):
                    text="".join(self.buf)
                    if len(text)>4000: text="…(truncated)…\\n"+text[-4000:]
                    self.ph.code(text, language="bash"); self.t=now
                return len(s)
            def flush(self): ...
        tee = _Tee(log_box)

    try:
        if capture_log:
            with contextlib.redirect_stdout(tee), contextlib.redirect_stderr(tee):
                with st.spinner(f"{label} 실행 중…"): result = fn(*args, **kwargs)
        else:
            with st.spinner(f"{label} 실행 중…"): result = fn(*args, **kwargs)
        success=True; st.toast(f"✅ {label} 완료", icon="✅"); return result
    except Exception as e:
        st.error(f"❌ {label} 실패: {e}"); st.exception(e)
    finally:
        if capture_log and hide_log_on_done and success and (log_placeholder is None) and log_box:
            time.sleep(.8); log_box.empty()

# ───────────────────────────────────────────────────────────────
def _need_ingest_base_tables()->bool:
    import pymysql
    host=os.getenv("DB_HOST","127.0.0.1"); port=int(os.getenv("DB_PORT","3306"))
    user=os.getenv("DB_USER","root"); pw=os.getenv("DB_PASS","root1234"); db=os.getenv("DB_NAME","sknproject2")
    try:
        conn=pymysql.connect(host=host,port=port,user=user,password=pw,database=db,charset="utf8mb4",autocommit=True)
    except Exception: return True
    try:
        with conn.cursor() as cur:
            cur.execute("SHOW TABLES LIKE 'bank_customer'"); has_customer=cur.fetchone() is not None
            cur.execute("SHOW TABLES LIKE 'rfm_result_once'"); has_rfm=cur.fetchone() is not None
        return not(has_customer and has_rfm)
    finally: conn.close()

def ensure_ingest_if_needed():
    if _need_ingest_base_tables():
        st.info("기초 테이블이 없어 CSV 적재부터 수행합니다.")
        run_task("CSV 적재", do_csv_to_db, capture_log=True, hide_log_on_done=True)

def do_train_and_score(write_db=True, create_view=True):
    import importlib
    os.environ["WRITE_DB"]="true" if write_db else "false"
    os.environ["CREATE_VIEW"]="true" if create_view else "false"
    os.environ.setdefault("N_FOLDS","5"); os.environ.setdefault("RANDOM_STATE","42")
    import service.full_scoring as full_scoring
    importlib.reload(full_scoring); full_scoring.main()
    models_dir=APP_ROOT/"models"; latest_path=None
    try:
        latest=max(models_dir.glob("best_model_*.pkl"), key=lambda p:p.stat().st_mtime); latest_path=str(latest)
    except ValueError: pass
    scores_csv=str(APP_ROOT/"assets"/"data"/"churn_scores.csv")
    return {"model_pkl": latest_path, "scores_csv": scores_csv}

def collect_status():
    needs=_need_ingest_base_tables()
    host=os.getenv("DB_HOST","127.0.0.1"); user=os.getenv("DB_USER","root"); db=os.getenv("DB_NAME","sknproject2")
    models_dir=APP_ROOT/"models"
    try: latest= max(models_dir.glob("best_model_*.pkl"), key=lambda p:p.stat().st_mtime).name
    except ValueError: latest=None
    scores_csv=(APP_ROOT/"assets"/"data"/"churn_scores.csv").exists()
    return {"db_ready": not needs, "host": host, "user": user, "db": db,
            "latest_model": latest, "scores_exists": scores_csv}

# ───────────────────────────────────────────────────────────────
# 상태/로그 모드
st.session_state.setdefault("bcms_do_db", True)
st.session_state.setdefault("log_mode", "인라인 로그")
HAS_DIALOG = hasattr(st, "dialog")

# 액션바 – 큰 Primary 버튼 + 토글 + 간단설명
col_action = st.container()
with col_action:
    st.markdown('<div class="actionbar">', unsafe_allow_html=True)
    colL, colM, colR = st.columns([3,2,5])
    with colL:
        run_clicked = st.button("🤖 모델 학습/스코어링", use_container_width=True)
    with colM:
        st.toggle("DB 적재 + 뷰 생성", key="bcms_do_db",
                  help="stg_churn_score 적재 + vw_rfm_for_app 생성")
    with colR:
        st.radio("로그 표시", ["인라인 로그", "팝업 로그" if HAS_DIALOG else "인라인 로그"],
                 key="log_mode", horizontal=True, label_visibility="collapsed")
        st.markdown('<div class="help">실행 전 Docker/DB 연결 상태를 확인하세요.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# 본문 레이아웃
left, right = st.columns([7,5], gap="large")

# ── 좌측: 실행/로그/가이드
with left:
    # 인라인 로그 카드 자리 고정
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 실행 로그")
    inline_log = st.empty()
    st.markdown("</div>", unsafe_allow_html=True)

    # 안내(문서 스타일)
    st.markdown('<div class="guide">', unsafe_allow_html=True)
    st.markdown("#### 작업 안내")
    st.markdown("""
    - **DB 적재 + 뷰 생성**이 켜져 있으면 기초 테이블 부재 시 CSV를 자동 적재합니다.  
    - **모델 학습/스코어링**은 교차검증 후 최적 모델을 저장하고 `churn_scores.csv`를 생성합니다.  
    - **로그 표시**는 *인라인* 또는 *팝업* 중에서 선택할 수 있습니다.  
    """)
    st.markdown("</div>", unsafe_allow_html=True)

    # 고급: 수동 적재 도구
    with st.expander("고급: 수동 적재 도구", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📥 CSV → DB 적재", use_container_width=True,
                         help="데이터셋을 가공하고 DB에 적재합니다 (Docker 필수)"):
                run_task("CSV 적재", do_csv_to_db, capture_log=True, hide_log_on_done=True)
        with c2:
            if st.button("♻️ 예비 버튼", use_container_width=True, help="예비 호출 자리"):
                st.toast("예비 작업 슬롯입니다.", icon="🛠️")

# ── 우측: 시스템 상태
with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 시스템 상태")
    s=collect_status()
    st.markdown(
        f'<div class="chips"><span class="chip {"ok" if s["db_ready"] else "warn"}">'
        f'DB 상태 · {"READY" if s["db_ready"] else "INIT NEEDED"}</span></div>',
        unsafe_allow_html=True)
    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
    st.write(f"• Host: **{s['host']}** · User: **{s['user']}** · DB: **{s['db']}**")
    st.write(f"• 최신 모델: **{s['latest_model'] or '없음'}**")
    st.write(f"• 스코어 CSV: **{'존재' if s['scores_exists'] else '없음'}**")
    if st.button("상태 새로고침", use_container_width=True):
        try: st.rerun()
        except AttributeError: st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

st.write("---"); st.caption("© 2025 BCMS")

# ───────────────────────────────────────────────────────────────
# 실행 트리거: 인라인/팝업 모드 처리
def _execute_with_inline():
    if st.session_state["bcms_do_db"]:
        ensure_ingest_if_needed()
    res = run_task("모델 학습/스코어링", do_train_and_score,
                   write_db=st.session_state["bcms_do_db"],
                   create_view=st.session_state["bcms_do_db"],
                   capture_log=True, hide_log_on_done=False,
                   log_placeholder=inline_log)
    if res:
        st.success("모델/스코어 생성 완료!")
        st.write("• 모델 파일:", res.get("model_pkl") or "(생성 확인 필요)")
        st.write("• 이탈 스코어 CSV:", res.get("scores_csv"))

def _execute_with_modal():
    if hasattr(st, "dialog"):
        @st.dialog("실행 로그", width="large")
        def _modal():
            ph = st.empty()
            if st.session_state["bcms_do_db"]:
                ensure_ingest_if_needed()
            run_task("모델 학습/스코어링", do_train_and_score,
                     write_db=st.session_state["bcms_do_db"],
                     create_view=st.session_state["bcms_do_db"],
                     capture_log=True, hide_log_on_done=False,
                     log_placeholder=ph)
            st.button("닫기", use_container_width=True, on_click=lambda: (st.rerun() if hasattr(st,"rerun") else st.experimental_rerun()))
        _modal()
    else:
        # 폴백 오버레이
        st.session_state["__show_overlay"]=True

if run_clicked:
    if st.session_state["log_mode"]=="팝업 로그" and HAS_DIALOG:
        _execute_with_modal()
    else:
        _execute_with_inline()

# 폴백 오버레이 렌더링(구버전)
if st.session_state.get("__show_overlay"):
    st.markdown('<div class="overlay"><div class="panel">', unsafe_allow_html=True)
    st.markdown("#### 실행 로그")
    ph=st.empty()
    if st.session_state["bcms_do_db"]:
        ensure_ingest_if_needed()
    run_task("모델 학습/스코어링", do_train_and_score,
             write_db=st.session_state["bcms_do_db"],
             create_view=st.session_state["bcms_do_db"],
             capture_log=True, hide_log_on_done=False,
             log_placeholder=ph)
    if st.button("닫기", use_container_width=True):
        st.session_state["__show_overlay"]=False
        try: st.rerun()
        except AttributeError: st.experimental_rerun()
    st.markdown("</div></div>", unsafe_allow_html=True)
