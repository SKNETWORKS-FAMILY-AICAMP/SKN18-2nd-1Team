# 3-application/pages/data_tool.py
import os
import sys
import io
import time
import contextlib
from pathlib import Path

import streamlit as st
from db.csv_to_db import main as do_csv_to_db
from pages.app_bootstrap import hide_builtin_nav, render_sidebar  # 필수

# ───────────────────────────────────────────────────────────────
# 경로 보정: service/utils 를 안정적으로 import 하기 위함
APP_ROOT = Path(__file__).resolve().parents[1]  # 3-application
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

# 공통 UI
hide_builtin_nav()
render_sidebar()

st.title("🧰 데이터 도구")
st.caption("데이터 관련 작업 버튼 모음 <주의> Docker 실행 !!")

# ───────────────────────────────────────────────────────────────
# 공용 실행 헬퍼 (스피너 + 완료 토스트 + (옵션) 실시간 로그 표시/자동 숨김)
def run_task(label, fn, *args, capture_log: bool = False, hide_log_on_done: bool = False, **kwargs):
    """
    label: 작업 라벨
    fn: 실행 함수
    capture_log: True면 stdout/stderr를 캡쳐해 실시간으로 표시
    hide_log_on_done: True면 성공 시 잠깐 보여주고 자동으로 로그 영역을 지움
    """
    log_box = None
    tee = None
    success = False

    if capture_log:
        st.write("🔎 실행 로그")
        log_box = st.empty()

        class _StreamlitTee(io.TextIOBase):
            def __init__(self, placeholder):
                self.placeholder = placeholder
                self.buf = []
                self.last_update = 0.0

            def write(self, s):
                if not isinstance(s, str):
                    s = s.decode("utf-8", errors="ignore")
                self.buf.append(s)
                # 너무 잦은 업데이트 방지 + 줄바꿈 시 즉시 갱신
                now = time.time()
                if ("\n" in s) or (now - self.last_update > 0.15):
                    text = "".join(self.buf)
                    # 너무 길면 뒤쪽만 보여주기
                    max_chars = 4000
                    if len(text) > max_chars:
                        text = "…(truncated)…\n" + text[-max_chars:]
                    self.placeholder.code(text, language="bash")
                    self.last_update = now
                return len(s)

            def flush(self):  # pragma: no cover
                pass

        tee = _StreamlitTee(log_box)

    try:
        if capture_log:
            with contextlib.redirect_stdout(tee), contextlib.redirect_stderr(tee):
                with st.spinner(f"{label} 실행 중…"):
                    result = fn(*args, **kwargs)
        else:
            with st.spinner(f"{label} 실행 중…"):
                result = fn(*args, **kwargs)

        success = True
        st.toast(f"✅ {label} 완료", icon="✅")
        return result

    except Exception as e:
        st.error(f"❌ {label} 실패: {e}")
        st.exception(e)

    finally:
        # 성공 시 잠깐 보여주고 로그 지우기
        if capture_log and hide_log_on_done and success and log_box is not None:
            time.sleep(0.8)
            log_box.empty()

# ───────────────────────────────────────────────────────────────
# 기초 테이블(bank_customer, rfm_result_once) 없으면 자동 CSV 적재
def _need_ingest_base_tables() -> bool:
    import pymysql
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = int(os.getenv("DB_PORT", "3306"))
    user = os.getenv("DB_USER", "root")
    pw   = os.getenv("DB_PASS", "root1234")
    db   = os.getenv("DB_NAME", "sknproject2")

    # DB가 없으면 적재 필요
    try:
        conn = pymysql.connect(host=host, port=port, user=user, password=pw,
                               database=db, charset="utf8mb4", autocommit=True)
    except Exception:
        return True

    try:
        with conn.cursor() as cur:
            cur.execute("SHOW TABLES LIKE 'bank_customer'")
            has_customer = cur.fetchone() is not None
            cur.execute("SHOW TABLES LIKE 'rfm_result_once'")
            has_rfm = cur.fetchone() is not None
        return not (has_customer and has_rfm)
    finally:
        conn.close()

def ensure_ingest_if_needed():
    if _need_ingest_base_tables():
        st.info("기초 테이블이 없어 CSV 적재부터 수행합니다.")
        run_task("CSV 적재", do_csv_to_db, capture_log=True, hide_log_on_done=True)

# ───────────────────────────────────────────────────────────────
# 모델 학습/스코어링 실행 (env → reload → main 호출 순서로 토글 반영)
def do_train_and_score(write_db: bool = True, create_view: bool = True):
    import importlib

    # 1) 토글을 환경변수에 먼저 반영
    os.environ["WRITE_DB"]    = "true" if write_db else "false"
    os.environ["CREATE_VIEW"] = "true" if create_view else "false"
    os.environ.setdefault("N_FOLDS", "5")
    os.environ.setdefault("RANDOM_STATE", "42")

    # 2) 모듈을 (재)로딩하여 최신 env 반영
    import service.full_scoring as full_scoring
    importlib.reload(full_scoring)

    # 3) 실행
    full_scoring.main()

    # 4) 결과 경로 반환
    models_dir = APP_ROOT / "models"
    latest_path = None
    try:
        latest = max(models_dir.glob("best_model_*.pkl"), key=lambda p: p.stat().st_mtime)
        latest_path = str(latest)
    except ValueError:
        pass
    scores_csv = str(APP_ROOT / "assets" / "data" / "churn_scores.csv")
    return {"model_pkl": latest_path, "scores_csv": scores_csv}

# ───────────────────────────────────────────────────────────────
# (UI) 모델링 섹션 — 페이지 최상단에 배치
st.subheader("모델링")
mc1, mc2 = st.columns([2, 1])
with mc2:
    do_db = st.toggle("DB 적재 + 뷰 생성", value=True, help="stg_churn_score 적재 + vw_rfm_for_app 생성")
with mc1:
    if st.button(
        "🤖 모델 학습/스코어링",
        use_container_width=True,
        help="CatBoost (SMOTENC vs Balanced) 5-Fold 평가 후 ACC 높은 모델을 저장하고 churn_scores.csv 생성"
    ):
        # DB에 쓸 예정이면, 기초 테이블이 없을 때 자동 CSV 적재부터 실행
        if do_db:
            ensure_ingest_if_needed()

        res = run_task(
            "모델 학습/스코어링",
            do_train_and_score,
            write_db=do_db,
            create_view=do_db,
            capture_log=True,          # 실시간 로그 표시
            hide_log_on_done=True      # 완료 시 로그 자동 숨김
        )
        if res:
            st.success("모델/스코어 생성 완료!")
            st.write("• 모델 파일:", res.get("model_pkl") or "(생성 확인 필요)")
            st.write("• 이탈 스코어 CSV:", res.get("scores_csv"))

# ───────────────────────────────────────────────────────────────
# (고급) 수동 적재 도구 — 필요할 때만 펼쳐서 사용
with st.expander("고급: 수동 적재 도구", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📥 CSV → DB 적재", use_container_width=True,
                     help="데이터셋을 가공하고 DB에 적재합니다 (Docker 필수)"):
            run_task("CSV 적재", do_csv_to_db, capture_log=True, hide_log_on_done=True)
    with c2:
        if st.button("♻️ 예비 버튼", use_container_width=True, help="예비 버튼입니다"):
            run_task("작업 필요하면 추가")

st.write("---")
st.caption("© 2025 BCMS")
