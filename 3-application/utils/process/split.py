# service/utils/process/split.py
from sklearn.model_selection import train_test_split, StratifiedKFold

DEFAULT_RANDOM_STATE = 42

#데이터 분할은 7:3로 진행함
def stratified_split(X, y, test_size=0.3, random_state=DEFAULT_RANDOM_STATE):
    return train_test_split(X, y, test_size=test_size, stratify=y, random_state=random_state)

def get_stratified_kfold(n_splits=5, random_state=DEFAULT_RANDOM_STATE):
    return StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
