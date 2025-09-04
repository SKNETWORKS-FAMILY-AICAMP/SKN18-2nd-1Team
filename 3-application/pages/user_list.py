# 3-application/pages/01_Results_Browser.py
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Results Browser", page_icon="📊", layout="wide")

st.title("📊 ML Results Browser")

# 프로젝트 루트 기준 경로 계산
ROOT = Path(__file__).resolve().parents[1]   # 3-application
RESULTS_DIR = ROOT / "assets" / "data"      # result_*.csv 저장 폴더
MODELS_DIR = ROOT / "models"                # model_*.joblib 저장 폴더

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# --- 결과 CSV 목록 가져오기 ---
result_files = sorted(RESULTS_DIR.glob("result_*.csv"),
                      key=lambda p: p.stat().st_mtime,
                      reverse=True)

if not result_files:
    st.info("아직 결과 CSV 파일이 없습니다. 먼저 학습/예측을 실행해 주세요.")
    st.stop()

# 파일 선택 UI
file_labels = [f"{p.name}  —  {p.stat().st_size/1024:.1f} KB" for p in result_files]
selected = st.selectbox("결과 CSV 선택", options=list(range(len(result_files))),
                        format_func=lambda i: file_labels[i])

sel_path = result_files[selected]
st.success(f"선택된 파일: {sel_path.name}")

# 미리보기 옵션
nrows = st.slider("미리보기 행 수", min_value=5, max_value=200, value=50, step=5)

# CSV 읽기 + 표시
@st.cache_data(show_spinner=False)
def load_csv_preview(path: Path, n: int) -> pd.DataFrame:
    try:
        df = pd.read_csv(path)
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="utf-8-sig")
    return df.head(n)

df_preview = load_csv_preview(sel_path, nrows)
st.dataframe(df_preview, use_container_width=True, height=480)

# 다운로드 버튼
with open(sel_path, "rb") as f:
    st.download_button(
        label="⬇️ 결과 CSV 다운로드",
        data=f,
        file_name=sel_path.name,
        mime="text/csv"
    )

# --- 모델 아티팩트 목록 표시 ---
st.markdown("---")
st.subheader("🧩 Saved Models (.joblib)")
artifacts = sorted(MODELS_DIR.glob("*.joblib"),
                   key=lambda p: p.stat().st_mtime,
                   reverse=True)
if artifacts:
    for a in artifacts[:10]:
        st.write(f"- {a.name}  —  {a.stat().st_size/1024:.1f} KB")
else:
    st.write("저장된 모델이 없습니다.")
