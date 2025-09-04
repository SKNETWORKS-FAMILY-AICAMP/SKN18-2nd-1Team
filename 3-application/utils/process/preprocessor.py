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
        transformers.append(("oh", OneHotEncoder(handle_unknown='ignore', sparse_output=False), onehot))

    return ColumnTransformer(
        transformers=transformers,
        remainder="drop",
        verbose_feature_names_out=False
    )
