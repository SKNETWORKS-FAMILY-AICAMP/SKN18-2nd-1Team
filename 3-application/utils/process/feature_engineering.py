# utils/process/feature_engineering.py
import pandas as pd
import numpy as np


REQUIRED_COLUMNS = [
    'CreditScore','Age','Tenure','Balance','NumOfProducts','IsActiveMember',
    'Geography','Satisfaction Score','Exited',
    'HasCrCard','Gender','EstimatedSalary','Card Type'
]#complain은 제외라 미포함

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

    # IsActiveMember × HasCrCard (참/거짓 조합)
    data['ia_x_card'] = data['IsActiveMember'].astype(str) + '_' + data['HasCrCard'].astype(str)

    # 2) Geography × Gender (지역·성별 상호작용)
    data['geo_x_gender'] = data['Geography'].astype(str) + '_' + data['Gender'].astype(str)

    # 4) Age (bin) × EstimatedSalary (bin)
    data['age_bin'] = pd.qcut(data['Age'], q=5, duplicates='drop')
    data['sal_bin'] = pd.qcut(data['EstimatedSalary'], q=5, duplicates='drop')
    data['agebin_x_salbin'] = data['age_bin'].astype(str) + '_' + data['sal_bin'].astype(str)

    # 6) Tenure (bin) × IsActiveMember
    data['ten_bin'] = pd.qcut(data['Tenure'], q=5, duplicates='drop')
    data['tenbin_x_ia'] = data['ten_bin'].astype(str) + '_' + data['IsActiveMember'].astype(str)

    # 7) Card Type × IsActiveMember  (카디널리티 낮아 안전)
    data['cardtype_x_ia'] = data['Card Type'].astype(str) + '_' + data['IsActiveMember'].astype(str)

    # ===== C. 수치형 상호작용(트리/선형모델 모두에서 유효) =====
    # 스케일 민감한 선형 모델을 쓸 땐 이후 표준화 권장
    data['age_x_balance'] = data['Age'] * data['Balance']
    data['age_x_products'] = data['Age'] * data['NumOfProducts']
    data['balance_x_products'] = data['Balance'] * data['NumOfProducts']

    #  임시 bin들을 제거 시 아래 코드 활성화
    data.drop(columns=['sat_bin','age_bin','sal_bin','cs_bin','ten_bin','bin'], inplace=True, errors='ignore')

    return data
