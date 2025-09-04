# utils/process/preprocessor.py
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

CATEGORICAL = ["Geography","Gender","Card Type","Surname"]
NUMERIC     = [
    "CreditScore","Age","Tenure","Balance","NumOfProducts",
    "HasCrCard","IsActiveMember","EstimatedSalary","Complain",
    "Satisfaction Score","Point Earned"
]

def build_preprocessor(df: pd.DataFrame) -> ColumnTransformer:
    cats = [c for c in CATEGORICAL if c in df.columns]
    nums = [c for c in NUMERIC if c in df.columns]

    pre = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cats),
            ("num", StandardScaler(), nums),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )
    return pre
