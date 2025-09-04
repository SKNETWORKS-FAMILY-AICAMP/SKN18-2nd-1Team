# 3-application/utils/process/pipeline.py
from __future__ import annotations
from pathlib import Path
from datetime import datetime
import json
import joblib
import numpy as np
import pandas as pd

# utils.process의 공개 API 사용 (__init__.py에 묶여 있음)
from utils.process import (
    load_csv_from_data,          # CSV 로더  :contentReference[oaicite:7]{index=7}
    engineer_features,           # 피처 엔지니어링 :contentReference[oaicite:8]{index=8}
    get_feature_groups,          # 피처 그룹(숫자/이진/원핫) :contentReference[oaicite:9]{index=9}
    make_preprocessor,           # 전처리 파이프라인  :contentReference[oaicite:10]{index=10}
    stratified_split,            # 7:3 분할(기본)  :contentReference[oaicite:11]{index=11}
    get_stratified_kfold,        # K-Fold 생성     :contentReference[oaicite:12]{index=12}
    set_seed,                    # 시드 고정        :contentReference[oaicite:13]{index=13}
)

from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    roc_auc_score, average_precision_score, f1_score,
    precision_score, recall_score
)

# ─────────────────────────────────────────────
# 경로: 3-application 기준으로 저장
# ─────────────────────────────────────────────
_APP_ROOT   = Path(__file__).resolve().parents[2]     # .../3-application
MODELS_DIR  = _APP_ROOT / "models"                    # 모델 저장
RESULTS_DIR = _APP_ROOT / "assets" / "data"           # 결과 CSV 저장
DATA_DIR    = _APP_ROOT / "assets" / "data"           # (참고: data_loader 기본도 이 폴더)  :contentReference[oaicite:15]{index=15}

MODELS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# 헬퍼
# ─────────────────────────────────────────────
def _now_tag() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def _make_pipe(fg) -> Pipeline:
    """전처리 + 모델로 구성된 Pipeline 생성"""
    preproc = make_preprocessor(fg)  # 숫자: StandardScaler, 이진: passthrough, 범주: OneHot  :contentReference[oaicite:16]{index=16}
    model = RandomForestClassifier(
        n_estimators=300,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    return Pipeline([("preprocess", preproc), ("model", model)])

def _metrics(y_true, y_prob=None, y_pred=None) -> dict:
    m = {}
    if y_prob is not None:
        m["roc_auc"] = float(roc_auc_score(y_true, y_prob))
        m["pr_auc"]  = float(average_precision_score(y_true, y_prob))
    if y_pred is not None:
        m["f1"]        = float(f1_score(y_true, y_pred))
        m["precision"] = float(precision_score(y_true, y_pred))
        m["recall"]    = float(recall_score(y_true, y_pred))
    return m

# ─────────────────────────────────────────────
# 메인 파이프라인
# ─────────────────────────────────────────────
def train_and_predict_to_csv(
    mode: str = "holdout",           # "holdout" | "oof" | "insample"
    input_filename: str | None = None,
    save_tag: str | None = None,
    test_size: float = 0.3,          # split.py 기본 7:3과 맞춤  :contentReference[oaicite:17]{index=17}
    n_splits: int = 5,
    seed: int = 42,
) -> dict:
    """
    mode:
    - holdout : 7:3(기본) 분할 → test에만 예측 저장(평가용)
    - oof     : StratifiedKFold OOF 예측 → 전 샘플 '검증 기반' 예측
    - insample: 전체 학습→전체 예측(대시보드/시연용)
    """
    set_seed(seed)  # 재현성  :contentReference[oaicite:18]{index=18}

    # 1) 데이터 로드 (원본을 수정하지 않음)
    df_raw = load_csv_from_data(filename=input_filename)  # 기본 경로: 3-application/assets/data  :contentReference[oaicite:19]{index=19}

    # 2) 피처 엔지니어링 + 컬럼확인
    data_fe = engineer_features(df_raw)                   # 필수 컬럼 검사/파생 생성  :contentReference[oaicite:20]{index=20}
    # (engineer_features 내부에 REQUIRED_COLUMNS 체크가 있으므로 별도 assert_columns 생략 가능하지만,
    #  필요 시 아래처럼 사용할 수 있습니다)
    # from utils.process.feature_engineering import REQUIRED_COLUMNS
    # assert_columns(data_fe, REQUIRED_COLUMNS)

    # 3) 피처 그룹/입력 행렬 구성
    fg = get_feature_groups()                             # 숫자/이진/원핫 컬렉션  :contentReference[oaicite:21]{index=21}
    feat_cols = fg["numeric"] + fg["binary"] + fg["onehot"]
    X = data_fe[feat_cols]
    y = data_fe["Exited"].astype(int).to_numpy()

    ts  = _now_tag()
    tag = f"_{save_tag}" if save_tag else ""

    # 4) 모드별 학습/예측
    if mode == "holdout":
        # stratified 7:3 분할  :contentReference[oaicite:22]{index=22}
        X_tr, X_te, y_tr, y_te = stratified_split(X, y, test_size=test_size)
        pipe = _make_pipe(fg)
        pipe.fit(X_tr, y_tr)

        y_prob_te = pipe.predict_proba(X_te)[:, 1]
        y_pred_te = (y_prob_te >= 0.5).astype(int)

        # test 레코드에만 예측 붙여 저장
        df_out = df_raw.iloc[X_te.index].copy()
        df_out["predicted_exited"] = y_pred_te
        df_out["predicted_proba"]  = y_prob_te

        result_path = RESULTS_DIR / f"result_holdout{tag}_{ts}.csv"
        df_out.to_csv(result_path, index=False, encoding="utf-8-sig")

        model_path = MODELS_DIR / f"model_holdout{tag}_{ts}.joblib"
        joblib.dump(pipe, model_path)

        metrics = _metrics(y_te, y_prob_te, y_pred_te)

    elif mode == "oof":
        skf = get_stratified_kfold(n_splits=n_splits)     # 5-Fold CV  :contentReference[oaicite:23]{index=23}
        oof_prob = np.zeros(len(y), dtype=float)
        oof_pred = np.zeros(len(y), dtype=int)

        for tr_idx, te_idx in skf.split(X, y):
            pipe = _make_pipe(fg)
            pipe.fit(X.iloc[tr_idx], y[tr_idx])
            prob_te = pipe.predict_proba(X.iloc[te_idx])[:, 1]
            oof_prob[te_idx] = prob_te
            oof_pred[te_idx] = (prob_te >= 0.5).astype(int)

        # 전 레코드에 OOF 예측 붙여 저장
        df_out = df_raw.copy()
        df_out["predicted_exited_oof"] = oof_pred
        df_out["predicted_proba_oof"]  = oof_prob

        result_path = RESULTS_DIR / f"result_oof_k{n_splits}{tag}_{ts}.csv"
        df_out.to_csv(result_path, index=False, encoding="utf-8-sig")

        # 배포용 최종 모델: 전체 데이터로 재학습
        final_pipe = _make_pipe(fg)
        final_pipe.fit(X, y)
        model_path = MODELS_DIR / f"model_oof_fullfit{tag}_{ts}.joblib"
        joblib.dump(final_pipe, model_path)

        metrics = _metrics(y, oof_prob, oof_pred)  # OOF 기준

    elif mode == "insample":
        pipe = _make_pipe(fg)
        pipe.fit(X, y)
        prob_all = pipe.predict_proba(X)[:, 1]
        pred_all = (prob_all >= 0.5).astype(int)

        df_out = df_raw.copy()
        df_out["predicted_exited"] = pred_all
        df_out["predicted_proba"]  = prob_all

        result_path = RESULTS_DIR / f"result_insample{tag}_{ts}.csv"
        df_out.to_csv(result_path, index=False, encoding="utf-8-sig")

        model_path = MODELS_DIR / f"model_insample{tag}_{ts}.joblib"
        joblib.dump(pipe, model_path)

        metrics = _metrics(y, prob_all, pred_all)

    else:
        raise ValueError("mode must be one of {'holdout','oof','insample'}")

    # 5) 메타 저장(선택)
    meta = {
        "mode": mode,
        "timestamp": ts,
        "input_csv": str((DATA_DIR / (input_filename or "Customer-Churn-Records.csv")).resolve()),
        "features": {
            "numeric": fg["numeric"],
            "binary":  fg["binary"],
            "onehot":  fg["onehot"],
        },
        "metrics": metrics,
        "result_csv": str(result_path.resolve()),
        "model_path": str(model_path.resolve()),
        "n_splits": n_splits if mode == "oof" else None,
        "test_size": test_size if mode == "holdout" else None,
        "seed": seed,
    }
    meta_path = result_path.with_suffix(".meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"[OK] Saved result CSV: {result_path}")
    print(f"[OK] Saved model:      {model_path}")
    print(f"[OK] Metrics: {metrics}")
    print(f"[OK] Meta:    {meta_path}")

    return {
        "result_csv": result_path,
        "model_artifact": model_path,
        "metrics": metrics,
        "meta": meta_path
    }

# 모듈 직접 실행 시: holdout 기본
if __name__ == "__main__":
    train_and_predict_to_csv(mode="holdout")

######################################
#모델 결과 csv와 모델 재현용 joblib, meta 만드는 코드
#사용법: root 경로에서, 터미널에 $env:PYTHONPATH=(Resolve-Path .\3-application).Path; python -m utils.process.pipeline 치기 