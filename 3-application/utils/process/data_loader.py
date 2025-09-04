# utils/process/data_loader.py
import pandas as pd

REQ_COLUMNS = [
    "CustomerId","Surname","CreditScore","Geography","Gender","Age","Tenure",
    "Balance","NumOfProducts","HasCrCard","IsActiveMember","EstimatedSalary",
    "Exited","Complain","Satisfaction Score","Card Type","Point Earned"
]

def load_customer_csv(csv_path: str) -> pd.DataFrame:
    """고객 CSV 로드 및 기본 컬럼 체크/정리."""
    df = pd.read_csv(csv_path)
    # 필요한 컬럼만 우선 추출 (있으면)
    cols = [c for c in REQ_COLUMNS if c in df.columns]
    df = df[cols].copy()

    # 타입 정리
    cat_cols = ["Geography","Gender","Card Type","Surname"]
    for c in cat_cols:
        if c in df.columns:
            df[c] = df[c].astype("category")
    if "CustomerId" in df.columns:
        df["CustomerId"] = df["CustomerId"].astype(int)

    return df
