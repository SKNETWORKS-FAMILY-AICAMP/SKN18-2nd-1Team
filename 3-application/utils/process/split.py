# utils/process/split.py
from typing import Tuple
import pandas as pd
from sklearn.model_selection import train_test_split

def train_test_split_xy(
    df: pd.DataFrame, target: str = "Exited", test_size: float = 0.3, random_state: int = 42
) -> Tuple[pd.DataFrame,pd.DataFrame,pd.Series,pd.Series]:
    assert target in df.columns, f"{target} 컬럼이 없습니다."
    X = df.drop(columns=[target])
    y = df[target].astype(int)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    return X_tr, X_te, y_tr, y_te
