# utils/process/feature_engineering.py
import pandas as pd

def add_basic_features(df: pd.DataFrame) -> pd.DataFrame:
    """가벼운 파생변수 (모델 안정성 + 약간의 성능 보탬)."""
    out = df.copy()
    if {"Balance","NumOfProducts"}.issubset(out.columns):
        out["balance_per_product"] = out["Balance"] / out["NumOfProducts"].clip(lower=1)
    if {"CreditScore"}.issubset(out.columns):
        out["is_high_credit"] = (out["CreditScore"] >= 700).astype(int)
    if {"Age"}.issubset(out.columns):
        out["age_bin"] = pd.cut(out["Age"], bins=[0,30,40,50,60,200], labels=False).astype("Int64")
    return out
