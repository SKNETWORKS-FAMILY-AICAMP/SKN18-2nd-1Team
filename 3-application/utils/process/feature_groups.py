# service/utils/process/feature_groups.py
from typing import Dict, List

def get_feature_groups() -> Dict[str, List[str]]:
    raw_numeric = ['CreditScore','Age','Tenure','Balance','NumOfProducts']
    raw_binary  = ['IsActiveMember']  # Complain 제외

    engineered_numeric = ['Balance_per_Product']
    engineered_binary  = ['Senior_Flag','Germany_Flag','Germany_HighBalance','LowActive_LowProduct']

    onehot_cats = ['Geography','Age_Group','Satisfaction_Level'] #onehot 할 범주형들

    return {
        'numeric': raw_numeric + engineered_numeric,
        'binary':  raw_binary + engineered_binary,
        'onehot':  onehot_cats
    }
