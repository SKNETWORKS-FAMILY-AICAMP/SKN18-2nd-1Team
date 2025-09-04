# full_scoring.py  (place under: 3-application/service/)
# ------------------------------------------------------------
# 목적: LGBM/XGBoost/CatBoost 중 설치된 모델로 CV AUC 최고 모델 선택
# 입력: assets/data/Customer-Churn-Records.csv (기본)
# 출력: models/best_model.pkl, assets/data/churn_scores.csv
# 옵션: stg_churn_score 테이블 적재, vw_rfm_for_app 뷰 생성
# ------------------------------------------------------------
import os
import pickle
from pathlib import Path
import numpy as np
import pandas as pd

from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.base import BaseEstimator

# ---------- 프로젝트 경로 자동 인식 ----------
HERE = Path(__file__).resolve()
APP_DIR = HERE.parent.parent            # 3-application/
ASSETS_DIR = APP_DIR / "assets" / "data"
MODELS_DIR = APP_DIR / "models"

# ---------- 환경설정(필요시 env로 오버라이드) ----------
CSV_PATH  = os.getenv("BANK_CSV", str(ASSETS_DIR / "Customer-Churn-Records.csv"))
OUT_CSV   = os.getenv("OUT_CSV",  str(ASSETS_DIR / "churn_scores.csv"))
MODEL_PKL = os.getenv("MODEL_PATH", str(MODELS_DIR / "best_model.pkl"))

WRITE_DB   = os.getenv("WRITE_DB", "false").lower() in ("1","true","yes")
CREATE_VIEW= os.getenv("CREATE_VIEW", "false").lower() in ("1","true","yes")

DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "root1234")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "sknproject2")
DB_TABLE= os.getenv("DB_TABLE", "stg_churn_score")

RANDOM_STATE = int(os.getenv("RANDOM_STATE", "42"))
N_FOLDS      = int(os.getenv("N_FOLDS", "5"))

FEATURES = [
    "CreditScore","Age","Tenure","Balance",
    "NumOfProducts","HasCrCard","IsActiveMember","EstimatedSalary"
]

# ---------- 모델 팩토리 ----------
def get_available_models() -> dict[str, BaseEstimator]:
    models = {}
    try:
        from lightgbm import LGBMClassifier
        models["LGBM"] = LGBMClassifier(
            random_state=RANDOM_STATE, n_estimators=600, learning_rate=0.05,
            max_depth=-1, subsample=0.9, colsample_bytree=0.9
        )
    except Exception:
        pass
    try:
        from xgboost import XGBClassifier
        models["XGB"] = XGBClassifier(
            random_state=RANDOM_STATE, n_estimators=800, learning_rate=0.05,
            max_depth=4, subsample=0.9, colsample_bytree=0.9,
            tree_method="hist", eval_metric="logloss", n_jobs=-1
        )
    except Exception:
        pass
    try:
        from catboost import CatBoostClassifier
        models["CAT"] = CatBoostClassifier(
            random_state=RANDOM_STATE, iterations=1000, learning_rate=0.05,
            depth=6, loss_function="Logloss", verbose=False
        )
    except Exception:
        pass
    if not models:
        models["LR"] = LogisticRegression(max_iter=2000)
    return models

# ---------- 데이터 ----------
def load_data(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    needed = ["CustomerId","Exited"] + FEATURES
    miss = [c for c in needed if c not in df.columns]
    if miss:
        raise ValueError(f"Missing columns: {miss}")
    # 간단 결측 처리
    for c in FEATURES:
        if df[c].isna().any():
            if df[c].dtype.kind in "if":
                df[c] = df[c].fillna(df[c].median())
            else:
                df[c] = df[c].fillna(0)
    return df

def cv_auc(model: BaseEstimator, X: pd.DataFrame, y: pd.Series) -> float:
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    proba = cross_val_predict(model, X, y, cv=skf, method="predict_proba", n_jobs=-1)[:, 1]
    return roc_auc_score(y, proba)

# ---------- DB ----------
def write_scores_and_view(df_scores: pd.DataFrame):
    from sqlalchemy import create_engine, text
    url = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    eng = create_engine(url, pool_pre_ping=True)

    df_scores.to_sql(DB_TABLE, con=eng, if_exists="replace", index=False)
    print(f"[DB] wrote {len(df_scores):,} rows -> {DB_NAME}.{DB_TABLE}")

    if CREATE_VIEW:
        sql = """
        CREATE OR REPLACE VIEW vw_rfm_for_app AS
        SELECT r.*,
               s.churn_probability
        FROM rfm_result_once r
        LEFT JOIN stg_churn_score s
          ON s.customer_id = r.customer_id;
        """
        with eng.begin() as conn:
            conn.execute(text(sql))
        print("[DB] created/updated view: vw_rfm_for_app")

# ---------- 메인 ----------
def main():
    np.random.seed(RANDOM_STATE)

    # 경로 생성
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] CSV:   {CSV_PATH}")
    print(f"[INFO] MODEL: {MODEL_PKL}")
    print(f"[INFO] OUT:   {OUT_CSV}")

    df = load_data(CSV_PATH)
    X = df[FEATURES].copy()
    y = df["Exited"].astype(int).copy()

    # 후보 모델
    candidates = get_available_models()
    print(f"[INFO] candidates: {list(candidates.keys())}")

    # CV 선택
    scores = {}
    for name, mdl in candidates.items():
        try:
            auc = cv_auc(mdl, X, y)
            scores[name] = auc
            print(f"[CV] {name}: AUC={auc:.5f}")
        except Exception as e:
            print(f"[WARN] {name} failed on CV: {e}")

    if not scores:
        raise RuntimeError("No model could be evaluated.")

    best_name = max(scores, key=scores.get)
    best_model = candidates[best_name]
    print(f"[BEST] {best_name} selected (AUC={scores[best_name]:.5f})")

    # 전체 학습 & 저장
    best_model.fit(X, y)
    with open(MODEL_PKL, "wb") as f:
        pickle.dump(best_model, f)
    print(f"[SAVE] model -> {MODEL_PKL}")

    # 전수 예측 & 저장
    prob = best_model.predict_proba(X)[:, 1]
    out = pd.DataFrame({
        "customer_id": df["CustomerId"].values,
        "churn_probability": prob
    })
    out.to_csv(OUT_CSV, index=False)
    print(f"[SAVE] scores -> {OUT_CSV} ({len(out):,} rows)")

    # DB 적재(+뷰)
    if WRITE_DB:
        write_scores_and_view(out)

    print(out.head(10).to_string(index=False))

if __name__ == "__main__":
    main()
