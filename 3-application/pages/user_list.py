# 3-application/pages/02_user_list.py
# Read at DB version (Tuple Cursor fix)
import os
import streamlit as st
import pandas as pd
import pymysql
from dotenv import load_dotenv
from st_aggrid import AgGrid, GridOptionsBuilder

from pages.app_bootstrap import hide_builtin_nav, render_sidebar  # 공통 UI

# ──────────────────────────────────────────────────────────────────────────────
# 1) .env 로드 + 페이지 공통
# ──────────────────────────────────────────────────────────────────────────────
load_dotenv()

st.set_page_config(page_title="고객 이탈률", page_icon="📊", layout="wide")
hide_builtin_nav()
render_sidebar()

st.title("📊 고객 이탈률")

# ──────────────────────────────────────────────────────────────────────────────
# 2) DB 연결(일반 Cursor) + pandas.read_sql 전용 함수
#    - DictCursor(=dict row)는 pandas.read_sql과 궁합이 안 맞아
#      값 대신 'customer_id' 같은 문자열이 반복되는 문제가 발생합니다.
#    - 반드시 tuple 커서(Cursor)로 연결하세요.
# ──────────────────────────────────────────────────────────────────────────────
def _get_conn_tuple():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASS", "rootpass"),
        database=os.getenv("DB_NAME", "sknproject2"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.Cursor,  # ✅ tuple cursor (중요)
        autocommit=True,
    )

def read_df(sql: str, params=None) -> pd.DataFrame:
    conn = _get_conn_tuple()
    try:
        return pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()

# ──────────────────────────────────────────────────────────────────────────────
# 3) 데이터 로드
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_from_db() -> pd.DataFrame:
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
    # 예측 라벨 파생
    if "predicted_proba" in df.columns:
        df["predicted_exited"] = (df["predicted_proba"] >= 0.5).astype(int)
    return df

df = load_from_db()

def detect_score_cols(df: pd.DataFrame) -> tuple[str, str]:
    proba_candidates = ["predicted_proba_oof", "predicted_proba"]
    label_candidates = ["predicted_exited_oof", "predicted_exited"]
    proba_col = next((c for c in proba_candidates if c in df.columns), None)
    label_col = next((c for c in label_candidates if c in df.columns), None)
    if not proba_col or not label_col:
        raise ValueError("예측 컬럼을 찾을 수 없습니다")
    return proba_col, label_col

proba_col, label_col = detect_score_cols(df)

# ──────────────────────────────────────────────────────────────────────────────
# 4) 우측 필터 영역
# ──────────────────────────────────────────────────────────────────────────────
left, right = st.columns([2, 1])
with right:
    st.subheader("필터")
    min_p, max_p = st.slider("예측 확률 범위", 0.0, 1.0, (0.0, 1.0), 0.01)
    sort_desc = st.toggle("확률 내림차순 정렬", value=True)
    q = st.text_input("검색(성/ID 포함)", "")

# ──────────────────────────────────────────────────────────────────────────────
# 5) 요약 리스트(DataFrame) 구성
# ──────────────────────────────────────────────────────────────────────────────
base_cols = [c for c in ["CustomerId", "Surname", "Age", "Geography", "Gender", "CreditScore"] if c in df.columns]
list_cols = base_cols + [proba_col, label_col]

list_df = df[list_cols].copy()
list_df.rename(columns={proba_col: "score", label_col: "label"}, inplace=True)

# 필터
list_df = list_df[(list_df["score"] >= min_p) & (list_df["score"] <= max_p)]
if q:
    q_lower = q.lower()
    mask = pd.Series(False, index=list_df.index)
    if "Surname" in list_df.columns:
        mask |= list_df["Surname"].astype(str).str.lower().str.contains(q_lower, na=False)
    if "CustomerId" in list_df.columns:
        mask |= list_df["CustomerId"].astype(str).str.contains(q_lower, na=False)
    list_df = list_df[mask]

# 정렬
list_df = list_df.sort_values("score", ascending=not sort_desc)

# ──────────────────────────────────────────────────────────────────────────────
# 6) 그리드 & 선택
# ──────────────────────────────────────────────────────────────────────────────
st.subheader("고객 리스트 (요약)")
n_show = st.slider("표시 행 수", 5, 200, 30, 5)
preview_df = list_df.head(n_show).reset_index(drop=True)

if "_orig_idx" not in preview_df.columns:
    preview_df.insert(0, "_orig_idx", preview_df.index)

gob = GridOptionsBuilder.from_dataframe(preview_df)
gob.configure_default_column(sortable=True, filter=True, resizable=True)
gob.configure_selection(selection_mode="single", use_checkbox=False)
gob.configure_pagination(paginationAutoPageSize=True)
if "score" in preview_df.columns:
    gob.configure_column("score", type=["numericColumn"], valueFormatter="value.toFixed(3)")
gob.configure_column("_orig_idx", hide=True)
grid_options = gob.build()

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

selected_rows = grid_resp.get("selected_rows", [])
if isinstance(selected_rows, pd.DataFrame):
    selected_rows = selected_rows.to_dict("records")
sel_row = selected_rows[0] if selected_rows else None
sel_id = str(sel_row["CustomerId"]) if sel_row and "CustomerId" in sel_row else None

st.markdown("---")

# ──────────────────────────────────────────────────────────────────────────────
# 7) 상세
# ──────────────────────────────────────────────────────────────────────────────
st.subheader("고객 상세")
if not sel_id:
    st.info("리스트에서 고객 행을 클릭하면 상세 정보가 여기에 표시됩니다.")
else:
    try:
        cid = int(sel_id)
        detail_row = df[df["CustomerId"] == cid].head(1)
    except ValueError:
        detail_row = df[df["CustomerId"].astype(str) == sel_id].head(1)

    if detail_row is None or detail_row.empty:
        st.warning("선택한 고객의 상세정보를 찾을 수 없습니다.")
    else:
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
