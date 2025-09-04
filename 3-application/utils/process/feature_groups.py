# utils/process/feature_groups.py
from typing import Dict, List

def get_feature_groups() -> Dict[str, List[str]]:
    # 원본 수치/이진
    raw_numeric = ['CreditScore','Age','Tenure','Balance','NumOfProducts']
    raw_binary  = ['IsActiveMember']  # Complain 제외

    # 엔지니어드 (수치/이진)
    engineered_numeric = [
        'Balance_per_Product',
        'age_x_balance','age_x_products','balance_x_products'
    ]
    engineered_binary  = [
        'Senior_Flag','Germany_Flag','Germany_HighBalance','LowActive_LowProduct'
    ]

    # 원핫 대상 (범주/상호작용 포함)
    onehot_cats = [
        'Geography','Age_Group','Satisfaction_Level',
        'ia_x_card','geo_x_gender','agebin_x_salbin','tenbin_x_ia','cardtype_x_ia'
    ]

    return {
        'numeric': raw_numeric + engineered_numeric,
        'binary':  raw_binary + engineered_binary,
        'onehot':  onehot_cats
    }
