import os
import streamlit as st
import pandas as pd
from pathlib import Path
from pages.app_bootstrap import render_sidebar  # 필수
from st_aggrid import AgGrid, GridOptionsBuilder  # 리스트 클릭 상호작용
from dotenv import load_dotenv
import pymysql

# ───────────────────────────────────────────────────────────────
# LLM 추천 래퍼 (키가 없거나 에러여도 내부 폴백으로 안전 동작)
try:
    from utils.llm.reco_templates import recommend_for_user, PRODUCT_CATALOG
    _PROD_MAP = {p["code"]: p for p in PRODUCT_CATALOG}
except Exception:
    recommend_for_user = None
    PRODUCT_CATALOG = []
    _PROD_MAP = {}

# ───────────────────────────────────────────────────────────────
# 공통 UI
render_sidebar()
st.set_page_config(page_title="고객 이탈률", page_icon="📊", layout="wide")

st.title("📊 고객 이탈률")

#------ 데이터 획득 영역-------
load_dotenv()
def _get_conn_tuple():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASS", "rootpass"),
        database=os.getenv("DB_NAME", "sknproject2"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.Cursor,  # ✅ tuple cursor (중요) -> 얘가 없으면 리스트에 해당 컬럼명만 계속 뜨게 됩니다.
        autocommit=True,
    )


def read_df(sql: str, params=None) -> pd.DataFrame:
    conn = _get_conn_tuple()
    try:
        return pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()

@st.cache_data(ttl=60)
def load_from_db() -> pd.DataFrame:
    sql = """
    SELECT
      b.CustomerId, b.Surname, b.CreditScore, b.Geography, b.Gender, b.Complain, 
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

def detect_score_cols(df: pd.DataFrame) -> tuple[str, str]:
    proba_candidates = ["predicted_proba_oof", "predicted_proba"]
    label_candidates = ["predicted_exited_oof", "predicted_exited"]
    proba_col = next((c for c in proba_candidates if c in df.columns), None)
    label_col = next((c for c in label_candidates if c in df.columns), None)
    if not proba_col or not label_col:
        raise ValueError("예측 컬럼을 찾을 수 없습니다")
    return proba_col, label_col

#------ 데이터 표출 영역-------
df = load_from_db()
proba_col, label_col = detect_score_cols(df)

# 필터링 --> 사이드바에 배치
with st.sidebar:
    st.markdown("### 고객 정보 필터 ")
    min_p, max_p = st.slider("예측 확률 범위", 0.0, 1.0, (0.0, 1.0), 0.01)
    complain = st.multiselect("Complain 여부", sorted(df["Complain"].map({0: "No", 1: "Yes"}).unique()))
    geos = st.multiselect("국가(Geography)", sorted(df["Geography"].unique()))
    genders = st.multiselect("성별(Gender)", sorted(df["Gender"].unique()))
    age_groups = st.multiselect(
        "연령대 선택",
        ["10대 (10-19)", "20대 (20-29)", "30대 (30-39)",
         "40대 (40-49)", "50대 (50-59)", "60대 이상 (60+)"],
        default=[]
    )
    credit_groups = st.multiselect(
        "신용점수 등급",
        ["Excellent (800-850)", "Very Good (740-799)", "Good (670-739)", "Fair (580-669)", "Poor (300-579)"],
        default=[]
    )

keyword = st.text_input("검색(ID/성명)")

base_cols = [c for c in ["CustomerId", "Complain", "Age", "Gender", "Geography", "CreditScore", "NumOfProducts"] if c in df.columns]
list_cols = base_cols + [proba_col]
list_df = df[list_cols].copy()

rename_map = {
    "CustomerId": "CustomerId",
    "Complain": "Complain",          # 표시명 그대로 Complain (원하면 '불만' 등으로 바꾸세요)
    "Age": "나이",
    "Gender": "성별",
    "Geography": "지역",
    "CreditScore": "신용점수",
    "NumOfProducts": "가입상품",
    proba_col: "이탈율",
}
list_df.rename(columns={k: v for k, v in rename_map.items() if k in list_df.columns}, inplace=True)

# 필터 적용
list_df = list_df[(list_df["이탈율"] >= min_p) & (list_df["이탈율"] <= max_p)]

# 연령대 필터
if age_groups:
    age_masks = []
    for grp in age_groups:
        if grp == "10대 (10-19)": age_masks.append(list_df["나이"].between(10, 19))
        elif grp == "20대 (20-29)": age_masks.append(list_df["나이"].between(20, 29))
        elif grp == "30대 (30-39)": age_masks.append(list_df["나이"].between(30, 39))
        elif grp == "40대 (40-49)": age_masks.append(list_df["나이"].between(40, 49))
        elif grp == "50대 (50-59)": age_masks.append(list_df["나이"].between(50, 59))
        elif grp == "60대 이상 (60+)": age_masks.append(list_df["나이"] >= 60)
    if age_masks:
        list_df = list_df[pd.concat(age_masks, axis=1).any(axis=1)]

# 신용점수 필터
ranges = {
    "Excellent (800-850)": (800, 850),
    "Very Good (740-799)": (740, 799),
    "Good (670-739)": (670, 739),
    "Fair (580-669)": (580, 669),
    "Poor (300-579)": (300, 579),
}
if credit_groups:
    credit_masks = []
    for grp in credit_groups:
        lo, hi = ranges[grp]
        credit_masks.append(list_df["신용점수"].between(lo, hi))
    if credit_masks:
        list_df = list_df[pd.concat(credit_masks, axis=1).any(axis=1)]

# Complain 필터링
if complain and "Complain" in list_df.columns:
    comp_vals = [1 if c == "Yes" else 0 for c in complain]
    list_df = list_df[list_df["Complain"].isin(comp_vals)]

# 국가 / 성별
if geos:
    list_df = list_df[list_df["지역"].isin(geos)]
if genders:
    list_df = list_df[list_df["성별"].isin(genders)]

# 검색어 필터링(성/ID)
# --- 검색어 필터링 (성명은 df에서 검색, CustomerId는 list_df에서 직접 검색)
if keyword:
    kw = keyword.strip()
    if kw:
        mask = pd.Series(False, index=list_df.index)

        # 1) CustomerId 검색 (list_df 자체에 존재)
        if "CustomerId" in list_df.columns:
            mask |= list_df["CustomerId"].astype(str).str.contains(kw, na=False, regex=False)

        # 2) 성명 검색 (df에서 찾고, 해당 CustomerId만 필터링)
        if "Surname" in df.columns:
            matched_ids = df.loc[
                df["Surname"].astype(str).str.contains(kw, case=False, na=False, regex=False),
                "CustomerId"
            ].astype(str).tolist()

            if matched_ids:
                mask |= list_df["CustomerId"].astype(str).isin(matched_ids)

        list_df = list_df[mask]

# ---------- 마스터(리스트) & 선택 ----------
st.subheader("고객 리스트")

# 정렬
sort_desc = st.toggle("확률 내림차순 정렬", value=True)
list_df = list_df.sort_values("이탈율", ascending=not sort_desc)

# 페이지 크기 + 전체 보기
left, right = st.columns([1, 1])
with left:
    page_size = st.selectbox("페이지 크기", [25, 50, 100], index=1)
with right:
    show_all = st.toggle("전체 보기 (주의)", value=False)

# 표시용 DF (행 매핑용 숨김 인덱스 추가)
display_df = list_df.reset_index(drop=True).copy()
if "_orig_idx" not in display_df.columns:
    display_df.insert(0, "_orig_idx", display_df.index)

# ---- AgGrid 옵션 구성
gob = GridOptionsBuilder.from_dataframe(display_df)
gob.configure_column(
    "이탈율",
    type=["numericColumn"],
    valueFormatter="(value == null) ? '' : (value * 100).toFixed(2) + ' %'"
)
gob.configure_column(
    "Complain",
    valueFormatter="(value == 1) ? 'Yes' : (value == 0 ? 'No' : value)"
)
gob.configure_default_column(sortable=True, filter=True, resizable=True)
gob.configure_selection(selection_mode="single", use_checkbox=False)
if show_all:
    gob.configure_grid_options(pagination=False)
    gob.configure_pagination(enabled=False)
else:
    gob.configure_pagination(paginationAutoPageSize=False, paginationPageSize=page_size)
gob.configure_column("_orig_idx", hide=True)
grid_options = gob.build()

grid_resp = AgGrid(
    display_df,
    gridOptions=grid_options,
    height=600 if show_all else 420,
    fit_columns_on_grid_load=True,
    update_on=["selectionChanged"],
    allow_unsafe_jscode=True,
    enable_enterprise_modules=False,
    key="customers_grid",
    custom_css={
        ".ag-cell-focus": {"border": "none !important", "outline": "none !important"},
        ".ag-row-selected": {"background-color": "rgba(255, 99, 132, 0.12) !important"},
    },
)

# 선택된 행
selected_rows = grid_resp.get("selected_rows", [])
if isinstance(selected_rows, pd.DataFrame):
    selected_rows = selected_rows.to_dict("records")
if selected_rows:
    sel_row = selected_rows[0]
    sel_id = str(sel_row.get("CustomerId", sel_row.get("_orig_idx", "")))
else:
    sel_id = None

st.markdown("---")

# ---------- 디테일(선택 고객 상세 + LLM 추천) ----------
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

    if detail_row is None or detail_row.empty:
        st.warning("선택한 고객의 상세정보를 찾을 수 없습니다.")
        st.stop()

    # 기본 지표
    proba_col, label_col = detect_score_cols(df)
    score_val = float(detail_row[proba_col].values[0] * 100)
    label_val = int(detail_row[label_col].values[0])

    def v(col, default="N/A"):
        return detail_row[col].values[0] if col in detail_row.columns else default

    st.subheader(f"👤 고객 : {v('Surname')} ({v('CustomerId')})")
    st.markdown(' ')
    c1, c2 = st.columns(2)
    c1.markdown(
        f"""
        <style>
        .churn-score {{ margin-bottom:0.1rem; font-weight:600; }}
        .churn-value {{ font-size:2rem; font-weight:700; margin-top:0; color: var(--text-color); }}
        </style>
        <div class='churn-score'>예측확률 (Churn)</div>
        <div class='churn-value'>{score_val:.2f}%</div>
        """,
        unsafe_allow_html=True
    )

    color = "red" if label_val == 1 else "green"
    label_txt = "이탈" if label_val == 1 else "유지"
    c2.markdown(
        f"""
        <div style='margin-bottom:0.1rem; font-weight:600;'>예측라벨</div>
        <div style='font-size:2rem; font-weight:700; color:{color}; margin-top:0;'>{label_txt}</div>
        """, unsafe_allow_html=True
    )

    st.markdown('    ')
    left_box, right_box = st.columns(2)
    with left_box:
        st.markdown("**프로필**")
        prof = {}
        for c in ["Geography", "Gender", "Age", "Tenure", "NumOfProducts", "HasCrCard", "IsActiveMember","Complain"]:
            if c in df.columns:
                prof[c] = v(c)
        # Arrow 타입 혼합 이슈 방지: 값 컬럼 문자열화
        st.table(pd.DataFrame(prof.items(), columns=["항목", "값"]).astype({"값": "string"}))

    with right_box:
        st.markdown("**재무/점수**")
        fin = {}
        for c in ["CreditScore", "Balance", "EstimatedSalary"]:
            if c in df.columns:
                fin[c] = v(c)
        fin["predicted_proba"] = score_val
        fin["predicted_label"] = label_val
        st.table(pd.DataFrame(fin.items(), columns=["항목", "값"]).astype({"값": "string"}))

    with st.expander("원본 레코드 전체 보기"):
        st.dataframe(detail_row.T, width="stretch")

    # ── LLM 추천 (래퍼 사용: 내부에서 키 없으면 자동 폴백)
    st.subheader("🤖 추천 상품")

    row_for_prompt = {
        "CustomerId": v("CustomerId"),
        "Surname": v("Surname"),
        "Geography": v("Geography"),
        "Gender": v("Gender"),
        "Age": float(v("Age", 0) or 0),
        "Tenure": float(v("Tenure", 0) or 0),
        "Balance": float(v("Balance", 0) or 0),
        "NumOfProducts": int(v("NumOfProducts", 0) or 0),
        "HasCrCard": int(v("HasCrCard", 0) or 0),
        "IsActiveMember": int(v("IsActiveMember", 0) or 0),
        "EstimatedSalary": float(v("EstimatedSalary", 0) or 0),
        "CreditScore": float(v("CreditScore", 0) or 0),
        "churn_probability": float(detail_row[proba_col].values[0]),
    }

    if recommend_for_user is not None:
        reco = recommend_for_user(row_for_prompt)
    else:
        reco = {"summary": "LLM 모듈이 없습니다.", "top_products": [], "next_actions": [], "risk_level": "N/A"}

    # 렌더링
    colA, colB = st.columns([1, 2])
    with colA:
        st.metric("위험도", reco.get("risk_level", "N/A"))
    with colB:
        st.info(reco.get("summary", "요약 없음"))

    recs = reco.get("top_products", [])
    if recs:
        for r in recs:
            code = r.get("code", "")
            name = _PROD_MAP.get(code, {}).get("name", code)
            reason = r.get("reason", "")
            st.markdown(
                f"""
                <div style="border:1px solid #e5e7eb; border-radius:12px; padding:12px; margin-bottom:8px;">
                  <div style="font-weight:700;">{name} <span style="opacity:.6">({code})</span></div>
                  <div style="opacity:.85;">{reason}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.write("- (추천 없음)")

    acts = reco.get("next_actions", [])
    if acts:
        st.markdown("**다음 액션**")
        st.markdown("\n".join([f"- {a}" for a in acts]))

    # 키가 없으면 가이드 표시(UX 방해 X)
    if not os.getenv("OPENAI_API_KEY"):
        st.caption("※ LLM 키가 없어 정책 기반 폴백으로 동작 중입니다. (.env: OPENAI_API_KEY)")
