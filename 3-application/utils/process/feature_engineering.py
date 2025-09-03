# service/utils/process/feature_engineering.py
import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    'CreditScore','Age','Tenure','Balance','NumOfProducts','IsActiveMember',
    'Geography','Satisfaction Score','Exited'
] #complain은 제외라 미포함

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()

    # 존재 컬럼 확인
    missing = [c for c in REQUIRED_COLUMNS if c not in data.columns]
    if missing:
        raise KeyError(f"[ERROR] 누락 컬럼: {missing}")

    # Age_Group (구간화)
    data['Age_Group'] = pd.cut(
        data['Age'], bins=[18, 30, 40, 50, 100],
        labels=['18-30','31-40','41-50','51+'], include_lowest=True
    )

    # Senior_Flag
    data['Senior_Flag'] = (data['Age'] >= 45).astype(int)

    # Germany 플래그 + 상호작용(고잔액)
    data['Germany_Flag'] = (data['Geography'] == 'Germany').astype(int)
    median_balance = data['Balance'].median()
    data['Germany_HighBalance'] = ((data['Geography'] == 'Germany') & (data['Balance'] > median_balance)).astype(int)

    # 잔액/상품수 (참여도)
    denom = data['NumOfProducts'].replace(0, np.nan)
    data['Balance_per_Product'] = (data['Balance'] / denom).fillna(0.0)

    # 비활동 & 상품 1개 (고위험) — Complain과 무관
    data['LowActive_LowProduct'] = ((data['IsActiveMember'] == 0) & (data['NumOfProducts'] == 1)).astype(int)

    # 만족도 구간화
    data['Satisfaction_Level'] = pd.cut(
        data['Satisfaction Score'], bins=[0,2,4,5],
        labels=['Low','Medium','High'], include_lowest=True
    )

    return data
