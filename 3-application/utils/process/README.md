utils/
   └─ process/
      ├─ __init__.py
      ├─ data_loader.py
      ├─ feature_engineering.py
      ├─ feature_groups.py
      ├─ preprocessor.py
      ├─ split.py
      └─ utils.py

__init__.py — 외부로 내보낼 대표 API
data_loader.py — 데이터 로딩/초기 정리
feature_engineering.py — 파생 피처/전처리
feature_groups.py — 학습에 쓸 컬럼 묶음 정의
preprocessor.py — 전처리 파이프라인(ColumnTransformer)
split.py — 데이터 분할/교차검증 헬퍼
utils.py — 공통 유틸(시드/검증)

사용 예:
from service.utils.process import (
    load_csv_from_data, engineer_features, get_feature_groups,
    make_preprocessor, stratified_split, set_seed
)
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier

set_seed(42)

# 1) 로드 & 엔지니어링
df = load_csv_from_data("Customer-Churn-Records.csv")
data_fe = engineer_features(df)

# 2) X, y 구성
fg = get_feature_groups()
use_cols = fg['numeric'] + fg['binary'] + fg['onehot']
X = data_fe[use_cols]
y = data_fe['Exited'].astype(int)

# 3) 전처리 + 모델
preproc = make_preprocessor(fg)
model = RandomForestClassifier(
    n_estimators=300, class_weight='balanced', random_state=42, n_jobs=-1
)
pipe = Pipeline([("preprocess", preproc), ("model", model)])

# 4) split & 학습
X_tr, X_te, y_tr, y_te = stratified_split(X, y, test_size=0.2)
pipe.fit(X_tr, y_tr)
print("Train OK ✅")
