import time
from db.csv_to_db import main as do_csv_to_db
import streamlit as st
from pages.app_bootstrap import hide_builtin_nav, render_sidebar # 필수 
# 공통
hide_builtin_nav()
render_sidebar()

st.title("🧰 데이터 도구")
st.caption("데이터 관련 작업 버튼 모음 <주의> Docker 실행 !!")

# 공용 실행 헬퍼 (스피너 + 완료 토스트)
def run_task(label, fn, *args, **kwargs):
    try:
        with st.spinner(f"{label} 실행 중…"):
            result = fn(*args, **kwargs)
        st.toast(f"✅ {label} 완료", icon="✅")
        return result
    except Exception as e:
        st.error(f"❌ {label} 실패: {e}")
        st.exception(e)

# ───────────────────────────────────────────────────────────────
st.subheader("적재")
r1, r2 = st.columns(2)
with r1:
    if st.button("📥 CSV → DB 적재", use_container_width=True, help="데이터셋을 가공하고 DB에 적재합니다 (Docker 필수)"):
        run_task("CSV 적재", do_csv_to_db)  # 인자가 없다면 그대로 호출
with r2:
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
