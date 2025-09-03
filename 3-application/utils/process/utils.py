# service/utils/process/utils.py
# seed고정, 컬럼 검증 함수
import os, random
import numpy as np
import pandas as pd

def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def assert_columns(df: pd.DataFrame, required: list[str]):
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"[ERROR] 누락 컬럼: {missing}")
