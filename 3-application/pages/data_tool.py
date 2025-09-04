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
        # 예외 상세는 Streamlit이 그려줌
        st.exception(e)

    finally:
        # 성공 시 잠깐 보여주고 로그 지우기
        if capture_log and hide_log_on_done and success and log_box is not None:
            time.sleep(0.8)
            log_box.empty()

# ───────────────────────────────────────────────────────────────
# (새 섹션) 모델링: CatBoost(SMOTENC vs Balanced) 5-Fold → ACC 높은 모델 저장 + 스코어 CSV 생성
def do_train_and_score(write_db: bool = True, create_view: bool = True):
    """
    service.full_scoring.main() 실행 래퍼:
    - WRITE_DB / CREATE_VIEW 환경변수로 DB 적재/뷰 생성 on/off
    - 실행 후 최신 모델 pkl과 churn_scores.csv 경로 반환
    """
    from service.full_scoring import main as train_and_score

    # full_scoring 동작 옵션 (DB 적재/뷰 생성 여부)
    os.environ["WRITE_DB"] = "true" if write_db else "false"
    os.environ["CREATE_VIEW"] = "true" if create_view else "false"

    # 필요 시 폴드/시드 등 고정값 (없으면 기본값 사용)
    os.environ.setdefault("N_FOLDS", "5")
    os.environ.setdefault("RANDOM_STATE", "42")

    # 실행
    train_and_score()

    # 결과 경로 (모델 pkl은 타임스탬프 파일명)
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
        res = run_task(
            "모델 학습/스코어링",
            do_train_and_score,
            write_db=do_db,
            create_view=do_db,
            capture_log=True,          # ← 실시간 로그 표시
            hide_log_on_done=True      # ← 완료 시 로그 자동 숨김
        )
        if res:
            st.success("모델/스코어 생성 완료!")
            st.write("• 모델 파일:", res.get("model_pkl") or "(생성 확인 필요)")
            st.write("• 이탈 스코어 CSV:", res.get("scores_csv"))

# ───────────────────────────────────────────────────────────────
# (기존) 적재 섹션 — 버튼을 모델링 섹션 아래에 유지
with st.expander("고급: 수동 적재 도구", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📥 CSV → DB 적재", use_container_width=True,
                     help="데이터셋을 가공하고 DB에 적재합니다 (Docker 필수)"):
            run_task("CSV 적재", do_csv_to_db)
    with c2:
        if st.button("♻️ 예비 버튼", use_container_width=True, help="예비 버튼입니다"):
            run_task("작업 필요하면 추가")



### 필요하면 활용
# ───────────────────────────────────────────────────────────────
# st.subheader("적재 / 리프레시")
# c1, c2, c3 = st.columns(3)
# with c1:
#     if st.button("📥 CSV → DB 적재", use_container_width=True, help="csv_to_db.py 로직 연동 지점"):
#         run_task("CSV 적재")
# with c2:
#     if st.button("♻️ RFM 재계산", use_container_width=True, help="rfm_result_once 재생성/갱신"):
#         run_task("RFM 재계산")
# with c3:
#     if st.button("🧱 뷰 갱신(vw_rfm_for_app)", use_container_width=True, help="앱용 뷰 재생성"):
#         run_task("뷰 갱신")

# # ───────────────────────────────────────────────────────────────
# st.subheader("점검 / 도구")
# d1, d2, d3 = st.columns(3)
# with d1:
#     if st.button("🔌 DB 연결 테스트", use_container_width=True):
#         run_task("DB 연결 테스트")
# with d2:
#     if st.button("🧾 테이블 존재 체크", use_container_width=True, help="핵심 테이블/뷰 점검"):
#         run_task("테이블 체크")
# with d3:
#     if st.button("🧹 캐시 비우기", use_container_width=True, help="Streamlit cache 초기화"):
#         st.cache_data.clear()
#         st.toast("🧹 캐시 삭제 완료")

# # ───────────────────────────────────────────────────────────────
# st.subheader("내보내기")
# e1, e2, e3 = st.columns(3)
# with e1:
#     if st.button("⬇️ RFM CSV 내보내기", use_container_width=True):
#         run_task("RFM CSV 내보내기")
# with e2:
#     if st.button("⬇️ 세그먼트별 CSV", use_container_width=True):
#         run_task("세그먼트별 CSV 내보내기")
# with e3:
#     if st.button("⬇️ 고객 이탈 스코어", use_container_width=True):
#         run_task("이탈 스코어 CSV 내보내기")

# # ───────────────────────────────────────────────────────────────
# st.subheader("Danger Zone")
# st.info("실제 파괴적 작업(드랍/재생성 등)은 연결 후에만 활성화하세요.")
# z1, z2 = st.columns(2)
# with z1:
#     if st.button("🧨 테이블 재생성", use_container_width=True):
#         run_task("테이블 재생성")
# with z2:
#     if st.button("🧨 샘플 데이터 리셋", use_container_width=True):
#         run_task("샘플 데이터 리셋")


st.write("---")
st.caption("© 2025 BCMS")