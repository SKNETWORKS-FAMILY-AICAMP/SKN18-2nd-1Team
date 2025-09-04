# full_scoring.py
# ------------------------------------------------------------
# 목적: CatBoost 2가지 설정(SMOTENC vs Balanced) 중 5-Fold ACC가 높은 모델 채택
# 입력: assets/data/Customer-Churn-Records.csv (기본, auto-discover)
# 출력: models/best_model_YYYYMMDD_HHMMSS.pkl, assets/data/churn_scores.csv
# 옵션: stg_churn_score 테이블 적재, vw_rfm_for_app 뷰 생성
# ------------------------------------------------------------
import os
import pickle
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import sys
from pathlib import Path

from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# 프로젝트 경로 ------------------------------------------------
HERE = Path(__file__).resolve()
APP_DIR = HERE.parent.parent            # 3-application/
ASSETS_DIR = APP_DIR / "assets" / "data"
MODELS_DIR = APP_DIR / "models"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# ENV ---------------------------------------------------------
OUT_CSV       = os.getenv("OUT_CSV",  str(ASSETS_DIR / "churn_scores.csv"))
WRITE_DB      = os.getenv("WRITE_DB", "false").lower() in ("1","true","yes")
CREATE_VIEW   = os.getenv("CREATE_VIEW", "false").lower() in ("1","true","yes")
RANDOM_STATE  = int(os.getenv("RANDOM_STATE", "42"))
N_FOLDS       = int(os.getenv("N_FOLDS", "5"))
DB_USER       = os.getenv("DB_USER", "root")
DB_PASS       = os.getenv("DB_PASS", "root1234")
DB_HOST       = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT       = os.getenv("DB_PORT", "3306")
DB_NAME       = os.getenv("DB_NAME", "sknproject2")
DB_TABLE      = os.getenv("DB_TABLE", "stg_churn_score")

# utils.process 모듈 사용(데이터 로드/피처엔지니어링) -------------------------
# (__init__.py에서 공개 API로 export됨)
from utils.process import load_csv_from_data, engineer_features  #  

# CatBoost / SMOTENC ------------------------------------------
from catboost import CatBoostClassifier, Pool
try:
    from imblearn.over_sampling import SMOTENC
except Exception as _:
    SMOTENC = None  # imblearn 미설치 환경에서도 동작하도록

# 추천/상호작용 피처(노트북 기준) -------------------------------------------
RECOMMENDED_COLS = [
    # 1) 원본(6)
    "Geography", "Gender", "Age", "Balance", "NumOfProducts", "IsActiveMember",
    # 2) 파생/조합(4)
    "ia_x_card", "geo_x_gender", "agebin_x_salbin", "cardtype_x_ia",
    # 3) 플래그(1)
    "Germany_Flag",
]

def _timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def _cat_cols_and_idx(X: pd.DataFrame):
    cat_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()
    for c in cat_cols:
        X[c] = X[c].astype(str)
    cat_idx = [X.columns.get_loc(c) for c in cat_cols]
    return cat_cols, cat_idx

def _evaluate_catboost_cv(X: pd.DataFrame, y: np.ndarray, variant: str, cat_idx, random_state=42):
    """
    variant: 'smote' or 'balanced'
    반환: (metrics_dict, oof_best_threshold)
    """
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=random_state)

    accs, f1s, precs, recs, aucs = [], [], [], [], []
    oof_proba = np.zeros(len(y), dtype=float)
    oof_true  = np.zeros(len(y), dtype=int)

    for tr_idx, te_idx in skf.split(X, y):
        X_tr, X_te = X.iloc[tr_idx].copy(), X.iloc[te_idx].copy()
        y_tr, y_te = y[tr_idx], y[te_idx]

        # SMOTENC 적용
        if variant == "smote":
            if SMOTENC is None:
                raise RuntimeError("SMOTENC가 설치되지 않았습니다 (pip install imbalanced-learn).")
            smote = SMOTENC(categorical_features=cat_idx, sampling_strategy=0.67,
                            random_state=random_state, k_neighbors=5)
            X_res, y_res = smote.fit_resample(X_tr.values, y_tr)
            X_tr = pd.DataFrame(X_res, columns=X.columns)
            y_tr = y_res
            # resample 후 범주형 다시 문자열 보장
            for i in cat_idx:
                X_tr.iloc[:, i] = X_tr.iloc[:, i].astype(str)
                X_te.iloc[:, i] = X_te.iloc[:, i].astype(str)

        # CatBoost Pool
        train_pool = Pool(X_tr, y_tr, cat_features=cat_idx)
        test_pool  = Pool(X_te, y_te, cat_features=cat_idx)

        # 모델 설정
        params = dict(
            loss_function="Logloss",
            eval_metric="AUC",
            iterations=800,
            learning_rate=0.05,
            depth=6,
            l2_leaf_reg=3.0,
            random_state=random_state,
            verbose=False,
        )
        if variant == "balanced":
            params["auto_class_weights"] = "Balanced"

        model = CatBoostClassifier(**params)
        model.fit(train_pool, eval_set=test_pool, use_best_model=True, early_stopping_rounds=100, verbose=False)

        proba = model.predict_proba(test_pool)[:, 1]
        # 임시 고정 임계값(노트북 기준)로 1차 점수
        thr = 0.39 if variant == "smote" else 0.62
        pred = (proba >= thr).astype(int)

        oof_proba[te_idx] = proba
        oof_true[te_idx]  = y_te

        accs.append(accuracy_score(y_te, pred))
        f1s.append(f1_score(y_te, pred))
        precs.append(precision_score(y_te, pred, zero_division=0))
        recs.append(recall_score(y_te, pred))
        aucs.append(roc_auc_score(y_te, proba))

    # OOF 기준 최적 threshold 탐색(참고 정보)
    best_th, best_f1 = 0.5, 0.0
    for th in np.linspace(0.2, 0.8, 61):
        f1 = f1_score(oof_true, (oof_proba >= th).astype(int))
        if f1 > best_f1:
            best_f1, best_th = f1, th

    def fmt(arr): return f"{np.mean(arr):.4f} ± {np.std(arr):.4f}"
    report = {"ACC": fmt(accs), "F1": fmt(f1s), "Precision": fmt(precs), "Recall": fmt(recs), "ROC_AUC": fmt(aucs)}
    return report, float(best_th), float(np.mean(accs))

def _write_scores_and_view(df_scores: pd.DataFrame):
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

def main():
    np.random.seed(RANDOM_STATE)

    # 1) CSV 자동 탐색 로드
    df_raw = load_csv_from_data()  # 기본 경로: 3-application/assets/data/… 

    # 2) 피처 엔지니어링
    df_ = engineer_features(df_raw).copy()
    print(f"[INFO] engineer_features 완료. 현재 컬럼 수={len(df_.columns)}")
    print(f"[INFO] 컬럼 목록: {list(df_.columns)}")

    # 3) 추천/상호작용 피처 서브셋
    cols = [c for c in RECOMMENDED_COLS if c in df_.columns]
    X = df_[cols].copy()
    y = df_["Exited"].astype(int).values

    print(f"[INFO] 학습에 사용할 추천 피처 {len(cols)}개: {cols}")

    # 4) CatBoost 범주형 처리
    _, cat_idx = _cat_cols_and_idx(X)

    # 5) 두 변형을 5-Fold로 평가하여 ACC 평균이 더 높은 쪽 채택
    print("[CV] Evaluate CatBoost + SMOTENC …")
    try:
        rep_smote, best_th_smote, acc_smote = _evaluate_catboost_cv(X, y, "smote", cat_idx, RANDOM_STATE)
        print("[CV] SMOTENC:", rep_smote, f"(OOF best_th={best_th_smote:.3f})")
    except Exception as e:
        rep_smote, best_th_smote, acc_smote = None, None, -1.0
        print(f"[CV] SMOTENC failed: {e}")

    print("[CV] Evaluate CatBoost (auto_class_weights='Balanced') …")
    rep_bal, best_th_bal, acc_bal = _evaluate_catboost_cv(X, y, "balanced", cat_idx, RANDOM_STATE)
    print("[CV] Balanced:", rep_bal, f"(OOF best_th={best_th_bal:.3f})")

    # 6) 선택
    if acc_smote >= acc_bal:
        best_variant = "smote"
        print(f"[BEST] Choose SMOTENC (ACC={acc_smote:.4f} ≥ {acc_bal:.4f})")
    else:
        best_variant = "balanced"
        print(f"[BEST] Choose Balanced (ACC={acc_bal:.4f} > {acc_smote:.4f})")

    # 7) 최종 학습 (전체 학습 데이터)
    X_fit = X.copy()
    y_fit = y.copy()

    if best_variant == "smote":
        if SMOTENC is None:
            raise RuntimeError("SMOTENC 미설치 상태에서는 smote 변형으로 최종 학습할 수 없습니다.")
        smote = SMOTENC(categorical_features=cat_idx, sampling_strategy=0.67,
                        random_state=RANDOM_STATE, k_neighbors=5)
        X_res, y_res = smote.fit_resample(X_fit.values, y_fit)
        X_fit = pd.DataFrame(X_res, columns=X.columns)
        y_fit = y_res
        # 범주형 문자열 보장
        for i in cat_idx:
            X_fit.iloc[:, i] = X_fit.iloc[:, i].astype(str)

    params = dict(
        loss_function="Logloss",
        eval_metric="AUC",
        iterations=800,
        learning_rate=0.05,
        depth=6,
        l2_leaf_reg=3.0,
        random_state=RANDOM_STATE,
        verbose=False,
    )
    if best_variant == "balanced":
        params["auto_class_weights"] = "Balanced"

    train_pool = Pool(X_fit, y_fit, cat_features=cat_idx)
    model = CatBoostClassifier(**params)
    model.fit(train_pool, verbose=False)

    # 8) 저장 (타임스탬프 파일명)
    ts = _timestamp()
    model_path = MODELS_DIR / f"best_model_{ts}.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    print(f"[SAVE] model -> {model_path}")

    # 9) 전수 예측 확률 저장 (churn_scores.csv)
    #    주의: 확률(스코어) 저장. 임계값은 별도 메타로만 참고.
    full_pool = Pool(X, y, cat_features=cat_idx)
    prob = model.predict_proba(full_pool)[:, 1]
    out = pd.DataFrame({"customer_id": df_raw["CustomerId"].values, "churn_probability": prob})
    out.to_csv(OUT_CSV, index=False)
    print(f"[SAVE] scores -> {OUT_CSV} ({len(out):,} rows)")

    # 10) DB 적재(+VIEW)
    if WRITE_DB:
        _write_scores_and_view(out)

    # 간단 프린트
    print(out.head(10).to_string(index=False))

if __name__ == "__main__":
    main()
