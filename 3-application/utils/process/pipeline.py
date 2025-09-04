# service/utils/process/pipeline.py
from __future__ import annotations
from pathlib import Path
from datetime import datetime
import pandas as pd
import joblib

from utils.process.data_loader import load_csv_from_data
from utils.process.feature_engineering import engineer_features
from utils.process.feature_groups import get_feature_groups
from utils.process.preprocessor import make_preprocessor

from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier

# 현재 파일(pipeline.py) → process → utils → 3-application → root
_ROOT = Path(__file__).resolve().parents[2]   # == 3-application
MODELS_DIR  = _ROOT / "models"                # 모델 저장
RESULTS_DIR = _ROOT / "assets" / "data"       # 결과 CSV 저장
DATA_DIR    = _ROOT.parent / "1-analytics" / "data"  # 원본 CSV 폴더

MODELS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def train_and_predict_to_csv(
    input_filename: str | None = None,
    model_name: str = "rf",
    save_tag: str | None = None,
) -> dict:
    # 1) 데이터 로드 (원본 보존)
    df_raw = load_csv_from_data(filename=input_filename)

    # 2) 피처 엔지니어링
    data_fe = engineer_features(df_raw)
    y = data_fe["Exited"].astype(int)
    fg = get_feature_groups()
    use_cols = fg["numeric"] + fg["binary"] + fg["onehot"]
    X = data_fe[use_cols]

    # 3) 전처리 + 모델
    preproc = make_preprocessor(fg)
    model = RandomForestClassifier(
        n_estimators=300,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    pipe = Pipeline([("preprocess", preproc), ("model", model)])
    pipe.fit(X, y)

    # 예측 생성
    y_hat = pipe.predict(X)
    y_proba = pipe.predict_proba(X)[:, 1] if hasattr(model, "predict_proba") else None

    # 4) 결과 CSV 저장
    df_out = df_raw.copy()
    df_out["predicted_exited"] = y_hat
    if y_proba is not None:
        df_out["predicted_proba"] = y_proba

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    tag = f"_{save_tag}" if save_tag else ""
    result_name = f"result_{model_name}{tag}_{ts}.csv"
    result_path = RESULTS_DIR / result_name
    df_out.to_csv(result_path, index=False, encoding="utf-8-sig")

    # 5) 모델 저장
    model_name_out = f"model_{model_name}{tag}_{ts}.joblib"
    model_path = MODELS_DIR / model_name_out
    joblib.dump(pipe, model_path)

    print(f"[OK] Saved result CSV: {result_path}")
    print(f"[OK] Saved model:      {model_path}")
    return {
        "result_csv": result_path,
        "model_artifact": model_path,
        "used_input": DATA_DIR / (input_filename or "Customer-Churn-Records.csv"),
    }

if __name__ == "__main__":
    train_and_predict_to_csv()

############################
# 스트림릿에 보일 ML 결과 csv와, 재현용 모델 joblib 파일을 만드는 코드에요
# 사용법: 현재 터미널 위치가 root인지 확인하고 터미널에 아래 명령어 실행
#$env:PYTHONPATH=(Resolve-Path .\3-application).Path; python -m utils.process.pipeline
#만약 3-application\models에 모델이 있고, asset/data에 result csv가 있다면 실행하지 않아도 되요
############################
