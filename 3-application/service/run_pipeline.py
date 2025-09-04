# run_pipeline.py  (place under 3-application/service)
from pathlib import Path
import os
import sys

# 워킹 디렉토리 기준 경로
HERE = Path(__file__).resolve()
APP = HERE.parent.parent

# 공통 ENV(필요시 수정)
os.environ.setdefault("DB_USER", "root")
os.environ.setdefault("DB_PASS", "root1234")
os.environ.setdefault("DB_HOST", "127.0.0.1")
os.environ.setdefault("DB_PORT", "3306")
os.environ.setdefault("DB_NAME", "sknproject2")

# full_scoring에서 DB/VIEW까지 쓰게끔
os.environ.setdefault("WRITE_DB", "true")
os.environ.setdefault("CREATE_VIEW", "true")

# 1) RFM 테이블 생성/갱신 (assets/data/Customer-Churn-Records.csv 자동 탐색)
print("[1/2] Build/refresh RFM tables ...")
sys.path.insert(0, str(APP))              # import 경로 보장
from db.load_rfm_once import main as build_rfm
build_rfm()                               # stg_bank_churn -> rfm_result_once

# 2) 모델 학습/선택/스코어 + stg_churn_score 적재 + 뷰 생성
print("[2/2] Train/select best model & score -> DB & view ...")
from service.full_scoring import main as train_and_score
train_and_score()

print("✅ All done. Check vw_rfm_for_app in DB and reload Streamlit.")
