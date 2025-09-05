# 3-application/pages/02_user_list.py
import streamlit as st
import pandas as pd
from pathlib import Path
from pages.app_bootstrap import hide_builtin_nav, render_sidebar # 필수 
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode # 리스트 클릭 상호작용 가능하게 해주는 lib

# 공통
hide_builtin_nav()
render_sidebar()

st.set_page_config(page_title="고객 이탈률", page_icon="📊", layout="wide")

st.title("📊 고객 이탈률")

# 경로
APP_ROOT   = Path(__file__).resolve().parents[1]   # .../3-application
RESULTS_DIR = APP_ROOT / "assets" / "data"
MODELS_DIR  = APP_ROOT / "models"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# ---------- 유틸 ----------
@st.cache_data(show_spinner=False)
def load_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="utf-8-sig")

def detect_score_cols(df: pd.DataFrame) -> tuple[str, str]:
    """
    결과 CSV에서 확률/레이블 컬럼 자동 탐지
    - OOF: predicted_proba_oof / predicted_exited_oof
    - holdout/insample: predicted_proba / predicted_exited
    """
    proba_candidates = ["predicted_proba_oof", "predicted_proba"]
    label_candidates = ["predicted_exited_oof", "predicted_exited"]
    proba_col = next((c for c in proba_candidates if c in df.columns), None)
    label_col = next((c for c in label_candidates if c in df.columns), None)
    if not proba_col or not label_col:
        raise ValueError("예측 컬럼을 찾을 수 없습니다. (predicted_proba[_oof], predicted_exited[_oof])")
    return proba_col, label_col

# ---------- 파일 선택 ----------
result_files = sorted(RESULTS_DIR.glob("result_*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
if not result_files:
    st.info("아직 결과 CSV가 없습니다. 먼저 파이프라인을 실행해 결과를 생성해 주세요.")
    st.stop()

left, right = st.columns([2, 1])
with left:
    file_labels = [f"{p.name}  —  {p.stat().st_size/1024:.1f} KB" for p in result_files]
    sel_idx = st.selectbox("결과 CSV 선택", options=range(len(result_files)), format_func=lambda i: file_labels[i])
    sel_path = result_files[sel_idx]
    st.caption(f"선택 파일: `{sel_path}`")

df = load_csv(sel_path)
proba_col, label_col = detect_score_cols(df)

# 필터링 --> 사이드바에 배치
with st.sidebar:
    st.markdown("### 고객 정보 필터 ")
    min_p, max_p = st.slider("예측 확률 범위", 0.0, 1.0, (0.0, 1.0), 0.01)
    complain = st.multiselect("Complain 여부", sorted(df["Complain"].map({0:"No",1:"Yes"}).unique()))
    geos = st.multiselect("국가(Geography)", sorted(df["Geography"].unique()))
    genders = st.multiselect("성별(Gender)", sorted(df["Gender"].unique()))
    # 나이_연령대
    age_groups = st.multiselect(
        "연령대 선택",
        ["10대 (10-19)", "20대 (20-29)", "30대 (30-39)",
        "40대 (40-49)", "50대 (50-59)", "60대 이상 (60+)"],
        default = []
    )

    # 나이_라이프 사이클
    # age_life_groups = st.multiselect(
    #     "연령대 선택",
    #     ["전체", "청소년(≤19)", "청년(20–34)", "중년(35–54)",
    #     "장년(55–64)", "노년(65+)"],default = []
    # )
    credit_groups = st.multiselect(
        "신용점수 등급",
        ["전체", "Excellent (800-850)", "Very Good (740-799)", 
        "Good (670-739)", "Fair (580-669)", "Poor (300-579)"],
        default=[]
        )


keyword = st.text_input("검색(성/ID 포함)")

base_cols = []
for c in ["CustomerId", "Age", "Gender", "Geography", "CreditScore", "NumOfProducts"]:
    if c in df.columns:
        base_cols.append(c)
list_cols = base_cols + [proba_col]

list_df = df[list_cols].copy()
list_df.columns = ["CustomerId", "나이", "성별", "지역", "신용점수", "가입상품","이탈율"]

# 필터 적용
list_df = list_df[(list_df["이탈율"] >= min_p) & (list_df["이탈율"] <= max_p)]

# 연령대 필터
if age_groups:
    age_masks = []
    for grp in age_groups:
        if grp == "10대 (10-19)":
            age_masks.append(list_df["나이"].between(10, 19))
        elif grp == "20대 (20-29)":
            age_masks.append(list_df["나이"].between(20, 29))
        elif grp == "30대 (30-39)":
            age_masks.append(list_df["나이"].between(30, 39))
        elif grp == "40대 (40-49)":
            age_masks.append(list_df["나이"].between(40, 49))
        elif grp == "50대 (50-59)":
            age_masks.append(list_df["나이"].between(50, 59))
        elif grp == "60대 이상 (60+)":
            age_masks.append(list_df["나이"] >= 60)

    if age_masks:
        list_df = list_df[pd.concat(age_masks, axis=1).any(axis=1)]

# # 라이프 사이클
# if age_life_groups:
#     age_masks = []
#     for grp in age_life_groups:
#         if grp == "청소년(≤19)":
#             age_masks.append(list_df["나이"].between(10, 19))
#         elif grp == "청년(20–34)":
#             age_masks.append(list_df["나이"].between(20, 34))
#         elif grp == "중년(35–54)":
#             age_masks.append(list_df["나이"].between(35, 54))
#         elif grp == "장년(55–64)":
#             age_masks.append(list_df["나이"].between(55, 64))
#         elif grp == "노년(65+)":
#             age_masks.append(list_df["나이"] >= 65)

#     if age_masks:  # 여러 조건을 OR 로 묶음
#         list_df = list_df[pd.concat(age_masks, axis=1).any(axis=1)]

# 신용점수 필터
ranges = {
    "Excellent (800-850)": (800, 850),
    "Very Good (740-799)": (740, 799),
    "Good (670-739)"     : (670, 739),
    "Fair (580-669)"     : (580, 669),
    "Poor (300-579)"     : (300, 579),
}

if credit_groups:
    credit_masks = []
    for grp in credit_groups:
        lo, hi = ranges[grp]
        credit_masks.append(list_df["신용점수"].between(lo, hi))
    if credit_masks:
        list_df = list_df[pd.concat(credit_masks, axis=1).any(axis=1)]

# Complain 필터링 ("Yes"/"No")
if complain:
    # "Yes" → 1, "No" → 0 변환
    comp_vals = [1 if c == "Yes" else 0 for c in complain]

    # 원본 df에서 CustomerId와 Complain 매핑 가져오기
    if "Complain" in df.columns:
        list_df = list_df.merge(df[["CustomerId", "Complain"]], on="CustomerId", how="left")
        list_df = list_df[list_df["Complain"].isin(comp_vals)]
        list_df.drop(columns=["Complain"], inplace=True, errors="ignore")

# 국가 필터링
if geos:
    list_df = list_df[list_df["지역"].isin(geos)]

# 성별 필터링
if genders:
    list_df = list_df[list_df["성별"].isin(genders)]


# 검색어 필터링
if keyword:
    keyword_lower = keyword.lower()
    mask = pd.Series([False] * len(list_df))
    if "Surname" in list_df.columns:
        mask = mask | list_df["Surname"].astype(str).str.lower().str.contains(keyword_lower, na=False)
    if "CustomerId" in list_df.columns:
        mask = mask | list_df["CustomerId"].astype(str).str.contains(keyword_lower, na=False)
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
gob.configure_default_column(sortable=True, filter=True, resizable=True)
gob.configure_selection(selection_mode="single", use_checkbox=False)
# 페이지네이션: 전체보기면 끄고, 아니면 page_size 적용
if show_all:
    gob.configure_grid_options(pagination=False)
    gob.configure_pagination(enabled=False)
else:
    gob.configure_pagination(paginationAutoPageSize=False, paginationPageSize=page_size)
# 숨김 컬럼
gob.configure_column("_orig_idx", hide=True)

grid_options = gob.build()

# ---- AgGrid 렌더(행 클릭 이벤트 수신)
grid_resp = AgGrid(
    display_df,
    gridOptions=grid_options,
    height=600 if show_all else 420,
    fit_columns_on_grid_load=True,
    update_on=["selectionChanged"],
    allow_unsafe_jscode=True,
    enable_enterprise_modules=False,
    key="customers_grid",
    custom_css={                                    # ✅ 셀 포커스 테두리 제거 + 선택행 하이라이트
        ".ag-cell-focus": {"border": "none !important", "outline": "none !important"},
        ".ag-row-selected": {"background-color": "rgba(255, 99, 132, 0.12) !important"},
    },
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
        name = detail_row["Surname"]
        # score/label 컬럼명 자동 감지 함수 사용 가정(detect_score_cols)
        proba_col, label_col = detect_score_cols(df)
        score_val = float(detail_row[proba_col].values[0]*100)
        label_val = int(detail_row[label_col].values[0])

        
        def v(col, default="N/A"):
            return detail_row[col].values[0] if col in detail_row.columns else default
        st.subheader(f"👤 고객 : {v('Surname')} ({v('CustomerId')})")

        st.markdown(' ')
        c1, c2 = st.columns(2)

        # 예측 확률
        c1.markdown(
            f"""
            <div style='margin-bottom:0.1rem; font-weight:600;'>예측확률 (Churn)</div>
            <div style='font-size:2rem; font-weight:700; color:#111; margin-top:0;'>{score_val:.2f}%</div>
            """, unsafe_allow_html=True)

        # 예측 라벨
        color = "red" if label_val == 1 else "green"
        label_txt = "이탈" if label_val == 1 else "유지"
        c2.markdown(
            f"""
            <div style='margin-bottom:0.1rem; font-weight:600;'>예측라벨</div>
            <div style='font-size:2rem; font-weight:700; color:{color}; margin-top:0;'>{label_txt}</div>
            """,unsafe_allow_html=True)


        st.markdown('    ')
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