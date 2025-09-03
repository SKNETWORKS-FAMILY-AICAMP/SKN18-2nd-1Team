# service/utils/process/preprocessor.py
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

def make_preprocessor(feature_groups) -> ColumnTransformer:
    numeric = feature_groups['numeric']
    binary  = feature_groups['binary']
    onehot  = feature_groups['onehot']

    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([("scaler", StandardScaler())]), numeric))
    if binary:
        transformers.append(("bin", "passthrough", binary))
    if onehot:
        transformers.append(("oh", OneHotEncoder(handle_unknown='ignore'), onehot))

    preproc = ColumnTransformer(transformers=transformers, remainder='drop', sparse_threshold=0.3)
    return preproc
