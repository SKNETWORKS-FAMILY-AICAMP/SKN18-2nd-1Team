from __future__ import annotations
import pandas as pd
from pathlib import Path
from typing import Optional
from utils.config import DEFAULT_DATA_PATH

def load_raw(data_path: Optional[Path] = None) -> pd.DataFrame:
    """
    CSV 로드. 기본: assets/data/Customer-Churn-Records.csv
    """
    csv_path = data_path or DEFAULT_DATA_PATH
    return pd.read_csv(csv_path)
