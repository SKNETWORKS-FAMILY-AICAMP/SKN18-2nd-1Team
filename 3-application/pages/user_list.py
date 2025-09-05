# 3-application/pages/02_user_list.py
# Read at DB version
import streamlit as st
import pandas as pd
from pathlib import Path
from pages.app_bootstrap import hide_builtin_nav, render_sidebar # 필수 
from utils.process.read_db import read_df #DB에서 df 읽어오는 함수
from st_aggrid import AgGrid, GridOptionsBuilder # 리스트 클릭 상호작용 가능하게 해주는 lib
from dotenv import load_dotenv

load_dotenv()  # .env 로드

# 공통
hide_builtin_nav()
render_sidebar()

st.set_page_config(page_title="고객 이탈률", page_icon="📊", layout="wide")

st.title("📊 고객 이탈률")

# ---------- 유틸 ----------
@st.cache_data(ttl=60) #로드 되는데 60초 캐시
def load_from_db() -> pd.DataFrame: #db에 올라간 bank_customer, stg_churn_score table 조합
    sql = """
    SELECT
      b.CustomerId, b.Surname, b.CreditScore, b.Geography, b.Gender,
      b.Age, b.Tenure, b.Balance, b.NumOfProducts, b.HasCrCard, b.IsActiveMember,
      b.EstimatedSalary, b.Exited,
      s.churn_probability AS predicted_proba
    FROM bank_customer b
    LEFT JOIN stg_churn_score s
      ON s.customer_id = b.CustomerId
    """
    df = read_df(sql)
    #컬럼명 수정
    df["predicted_exited"] = (df["predicted_proba"] >= 0.5).astype(int)
    return df

df = load_from_db()

def detect_score_cols(df: pd.DataFrame) -> tuple[str, str]:
    """
    결과 df에서 확률/레이블 컬럼 자동 탐지
    """
    proba_candidates = ["predicted_proba_oof", "predicted_proba"]
    label_candidates = ["predicted_exited_oof", "predicted_exited"]
    proba_col = next((c for c in proba_candidates if c in df.columns), None)
    label_col = next((c for c in label_candidates if c in df.columns), None)
    if not proba_col or not label_col:
        raise ValueError("예측 컬럼을 찾을 수 없습니다")
    return proba_col, label_col

proba_col, label_col = detect_score_cols(df)

left, right = st.columns([2, 1])
with left:
    # file_labels = [f"{p.name}  —  {p.stat().st_size/1024:.1f} KB" for p in result_files]
    # sel_idx = st.selectbox("결과 CSV 선택", options=range(len(result_files)), format_func=lambda i: file_labels[i])
    # sel_path = result_files[sel_idx]
    # st.caption(f"선택 파일: `{sel_path}`")
    pass


# ---------- 필터/정렬 영역 ----------
with right:
    st.subheader("필터")
    # 확률 슬라이더(0~1)
    min_p, max_p = st.slider("예측 확률 범위", 0.0, 1.0, (0.0, 1.0), 0.01)
    # 정렬 기준
    sort_desc = st.toggle("확률 내림차순 정렬", value=True)
    # 간단 텍스트 검색(성/ID)
    q = st.text_input("검색(성/ID 포함)", "")

# ---------- 리스트(요약) 빌드 ----------
# 존재 가능성이 높은 핵심 컬럼 추려서 요약 리스트 만들기
base_cols = []
for c in ["CustomerId", "Surname", "Age", "Geography", "Gender", "CreditScore"]:
    if c in df.columns:
        base_cols.append(c)
list_cols = base_cols + [proba_col, label_col]

list_df = df[list_cols].copy()
list_df.rename(columns={proba_col: "score", label_col: "label"}, inplace=True)

# 필터 적용
list_df = list_df[(list_df["score"] >= min_p) & (list_df["score"] <= max_p)]
if q:
    q_lower = q.lower()
    mask = pd.Series([False] * len(list_df))
    if "Surname" in list_df.columns:
        mask = mask | list_df["Surname"].astype(str).str.lower().str.contains(q_lower, na=False)
    if "CustomerId" in list_df.columns:
        mask = mask | list_df["CustomerId"].astype(str).str.contains(q_lower, na=False)
    list_df = list_df[mask]

# 정렬
list_df = list_df.sort_values("score", ascending=not sort_desc)

# ---------- 마스터(리스트) & 선택 ----------
st.subheader("고객 리스트 (요약)")
# 보여줄 행 수
n_show = st.slider("표시 행 수", 5, 200, 30, 5)
preview_df = list_df.head(n_show).reset_index(drop=True)

# 원본 매핑을 위한 숨김 인덱스 보존
if "_orig_idx" not in preview_df.columns:
    preview_df.insert(0, "_orig_idx", preview_df.index)

# ---- AgGrid 옵션 구성
gob = GridOptionsBuilder.from_dataframe(preview_df)
gob.configure_default_column(sortable=True, filter=True, resizable=True)
gob.configure_selection(selection_mode="single", use_checkbox=False)
gob.configure_pagination(paginationAutoPageSize=True)

# score 포맷
if "score" in preview_df.columns:
    gob.configure_column("score", type=["numericColumn"], valueFormatter="value.toFixed(3)")

# (선택) 숨김 컬럼
gob.configure_column("_orig_idx", hide=True)

grid_options = gob.build()

# ---- AgGrid 렌더(행 클릭 이벤트 수신)
grid_resp = AgGrid(
    preview_df,
    gridOptions=grid_options,
    height=420,
    fit_columns_on_grid_load=True,
    update_on=["selectionChanged"],
    allow_unsafe_jscode=True,
    enable_enterprise_modules=False,
    key="customers_grid",
)

# 선택된 행 받기
selected_rows = grid_resp.get("selected_rows", [])
if isinstance(selected_rows, pd.DataFrame):
    selected_rows = selected_rows.to_dict("records")  # ✅ DF → list[dict]

if selected_rows and len(selected_rows) > 0:          # ✅ 모호성 제거m
    sel_row = selected_rows[0]
    # 고유키로 매핑 (CustomerId 우선)
    if "CustomerId" in sel_row:
        sel_id = str(sel_row["CustomerId"])
    else:
        # 숨김 인덱스로 원본 df 매핑
        sel_id = str(sel_row.get("_orig_idx", 0))
else:
    sel_id = None

st.markdown("---")

# ---------- 디테일(선택 고객 상세) ----------
st.subheader("고객 상세")

if not sel_id:
    st.info("리스트에서 고객 행을 클릭하면 상세 정보가 여기에 표시됩니다.")
else:

    detail_row = None
    if "CustomerId" in df.columns:
        try:
            cid = int(sel_id)
            detail_row = df[df["CustomerId"] == cid].head(1)
        except ValueError:
            detail_row = df[df["CustomerId"].astype(str) == sel_id].head(1)
    else:
        # (CustomerId가 없다면, preview_df에서 인덱스를 hidden 컬럼으로 넘겨 받아 원본 df에 매핑하는 로직을 추가)
        pass

    if detail_row is None or detail_row.empty:
        st.warning("선택한 고객의 상세정보를 찾을 수 없습니다.")
    else:
        # score/label 컬럼명 자동 감지 함수 사용 가정(detect_score_cols)
        proba_col, label_col = detect_score_cols(df)
        score_val = float(detail_row[proba_col].values[0])
        label_val = int(detail_row[label_col].values[0])

        c1, c2, c3, c4 = st.columns(4)
        def v(col, default="N/A"):
            return detail_row[col].values[0] if col in detail_row.columns else default
        c1.metric("예측확률 (Churn)", f"{score_val*100:.2f}%")
        c2.metric("예측라벨", "이탈" if label_val == 1 else "유지")
        c3.metric("CustomerId", str(v("CustomerId")))
        c4.metric("Surname", str(v("Surname")))

        left_box, right_box = st.columns(2)
        with left_box:
            st.markdown("**프로필**")
            prof = {}
            for c in ["Geography", "Gender", "Age", "Tenure", "NumOfProducts", "HasCrCard", "IsActiveMember"]:
                if c in df.columns: prof[c] = v(c)
            st.table(pd.DataFrame(prof.items(), columns=["항목", "값"]))
        with right_box:
            st.markdown("**재무/점수**")
            fin = {}
            for c in ["CreditScore", "Balance", "EstimatedSalary"]:
                if c in df.columns: fin[c] = v(c)
            fin["predicted_proba"] = score_val
            fin["predicted_label"] = label_val
            st.table(pd.DataFrame(fin.items(), columns=["항목", "값"]))

        with st.expander("원본 레코드 전체 보기"):
            st.dataframe(detail_row.T, use_container_width=True)