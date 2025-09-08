# import os
# import streamlit as st
# import pandas as pd
# from pathlib import Path
# from pages.app_bootstrap import render_sidebar  # 필수
# from st_aggrid import AgGrid, GridOptionsBuilder  # 리스트 클릭 상호작용
# from dotenv import load_dotenv
# import pymysql

# # ───────────────────────────────────────────────────────────────
# # LLM 추천 래퍼 (키가 없거나 에러여도 내부 폴백으로 안전 동작)
# try:
#     from utils.llm.reco_templates import recommend_for_user, PRODUCT_CATALOG
#     _PROD_MAP = {p["code"]: p for p in PRODUCT_CATALOG}
# except Exception:
#     recommend_for_user = None
#     PRODUCT_CATALOG = []
#     _PROD_MAP = {}

# # ───────────────────────────────────────────────────────────────
# # 공통 UI
# render_sidebar()
# st.set_page_config(page_title="고객 이탈률", page_icon="📊", layout="wide")

# st.title("📊 고객 이탈률")

# #------ 데이터 획득 영역-------
# load_dotenv()
# def _get_conn_tuple():
#     return pymysql.connect(
#         host=os.getenv("DB_HOST", "127.0.0.1"),
#         port=int(os.getenv("DB_PORT", "3306")),
#         user=os.getenv("DB_USER", "root"),
#         password=os.getenv("DB_PASS", "rootpass"),
#         database=os.getenv("DB_NAME", "sknproject2"),
#         charset="utf8mb4",
#         cursorclass=pymysql.cursors.Cursor,  # ✅ tuple cursor (중요) -> 얘가 없으면 리스트에 해당 컬럼명만 계속 뜨게 됩니다.
#         autocommit=True,
#     )


# def read_df(sql: str, params=None) -> pd.DataFrame:
#     conn = _get_conn_tuple()
#     try:
#         return pd.read_sql(sql, conn, params=params)
#     finally:
#         conn.close()

# @st.cache_data(ttl=60)
# def load_from_db() -> pd.DataFrame:
#     sql = """
#     SELECT
#       b.CustomerId, b.Surname, b.CreditScore, b.Geography, b.Gender, b.Complain, 
#       b.Age, b.Tenure, b.Balance, b.NumOfProducts, b.HasCrCard, b.IsActiveMember,
#       b.EstimatedSalary, b.Exited,
#       s.churn_probability AS predicted_proba
#     FROM bank_customer b
#     LEFT JOIN stg_churn_score s
#       ON s.customer_id = b.CustomerId
#     """
#     df = read_df(sql)
#     # 예측 라벨 파생
#     if "predicted_proba" in df.columns:
#         df["predicted_exited"] = (df["predicted_proba"] >= 0.5).astype(int)
#     return df

# def detect_score_cols(df: pd.DataFrame) -> tuple[str, str]:
#     proba_candidates = ["predicted_proba_oof", "predicted_proba"]
#     label_candidates = ["predicted_exited_oof", "predicted_exited"]
#     proba_col = next((c for c in proba_candidates if c in df.columns), None)
#     label_col = next((c for c in label_candidates if c in df.columns), None)
#     if not proba_col or not label_col:
#         raise ValueError("예측 컬럼을 찾을 수 없습니다")
#     return proba_col, label_col

# #------ 데이터 표출 영역-------
# df = load_from_db()
# proba_col, label_col = detect_score_cols(df)

# # 필터링 --> 사이드바에 배치
# with st.sidebar:
#     st.markdown("### 고객 정보 필터 ")
#     min_p, max_p = st.slider("예측 확률 범위", 0.0, 1.0, (0.0, 1.0), 0.01)
#     complain = st.multiselect("Complain 여부", sorted(df["Complain"].map({0: "No", 1: "Yes"}).unique()))
#     geos = st.multiselect("국가(Geography)", sorted(df["Geography"].unique()))
#     genders = st.multiselect("성별(Gender)", sorted(df["Gender"].unique()))
#     age_groups = st.multiselect(
#         "연령대 선택",
#         ["10대 (10-19)", "20대 (20-29)", "30대 (30-39)",
#          "40대 (40-49)", "50대 (50-59)", "60대 이상 (60+)"],
#         default=[]
#     )
#     credit_groups = st.multiselect(
#         "신용점수 등급",
#         ["Excellent (800-850)", "Very Good (740-799)", "Good (670-739)", "Fair (580-669)", "Poor (300-579)"],
#         default=[]
#     )

# keyword = st.text_input("검색(ID/성명)")

# base_cols = [c for c in ["CustomerId", "Complain", "Age", "Gender", "Geography", "CreditScore", "NumOfProducts"] if c in df.columns]
# list_cols = base_cols + [proba_col]
# list_df = df[list_cols].copy()

# rename_map = {
#     "CustomerId": "CustomerId",
#     "Complain": "Complain",          # 표시명 그대로 Complain (원하면 '불만' 등으로 바꾸세요)
#     "Age": "나이",
#     "Gender": "성별",
#     "Geography": "지역",
#     "CreditScore": "신용점수",
#     "NumOfProducts": "가입상품",
#     proba_col: "이탈률",
# }
# list_df.rename(columns={k: v for k, v in rename_map.items() if k in list_df.columns}, inplace=True)

# # 필터 적용
# list_df = list_df[(list_df["이탈률"] >= min_p) & (list_df["이탈률"] <= max_p)]

# # 연령대 필터
# if age_groups:
#     age_masks = []
#     for grp in age_groups:
#         if grp == "10대 (10-19)": age_masks.append(list_df["나이"].between(10, 19))
#         elif grp == "20대 (20-29)": age_masks.append(list_df["나이"].between(20, 29))
#         elif grp == "30대 (30-39)": age_masks.append(list_df["나이"].between(30, 39))
#         elif grp == "40대 (40-49)": age_masks.append(list_df["나이"].between(40, 49))
#         elif grp == "50대 (50-59)": age_masks.append(list_df["나이"].between(50, 59))
#         elif grp == "60대 이상 (60+)": age_masks.append(list_df["나이"] >= 60)
#     if age_masks:
#         list_df = list_df[pd.concat(age_masks, axis=1).any(axis=1)]

# # 신용점수 필터
# ranges = {
#     "Excellent (800-850)": (800, 850),
#     "Very Good (740-799)": (740, 799),
#     "Good (670-739)": (670, 739),
#     "Fair (580-669)": (580, 669),
#     "Poor (300-579)": (300, 579),
# }
# if credit_groups:
#     credit_masks = []
#     for grp in credit_groups:
#         lo, hi = ranges[grp]
#         credit_masks.append(list_df["신용점수"].between(lo, hi))
#     if credit_masks:
#         list_df = list_df[pd.concat(credit_masks, axis=1).any(axis=1)]

# # Complain 필터링
# if complain and "Complain" in list_df.columns:
#     comp_vals = [1 if c == "Yes" else 0 for c in complain]
#     list_df = list_df[list_df["Complain"].isin(comp_vals)]

# # 국가 / 성별
# if geos:
#     list_df = list_df[list_df["지역"].isin(geos)]
# if genders:
#     list_df = list_df[list_df["성별"].isin(genders)]

# # 검색어 필터링(성/ID)
# # --- 검색어 필터링 (성명은 df에서 검색, CustomerId는 list_df에서 직접 검색)
# if keyword:
#     kw = keyword.strip()
#     if kw:
#         mask = pd.Series(False, index=list_df.index)

#         # 1) CustomerId 검색 (list_df 자체에 존재)
#         if "CustomerId" in list_df.columns:
#             mask |= list_df["CustomerId"].astype(str).str.contains(kw, na=False, regex=False)

#         # 2) 성명 검색 (df에서 찾고, 해당 CustomerId만 필터링)
#         if "Surname" in df.columns:
#             matched_ids = df.loc[
#                 df["Surname"].astype(str).str.contains(kw, case=False, na=False, regex=False),
#                 "CustomerId"
#             ].astype(str).tolist()

#             if matched_ids:
#                 mask |= list_df["CustomerId"].astype(str).isin(matched_ids)

#         list_df = list_df[mask]

# # ---------- 마스터(리스트) & 선택 ----------
# st.subheader("고객 리스트")

# # 정렬
# sort_desc = st.toggle("확률 내림차순 정렬", value=True)
# list_df = list_df.sort_values("이탈률", ascending=not sort_desc)

# # 페이지 크기 + 전체 보기
# left, right = st.columns([1, 1])
# with left:
#     page_size = st.selectbox("페이지 크기", [25, 50, 100], index=1)
# with right:
#     show_all = st.toggle("전체 보기 (주의)", value=False)

# # 표시용 DF (행 매핑용 숨김 인덱스 추가)
# display_df = list_df.reset_index(drop=True).copy()
# if "_orig_idx" not in display_df.columns:
#     display_df.insert(0, "_orig_idx", display_df.index)

# # ---- AgGrid 옵션 구성
# gob = GridOptionsBuilder.from_dataframe(display_df)
# gob.configure_column(
#     "이탈률",
#     type=["numericColumn"],
#     valueFormatter="(value == null) ? '' : (value * 100).toFixed(2) + ' %'"
# )
# gob.configure_column(
#     "Complain",
#     valueFormatter="(value == 1) ? 'Yes' : (value == 0 ? 'No' : value)"
# )
# gob.configure_default_column(sortable=True, filter=True, resizable=True)
# gob.configure_selection(selection_mode="single", use_checkbox=False)
# if show_all:
#     gob.configure_grid_options(pagination=False)
#     gob.configure_pagination(enabled=False)
# else:
#     gob.configure_pagination(paginationAutoPageSize=False, paginationPageSize=page_size)
# gob.configure_column("_orig_idx", hide=True)
# grid_options = gob.build()

# grid_resp = AgGrid(
#     display_df,
#     gridOptions=grid_options,
#     height=600 if show_all else 420,
#     fit_columns_on_grid_load=True,
#     update_on=["selectionChanged"],
#     allow_unsafe_jscode=True,
#     enable_enterprise_modules=False,
#     key="customers_grid",
#     custom_css={
#         ".ag-cell-focus": {"border": "none !important", "outline": "none !important"},
#         ".ag-row-selected": {"background-color": "rgba(255, 99, 132, 0.12) !important"},
#     },
# )

# # 선택된 행
# selected_rows = grid_resp.get("selected_rows", [])
# if isinstance(selected_rows, pd.DataFrame):
#     selected_rows = selected_rows.to_dict("records")
# if selected_rows:
#     sel_row = selected_rows[0]
#     sel_id = str(sel_row.get("CustomerId", sel_row.get("_orig_idx", "")))
# else:
#     sel_id = None

# st.markdown("---")

# # ---------- 디테일(선택 고객 상세 + LLM 추천) ----------
# st.subheader("고객 상세")

# if not sel_id:
#     st.info("리스트에서 고객 행을 클릭하면 상세 정보가 여기에 표시됩니다.")
# else:
#     detail_row = None
#     if "CustomerId" in df.columns:
#         try:
#             cid = int(sel_id)
#             detail_row = df[df["CustomerId"] == cid].head(1)
#         except ValueError:
#             detail_row = df[df["CustomerId"].astype(str) == sel_id].head(1)

#     if detail_row is None or detail_row.empty:
#         st.warning("선택한 고객의 상세정보를 찾을 수 없습니다.")
#         st.stop()

#     # 기본 지표
#     proba_col, label_col = detect_score_cols(df)
#     score_val = float(detail_row[proba_col].values[0] * 100)
#     label_val = int(detail_row[label_col].values[0])

#     def v(col, default="N/A"):
#         return detail_row[col].values[0] if col in detail_row.columns else default

#     st.subheader(f"👤 고객 : {v('Surname')} ({v('CustomerId')})")
#     st.markdown(' ')
#     c1, c2 = st.columns(2)
#     c1.markdown(
#         f"""
#         <style>
#         .churn-score {{ margin-bottom:0.1rem; font-weight:600; }}
#         .churn-value {{ font-size:2rem; font-weight:700; margin-top:0; color: var(--text-color); }}
#         </style>
#         <div class='churn-score'>예측확률 (Churn)</div>
#         <div class='churn-value'>{score_val:.2f}%</div>
#         """,
#         unsafe_allow_html=True
#     )

#     color = "red" if label_val == 1 else "green"
#     label_txt = "이탈" if label_val == 1 else "유지"
#     c2.markdown(
#         f"""
#         <div style='margin-bottom:0.1rem; font-weight:600;'>예측라벨</div>
#         <div style='font-size:2rem; font-weight:700; color:{color}; margin-top:0;'>{label_txt}</div>
#         """, unsafe_allow_html=True
#     )

#     st.markdown('    ')
#     left_box, right_box = st.columns(2)
#     with left_box:
#         st.markdown("**프로필**")
#         prof = {}
#         for c in ["Geography", "Gender", "Age", "Tenure", "NumOfProducts", "HasCrCard", "IsActiveMember","Complain"]:
#             if c in df.columns:
#                 prof[c] = v(c)
#         # Arrow 타입 혼합 이슈 방지: 값 컬럼 문자열화
#         st.table(pd.DataFrame(prof.items(), columns=["항목", "값"]).astype({"값": "string"}))

#     with right_box:
#         st.markdown("**재무/점수**")
#         fin = {}
#         for c in ["CreditScore", "Balance", "EstimatedSalary"]:
#             if c in df.columns:
#                 fin[c] = v(c)
#         fin["predicted_proba"] = score_val
#         fin["predicted_label"] = label_val
#         st.table(pd.DataFrame(fin.items(), columns=["항목", "값"]).astype({"값": "string"}))

#     with st.expander("원본 레코드 전체 보기"):
#         st.dataframe(detail_row.T, width="stretch")

#     # ── LLM 추천 (래퍼 사용: 내부에서 키 없으면 자동 폴백)
#     st.subheader("🤖 추천 상품")

#     row_for_prompt = {
#         "CustomerId": v("CustomerId"),
#         "Surname": v("Surname"),
#         "Geography": v("Geography"),
#         "Gender": v("Gender"),
#         "Age": float(v("Age", 0) or 0),
#         "Tenure": float(v("Tenure", 0) or 0),
#         "Balance": float(v("Balance", 0) or 0),
#         "NumOfProducts": int(v("NumOfProducts", 0) or 0),
#         "HasCrCard": int(v("HasCrCard", 0) or 0),
#         "IsActiveMember": int(v("IsActiveMember", 0) or 0),
#         "EstimatedSalary": float(v("EstimatedSalary", 0) or 0),
#         "CreditScore": float(v("CreditScore", 0) or 0),
#         "churn_probability": float(detail_row[proba_col].values[0]),
#     }

#     if recommend_for_user is not None:
#         reco = recommend_for_user(row_for_prompt)
#     else:
#         reco = {"summary": "LLM 모듈이 없습니다.", "top_products": [], "next_actions": [], "risk_level": "N/A"}

#     # 렌더링
#     colA, colB = st.columns([1, 2])
#     with colA:
#         st.metric("위험도", reco.get("risk_level", "N/A"))
#     with colB:
#         st.info(reco.get("summary", "요약 없음"))

#     recs = reco.get("top_products", [])
#     if recs:
#         for r in recs:
#             code = r.get("code", "")
#             name = _PROD_MAP.get(code, {}).get("name", code)
#             reason = r.get("reason", "")
#             st.markdown(
#                 f"""
#                 <div style="border:1px solid #e5e7eb; border-radius:12px; padding:12px; margin-bottom:8px;">
#                   <div style="font-weight:700;">{name} <span style="opacity:.6">({code})</span></div>
#                   <div style="opacity:.85;">{reason}</div>
#                 </div>
#                 """,
#                 unsafe_allow_html=True,
#             )
#     else:
#         st.write("- (추천 없음)")

#     acts = reco.get("next_actions", [])
#     if acts:
#         st.markdown("**다음 액션**")
#         st.markdown("\n".join([f"- {a}" for a in acts]))

#     # 키가 없으면 가이드 표시(UX 방해 X)
#     if not os.getenv("OPENAI_API_KEY"):
#         st.caption("※ LLM 키가 없어 정책 기반 폴백으로 동작 중입니다. (.env: OPENAI_API_KEY)")

#-----------------------------------------------------------------------------------
# import os
# import streamlit as st
# import pandas as pd
# from pathlib import Path
# from pages.app_bootstrap import render_sidebar  # 필수
# from st_aggrid import AgGrid, GridOptionsBuilder  # 리스트 클릭 상호작용
# from dotenv import load_dotenv
# import pymysql

# # ───────────────────────────────────────────────────────────────
# # 페이지 전역 설정 (다크 고정 느낌의 스타일을 코드로 주입)
# st.set_page_config(
#     page_title="고객 이탈률",
#     page_icon="📊",
#     layout="wide",
# )

# # 전역 다크 스타일 (Streamlit 다크/라이트 무관하게 어두운 톤 유지)
# DARK_CSS = """
#     <style>
#     html, body, [data-testid="stAppViewContainer"] {
#         background-color: #0f1216 !important;
#         color: #e5e7eb !important;
#     }
#     [data-testid="stHeader"] { display: none; }
#     .erp-shell { padding: 8px 16px 20px; }
#     .erp-header {
#         background: linear-gradient(180deg, #171b22 0%, #12161b 100%);
#         border: 1px solid #262b33;
#         border-radius: 12px;
#         padding: 16px 18px;
#         margin-bottom: 16px;
#         box-shadow: 0 8px 20px rgba(0,0,0,.25);
#     }
#     .erp-title { margin: 0; font-weight: 700; font-size: 20px; color: #f3f4f6; }
#     .erp-sub { margin: 2px 0 0; font-size: 13px; color: #94a3b8; }

#     /* 사이드바 */
#     [data-testid="stSidebar"] {
#         background-color: #0b0e12 !important;
#         border-right: 1px solid #232832;
#     }
#     [data-testid="stSidebar"] .sidebar-title {
#         font-weight: 700; color:#cbd5e1; margin-bottom:8px; font-size:14px;
#     }
#     .sidebar-box {
#         background: #0f141a; border:1px solid #232832; border-radius:12px; padding:10px; margin-bottom:12px;
#     }
#     .sidebar-box .stMultiSelect > label, .sidebar-box .stSlider > label, .sidebar-box .stTextInput > label {
#         color:#94a3b8 !important;
#     }

#     /* 섹션 헤더/구분선 */
#     .section-title { font-weight:700; font-size:16px; margin: 6px 0 8px; color: #e2e8f0; }
#     .divider { height:1px; background: linear-gradient(90deg, transparent, #28303b, transparent); margin: 12px 0; }

#     /* 표/테이블 기본 색 보정 */
#     .stTable, .stDataFrame { filter: brightness(0.98); }

#     /* 버튼/토글 계열 색상 보정 */
#     .stToggle, .stSelectbox, .stSlider, .stTextInput { color: #e5e7eb !important; }

#     /* Ag-Grid 다크 룩 보정 */
#     .ag-theme-balham-dark {
#         --ag-background-color: #0f1216;
#         --ag-odd-row-background-color: #0c0f13;
#         --ag-header-background-color: #0c0f13;
#         --ag-border-color: #20232a;
#         --ag-foreground-color: #e5e7eb;
#         --ag-secondary-foreground-color: #cbd5e1;
#         --ag-row-hover-color: #12161b;
#         --ag-selected-row-background-color: rgba(56, 189, 248, 0.15);
#     }
#     .ag-theme-balham-dark .ag-root-wrapper { border-radius: 12px; border:1px solid #232832; }
#     .ag-theme-balham-dark .ag-header-cell-label { justify-content: center; }
#     .ag-theme-balham-dark .ag-cell { font-size: 13px; padding: 6px 8px; }
#     .ag-theme-balham-dark .ag-row-selected { background-color: rgba(248, 113, 113, 0.15) !important; }

#     /* metric-like 수치 텍스트 */
#     .churn-score { margin-bottom:0.1rem; font-weight:600; color:#9ca3af; }
#     .churn-value { font-size:2rem; font-weight:800; margin-top:0; color:#f8fafc; }
#     </style>
# """

# st.markdown(DARK_CSS, unsafe_allow_html=True)

# # ───────────────────────────────────────────────────────────────
# # LLM 추천 래퍼 (키가 없거나 에러여도 내부 폴백으로 안전 동작)
# try:
#     from utils.llm.reco_templates import recommend_for_user, PRODUCT_CATALOG
#     _PROD_MAP = {p["code"]: p for p in PRODUCT_CATALOG}
# except Exception:
#     recommend_for_user = None
#     PRODUCT_CATALOG = []
#     _PROD_MAP = {}

# # ───────────────────────────────────────────────────────────────
# # 공통 UI
# render_sidebar()

# st.markdown(
#     """
#     <div class="erp-shell">
#       <div class="erp-header">
#         <h1 class="erp-title">📊 고객 이탈률</h1>
#         <p class="erp-sub">은행 ERP 스타일 — 리스트 선택 후 상세 정보를 확인하세요</p>
#       </div>
#     </div>
#     """,
#     unsafe_allow_html=True,
# )

# #------ 데이터 획득 영역-------
# load_dotenv()

# def _get_conn_tuple():
#     return pymysql.connect(
#         host=os.getenv("DB_HOST", "127.0.0.1"),
#         port=int(os.getenv("DB_PORT", "3306")),
#         user=os.getenv("DB_USER", "root"),
#         password=os.getenv("DB_PASS", "rootpass"),
#         database=os.getenv("DB_NAME", "sknproject2"),
#         charset="utf8mb4",
#         cursorclass=pymysql.cursors.Cursor,  # ✅ tuple cursor (중요)
#         autocommit=True,
#     )


# def read_df(sql: str, params=None) -> pd.DataFrame:
#     conn = _get_conn_tuple()
#     try:
#         return pd.read_sql(sql, conn, params=params)
#     finally:
#         conn.close()

# @st.cache_data(ttl=60)
# def load_from_db() -> pd.DataFrame:
#     sql = """
#     SELECT
#       b.CustomerId, b.Surname, b.CreditScore, b.Geography, b.Gender, b.Complain, 
#       b.Age, b.Tenure, b.Balance, b.NumOfProducts, b.HasCrCard, b.IsActiveMember,
#       b.EstimatedSalary, b.Exited,
#       s.churn_probability AS predicted_proba
#     FROM bank_customer b
#     LEFT JOIN stg_churn_score s
#       ON s.customer_id = b.CustomerId
#     """
#     df = read_df(sql)
#     # 예측 라벨 파생
#     if "predicted_proba" in df.columns:
#         df["predicted_exited"] = (df["predicted_proba"] >= 0.5).astype(int)
#     return df


# def detect_score_cols(df: pd.DataFrame) -> tuple[str, str]:
#     proba_candidates = ["predicted_proba_oof", "predicted_proba"]
#     label_candidates = ["predicted_exited_oof", "predicted_exited"]
#     proba_col = next((c for c in proba_candidates if c in df.columns), None)
#     label_col = next((c for c in label_candidates if c in df.columns), None)
#     if not proba_col or not label_col:
#         raise ValueError("예측 컬럼을 찾을 수 없습니다")
#     return proba_col, label_col

# #------ 데이터 표출 영역-------
# df = load_from_db()
# proba_col, label_col = detect_score_cols(df)

# # ───────── 사이드바 필터 (디자인만 조정) ─────────
# with st.sidebar:
#     st.markdown('<div class="sidebar-title">고객 정보 필터</div>', unsafe_allow_html=True)
#     with st.container(border=False):
#         st.markdown('<div class="sidebar-box">', unsafe_allow_html=True)
#         min_p, max_p = st.slider("예측 확률 범위", 0.0, 1.0, (0.0, 1.0), 0.01)
#         complain = st.multiselect("Complain 여부", sorted(df["Complain"].map({0: "No", 1: "Yes"}).unique()))
#         geos = st.multiselect("국가(Geography)", sorted(df["Geography"].unique()))
#         genders = st.multiselect("성별(Gender)", sorted(df["Gender"].unique()))
#         age_groups = st.multiselect(
#             "연령대 선택",
#             [
#                 "10대 (10-19)", "20대 (20-29)", "30대 (30-39)",
#                 "40대 (40-49)", "50대 (50-59)", "60대 이상 (60+)"
#             ],
#             default=[]
#         )
#         credit_groups = st.multiselect(
#             "신용점수 등급",
#             [
#                 "Excellent (800-850)", "Very Good (740-799)", "Good (670-739)",
#                 "Fair (580-669)", "Poor (300-579)"
#             ],
#             default=[]
#         )
#         st.markdown('</div>', unsafe_allow_html=True)

# keyword = st.text_input("검색(ID/성명)")

# base_cols = [c for c in ["CustomerId", "Complain", "Age", "Gender", "Geography", "CreditScore", "NumOfProducts"] if c in df.columns]
# list_cols = base_cols + [proba_col]
# list_df = df[list_cols].copy()

# rename_map = {
#     "CustomerId": "CustomerId",
#     "Complain": "Complain",          # 표시명 그대로 유지
#     "Age": "나이",
#     "Gender": "성별",
#     "Geography": "지역",
#     "CreditScore": "신용점수",
#     "NumOfProducts": "가입상품",
#     proba_col: "이탈률",
# }
# list_df.rename(columns={k: v for k, v in rename_map.items() if k in list_df.columns}, inplace=True)

# # 필터 적용
# list_df = list_df[(list_df["이탈률"] >= min_p) & (list_df["이탈률"] <= max_p)]

# # 연령대 필터
# if age_groups:
#     age_masks = []
#     for grp in age_groups:
#         if grp == "10대 (10-19)": age_masks.append(list_df["나이"].between(10, 19))
#         elif grp == "20대 (20-29)": age_masks.append(list_df["나이"].between(20, 29))
#         elif grp == "30대 (30-39)": age_masks.append(list_df["나이"].between(30, 39))
#         elif grp == "40대 (40-49)": age_masks.append(list_df["나이"].between(40, 49))
#         elif grp == "50대 (50-59)": age_masks.append(list_df["나이"].between(50, 59))
#         elif grp == "60대 이상 (60+)": age_masks.append(list_df["나이"] >= 60)
#     if age_masks:
#         list_df = list_df[pd.concat(age_masks, axis=1).any(axis=1)]

# # 신용점수 필터
# ranges = {
#     "Excellent (800-850)": (800, 850),
#     "Very Good (740-799)": (740, 799),
#     "Good (670-739)": (670, 739),
#     "Fair (580-669)": (580, 669),
#     "Poor (300-579)": (300, 579),
# }
# if credit_groups:
#     credit_masks = []
#     for grp in credit_groups:
#         lo, hi = ranges[grp]
#         credit_masks.append(list_df["신용점수"].between(lo, hi))
#     if credit_masks:
#         list_df = list_df[pd.concat(credit_masks, axis=1).any(axis=1)]

# # Complain 필터링
# if complain and "Complain" in list_df.columns:
#     comp_vals = [1 if c == "Yes" else 0 for c in complain]
#     list_df = list_df[list_df["Complain"].isin(comp_vals)]

# # 국가 / 성별
# if geos:
#     list_df = list_df[list_df["지역"].isin(geos)]
# if genders:
#     list_df = list_df[list_df["성별"].isin(genders)]

# # 검색어 필터링(성/ID)
# if keyword:
#     kw = keyword.strip()
#     if kw:
#         mask = pd.Series(False, index=list_df.index)
#         if "CustomerId" in list_df.columns:
#             mask |= list_df["CustomerId"].astype(str).str.contains(kw, na=False, regex=False)
#         if "Surname" in df.columns:
#             matched_ids = df.loc[
#                 df["Surname"].astype(str).str.contains(kw, case=False, na=False, regex=False),
#                 "CustomerId"
#             ].astype(str).tolist()
#             if matched_ids:
#                 mask |= list_df["CustomerId"].astype(str).isin(matched_ids)
#         list_df = list_df[mask]

# # ---------- 마스터(리스트) & 선택 ----------
# st.markdown('<div class="section-title">고객 리스트</div>', unsafe_allow_html=True)

# # 정렬
# sort_desc = st.toggle("확률 내림차순 정렬", value=True)
# list_df = list_df.sort_values("이탈률", ascending=not sort_desc)

# # 페이지 크기 + 전체 보기
# left, right = st.columns([1, 1])
# with left:
#     page_size = st.selectbox("페이지 크기", [25, 50, 100], index=1)
# with right:
#     show_all = st.toggle("전체 보기 (주의)", value=False)

# # 표시용 DF (행 매핑용 숨김 인덱스 추가)
# display_df = list_df.reset_index(drop=True).copy()
# if "_orig_idx" not in display_df.columns:
#     display_df.insert(0, "_orig_idx", display_df.index)

# # ---- AgGrid 옵션 구성 (다크 테마 적용)
# gob = GridOptionsBuilder.from_dataframe(display_df)
# gob.configure_column(
#     "이탈률",
#     type=["numericColumn"],
#     valueFormatter="(value == null) ? '' : (value * 100).toFixed(2) + ' %'"
# )
# gob.configure_column(
#     "Complain",
#     valueFormatter="(value == 1) ? 'Yes' : (value == 0 ? 'No' : value)"
# )
# gob.configure_default_column(sortable=True, filter=True, resizable=True)
# gob.configure_selection(selection_mode="single", use_checkbox=False)
# if show_all:
#     gob.configure_grid_options(pagination=False)
#     gob.configure_pagination(enabled=False)
# else:
#     gob.configure_pagination(paginationAutoPageSize=False, paginationPageSize=page_size)
# gob.configure_column("_orig_idx", hide=True)
# grid_options = gob.build()

# grid_resp = AgGrid(
#     display_df,
#     gridOptions=grid_options,
#     height=600 if show_all else 420,
#     fit_columns_on_grid_load=True,
#     update_on=["selectionChanged"],
#     allow_unsafe_jscode=True,
#     enable_enterprise_modules=False,
#     key="customers_grid",
#     theme="balham-dark",
#     custom_css={
#         ".ag-cell-focus": {"border": "none !important", "outline": "none !important"},
#         ".ag-row-hover": {"background-color": "#0f141a !important"},
#         ".ag-row-selected": {"background-color": "rgba(248,113,113,0.15) !important"},
#     },
# )

# # 선택된 행
# selected_rows = grid_resp.get("selected_rows", [])
# if isinstance(selected_rows, pd.DataFrame):
#     selected_rows = selected_rows.to_dict("records")
# if selected_rows:
#     sel_row = selected_rows[0]
#     sel_id = str(sel_row.get("CustomerId", sel_row.get("_orig_idx", "")))
# else:
#     sel_id = None

# st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# # ---------- 디테일(선택 고객 상세 + LLM 추천) ----------
# st.markdown('<div class="section-title">고객 상세</div>', unsafe_allow_html=True)

# if not sel_id:
#     st.info("리스트에서 고객 행을 클릭하면 상세 정보가 여기에 표시됩니다.")
# else:
#     detail_row = None
#     if "CustomerId" in df.columns:
#         try:
#             cid = int(sel_id)
#             detail_row = df[df["CustomerId"] == cid].head(1)
#         except ValueError:
#             detail_row = df[df["CustomerId"].astype(str) == sel_id].head(1)

#     if detail_row is None or detail_row.empty:
#         st.warning("선택한 고객의 상세정보를 찾을 수 없습니다.")
#         st.stop()

#     # 기본 지표
#     proba_col, label_col = detect_score_cols(df)
#     score_val = float(detail_row[proba_col].values[0] * 100)
#     label_val = int(detail_row[label_col].values[0])

#     def v(col, default="N/A"):
#         return detail_row[col].values[0] if col in detail_row.columns else default

#     st.subheader(f"👤 고객 : {v('Surname')} ({v('CustomerId')})")
#     st.markdown(' ')
#     c1, c2 = st.columns(2)
#     c1.markdown(
#         f"""
#         <div class='churn-score'>예측확률 (Churn)</div>
#         <div class='churn-value'>{score_val:.2f}%</div>
#         """,
#         unsafe_allow_html=True
#     )

#     color = "#ef4444" if label_val == 1 else "#22c55e"
#     label_txt = "이탈" if label_val == 1 else "유지"
#     c2.markdown(
#         f"""
#         <div style='margin-bottom:0.1rem; font-weight:600; color:#9ca3af;'>예측라벨</div>
#         <div style='font-size:2rem; font-weight:800; color:{color}; margin-top:0;'>{label_txt}</div>
#         """, unsafe_allow_html=True
#     )

#     st.markdown('    ')
#     left_box, right_box = st.columns(2)
#     with left_box:
#         st.markdown("**프로필**")
#         prof = {}
#         for c in ["Geography", "Gender", "Age", "Tenure", "NumOfProducts", "HasCrCard", "IsActiveMember","Complain"]:
#             if c in df.columns:
#                 prof[c] = v(c)
#         st.table(pd.DataFrame(prof.items(), columns=["항목", "값"]).astype({"값": "string"}))

#     with right_box:
#         st.markdown("**재무/점수**")
#         fin = {}
#         for c in ["CreditScore", "Balance", "EstimatedSalary"]:
#             if c in df.columns:
#                 fin[c] = v(c)
#         fin["predicted_proba"] = score_val
#         fin["predicted_label"] = label_val
#         st.table(pd.DataFrame(fin.items(), columns=["항목", "값"]).astype({"값": "string"}))

#     with st.expander("원본 레코드 전체 보기"):
#         st.dataframe(detail_row.T, use_container_width=True)

#     # ── LLM 추천 (래퍼 사용: 내부에서 키 없으면 자동 폴백)
#     st.subheader("🤖 추천 상품")

#     row_for_prompt = {
#         "CustomerId": v("CustomerId"),
#         "Surname": v("Surname"),
#         "Geography": v("Geography"),
#         "Gender": v("Gender"),
#         "Age": float(v("Age", 0) or 0),
#         "Tenure": float(v("Tenure", 0) or 0),
#         "Balance": float(v("Balance", 0) or 0),
#         "NumOfProducts": int(v("NumOfProducts", 0) or 0),
#         "HasCrCard": int(v("HasCrCard", 0) or 0),
#         "IsActiveMember": int(v("IsActiveMember", 0) or 0),
#         "EstimatedSalary": float(v("EstimatedSalary", 0) or 0),
#         "CreditScore": float(v("CreditScore", 0) or 0),
#         "churn_probability": float(detail_row[proba_col].values[0]),
#     }

#     if recommend_for_user is not None:
#         reco = recommend_for_user(row_for_prompt)
#     else:
#         reco = {"summary": "LLM 모듈이 없습니다.", "top_products": [], "next_actions": [], "risk_level": "N/A"}

#     colA, colB = st.columns([1, 2])
#     with colA:
#         st.metric("위험도", reco.get("risk_level", "N/A"))
#     with colB:
#         st.info(reco.get("summary", "요약 없음"))

#     recs = reco.get("top_products", [])
#     if recs:
#         for r in recs:
#             code = r.get("code", "")
#             name = _PROD_MAP.get(code, {}).get("name", code)
#             reason = r.get("reason", "")
#             st.markdown(
#                 f"""
#                 <div style="border:1px solid #232832; background:#0f141a; border-radius:12px; padding:12px; margin-bottom:8px;">
#                   <div style="font-weight:700; color:#e5e7eb;">{name} <span style="opacity:.6">({code})</span></div>
#                   <div style="opacity:.85; color:#cbd5e1;">{reason}</div>
#                 </div>
#                 """,
#                 unsafe_allow_html=True,
#             )
#     else:
#         st.write("- (추천 없음)")

#     acts = reco.get("next_actions", [])
#     if acts:
#         st.markdown("**다음 액션**")
#         st.markdown("\n".join([f"- {a}" for a in acts]))

#     if not os.getenv("OPENAI_API_KEY"):
#         st.caption("※ LLM 키가 없어 정책 기반 폴백으로 동작 중입니다. (.env: OPENAI_API_KEY)")
#---------------------------------------------------------------------------
# import os
# import streamlit as st
# import pandas as pd
# from pages.app_bootstrap import render_sidebar  # 필수
# from st_aggrid import AgGrid, GridOptionsBuilder  # 리스트 클릭 상호작용
# from dotenv import load_dotenv
# import pymysql

# # ───────────────────────────────────────────────────────────────
# # 페이지 전역 설정 (다크 고정 느낌의 스타일을 코드로 주입)
# st.set_page_config(
#     page_title="고객 이탈률",
#     page_icon="📊",
#     layout="wide",
# )

# # 전역 다크 스타일 (Streamlit 다크/라이트 무관하게 어두운 톤 유지)
# DARK_CSS = """
#     <style>
#     html, body, [data-testid=\"stAppViewContainer\"] {
#         background-color: #0f1216 !important;
#         color: #e5e7eb !important;
#     }
#     [data-testid=\"stHeader\"] { display: none; }
#     .erp-shell { padding: 8px 16px 20px; }

#     /* ─── 상단 네비게이션 바 (이전 버전 유지) ─── */
#     .erp-topbar { display:flex; align-items:center; gap:12px; background:#0b0f14; border:1px solid #232832; border-radius:12px; padding:10px 14px; margin-bottom:12px; }
#     .erp-brand { font-weight:800; color:#e5e7eb; letter-spacing:.3px; }
#     .erp-breadcrumb { color:#9aa4b2; font-size:12.5px; }
#     .erp-breadcrumb .sep { opacity:.45; padding:0 6px; }
#     .erp-actions { margin-left:auto; display:flex; gap:8px; }
#     .erp-btn { padding:6px 10px; font-size:12.5px; border:1px solid #2a303a; border-radius:8px; background:#0f141a; color:#cbd5e1; }
#     .erp-btn:disabled { opacity:.5; cursor:not-allowed; }

#     /* 헤더 카드 (선호하신 심플 버전 유지) */
#     .erp-header {
#         background: linear-gradient(180deg, #171b22 0%, #12161b 100%);
#         border: 1px solid #262b33;
#         border-radius: 12px;
#         padding: 16px 18px;
#         margin-bottom: 16px;
#         box-shadow: 0 8px 20px rgba(0,0,0,.25);
#     }
#     .erp-title { margin: 0; font-weight: 700; font-size: 20px; color: #f3f4f6; }
#     .erp-sub { margin: 2px 0 0; font-size: 13px; color: #94a3b8; }

#     /* 사이드바 */
#     [data-testid=\"stSidebar\"] { background-color: #0b0e12 !important; border-right: 1px solid #232832; }
#     [data-testid=\"stSidebar\"] .sidebar-title { font-weight: 700; color:#cbd5e1; margin-bottom:8px; font-size:14px; }
#     .sidebar-box { background: #0f141a; border:1px solid #232832; border-radius:12px; padding:10px; margin-bottom:12px; }
#     .sidebar-box .stMultiSelect > label, .sidebar-box .stSlider > label, .sidebar-box .stTextInput > label { color:#94a3b8 !important; }

#     /* 섹션 헤더/구분선 */
#     .section-title { font-weight:700; font-size:16px; margin: 6px 0 8px; color: #e2e8f0; }
#     .divider { height:1px; background: linear-gradient(90deg, transparent, #28303b, transparent); margin: 12px 0; }

#     /* 표/테이블 기본 색 보정 */
#     .stTable, .stDataFrame { filter: brightness(0.98); }

#     /* Ag-Grid 다크 룩 보정 */
#     .ag-theme-balham-dark {
#         --ag-background-color: #0f1216;
#         --ag-odd-row-background-color: #0c0f13;
#         --ag-header-background-color: #0c0f13;
#         --ag-border-color: #20232a;
#         --ag-foreground-color: #e5e7eb;
#         --ag-secondary-foreground-color: #cbd5e1;
#         --ag-row-hover-color: #12161b;
#         --ag-selected-row-background-color: rgba(56, 189, 248, 0.15);
#     }
#     .ag-theme-balham-dark .ag-root-wrapper { border-radius: 12px; border:1px solid #232832; }
#     .ag-theme-balham-dark .ag-header-cell-label { justify-content: center; }
#     .ag-theme-balham-dark .ag-cell { font-size: 13px; padding: 6px 8px; }
#     .ag-theme-balham-dark .ag-row-selected { background-color: rgba(248, 113, 113, 0.15) !important; }

#     /* metric-like 수치 텍스트 */
#     .churn-score { margin-bottom:0.1rem; font-weight:600; color:#9ca3af; }
#     .churn-value { font-size:2rem; font-weight:800; margin-top:0; color:#f8fafc; }

#     /* ─── 추천 섹션 커스텀 (디자인만 변경) ─── */
#     .reco-row { display:grid; grid-template-columns: 200px 1fr; gap:12px; align-items:center; margin: 10px 0 14px; }
#     .risk-badge { background:#12161b; border:1px solid #263042; border-radius:12px; padding:16px; text-align:center; }
#     .risk-title { font-size:12px; color:#93a4b8; margin:0 0 2px; font-weight:600; letter-spacing:.4px; }
#     .risk-pill { font-size:28px; font-weight:800; margin:0; }
#     .risk-pill.red { color:#ef4444; }
#     .risk-pill.orange { color:#f59e0b; }
#     .risk-pill.green { color:#22c55e; }
#     .summary-box { background:#0f1b27; border:1px solid #1f2a38; border-radius:12px; padding:14px 16px; color:#cfe0f4; }

#     .reco-card { display:flex; gap:12px; align-items:flex-start; background:#0f141a; border:1px solid #232832; border-radius:12px; padding:12px 14px; margin-bottom:10px; transition: background .15s ease, border-color .15s ease; }
#     .reco-card:hover { background:#11171e; border-color:#2b3542; }
#     .reco-icon { width:28px; height:28px; border-radius:8px; background:#111922; border:1px solid #243044; display:flex; align-items:center; justify-content:center; font-size:14px; opacity:.85; }
#     .reco-main { flex:1; }
#     .reco-name { font-weight:700; color:#e5e7eb; }
#     .reco-code { display:inline-block; margin-left:6px; padding:2px 6px; font-size:11px; border:1px solid #2a3545; color:#9fb2cc; border-radius:999px; }
#     .reco-reason { color:#cbd5e1; opacity:.9; margin-top:4px; }

#     .reco-actions { margin-top:10px; }
#     .reco-actions h4 { margin:0 0 6px; font-size:13px; color:#e5e7eb; }
#     .reco-actions ul { margin:0; padding-left:18px; }
#     .reco-actions li { margin:4px 0; color:#cbd5e1; }
#     </style>
# """

# st.markdown(DARK_CSS, unsafe_allow_html=True)

# # ───────────────────────────────────────────────────────────────
# # LLM 추천 래퍼 (키가 없거나 에러여도 내부 폴백으로 안전 동작)
# try:
#     from utils.llm.reco_templates import recommend_for_user, PRODUCT_CATALOG
#     _PROD_MAP = {p["code"]: p for p in PRODUCT_CATALOG}
# except Exception:
#     recommend_for_user = None
#     PRODUCT_CATALOG = []
#     _PROD_MAP = {}

# # ───────────────────────────────────────────────────────────────
# # 공통 UI
# render_sidebar()

# st.markdown(
#     """
#     <div class=\"erp-shell\">
#       <div class=\"erp-topbar\">
#         <div class=\"erp-brand\">🏦 Bank ERP</div>
#         <div class=\"erp-breadcrumb\">고객관리 <span class=\"sep\">/</span> 이탈 관리</div>
#         <div class=\"erp-actions\">
#           <button class=\"erp-btn\" disabled>새로고침</button>
#           <button class=\"erp-btn\" disabled>설정</button>
#         </div>
#       </div>
#       <div class=\"erp-header\">
#         <h1 class=\"erp-title\">📊 고객 이탈률</h1>
#         <p class=\"erp-sub\">은행 ERP 스타일 — 리스트 선택 후 상세 정보를 확인하세요</p>
#       </div>
#     </div>
#     """,
#     unsafe_allow_html=True,
# )

# #------ 데이터 획득 영역-------
# load_dotenv()

# def _get_conn_tuple():
#     return pymysql.connect(
#         host=os.getenv("DB_HOST", "127.0.0.1"),
#         port=int(os.getenv("DB_PORT", "3306")),
#         user=os.getenv("DB_USER", "root"),
#         password=os.getenv("DB_PASS", "rootpass"),
#         database=os.getenv("DB_NAME", "sknproject2"),
#         charset="utf8mb4",
#         cursorclass=pymysql.cursors.Cursor,  # ✅ tuple cursor (중요)
#         autocommit=True,
#     )


# def read_df(sql: str, params=None) -> pd.DataFrame:
#     conn = _get_conn_tuple()
#     try:
#         return pd.read_sql(sql, conn, params=params)
#     finally:
#         conn.close()

# @st.cache_data(ttl=60)
# def load_from_db() -> pd.DataFrame:
#     sql = """
#     SELECT
#       b.CustomerId, b.Surname, b.CreditScore, b.Geography, b.Gender, b.Complain, 
#       b.Age, b.Tenure, b.Balance, b.NumOfProducts, b.HasCrCard, b.IsActiveMember,
#       b.EstimatedSalary, b.Exited,
#       s.churn_probability AS predicted_proba
#     FROM bank_customer b
#     LEFT JOIN stg_churn_score s
#       ON s.customer_id = b.CustomerId
#     """
#     df = read_df(sql)
#     # 예측 라벨 파생
#     if "predicted_proba" in df.columns:
#         df["predicted_exited"] = (df["predicted_proba"] >= 0.5).astype(int)
#     return df


# def detect_score_cols(df: pd.DataFrame) -> tuple[str, str]:
#     proba_candidates = ["predicted_proba_oof", "predicted_proba"]
#     label_candidates = ["predicted_exited_oof", "predicted_exited"]
#     proba_col = next((c for c in proba_candidates if c in df.columns), None)
#     label_col = next((c for c in label_candidates if c in df.columns), None)
#     if not proba_col or not label_col:
#         raise ValueError("예측 컬럼을 찾을 수 없습니다")
#     return proba_col, label_col

# #------ 데이터 표출 영역-------
# df = load_from_db()
# proba_col, label_col = detect_score_cols(df)

# # ───────── 사이드바 필터 (디자인만 조정) ─────────
# with st.sidebar:
#     st.markdown('<div class="sidebar-title">고객 정보 필터</div>', unsafe_allow_html=True)
#     with st.container(border=False):
#         st.markdown('<div class="sidebar-box">', unsafe_allow_html=True)
#         min_p, max_p = st.slider("예측 확률 범위", 0.0, 1.0, (0.0, 1.0), 0.01)
#         complain = st.multiselect("Complain 여부", sorted(df["Complain"].map({0: "No", 1: "Yes"}).unique()))
#         geos = st.multiselect("국가(Geography)", sorted(df["Geography"].unique()))
#         genders = st.multiselect("성별(Gender)", sorted(df["Gender"].unique()))
#         age_groups = st.multiselect(
#             "연령대 선택",
#             [
#                 "10대 (10-19)", "20대 (20-29)", "30대 (30-39)",
#                 "40대 (40-49)", "50대 (50-59)", "60대 이상 (60+)"
#             ],
#             default=[]
#         )
#         credit_groups = st.multiselect(
#             "신용점수 등급",
#             [
#                 "Excellent (800-850)", "Very Good (740-799)", "Good (670-739)",
#                 "Fair (580-669)", "Poor (300-579)"
#             ],
#             default=[]
#         )
#         st.markdown('</div>', unsafe_allow_html=True)

# keyword = st.text_input("검색(ID/성명)")

# base_cols = [c for c in ["CustomerId", "Complain", "Age", "Gender", "Geography", "CreditScore", "NumOfProducts"] if c in df.columns]
# list_cols = base_cols + [proba_col]
# list_df = df[list_cols].copy()

# rename_map = {
#     "CustomerId": "CustomerId",
#     "Complain": "Complain",          # 표시명 그대로 유지
#     "Age": "나이",
#     "Gender": "성별",
#     "Geography": "지역",
#     "CreditScore": "신용점수",
#     "NumOfProducts": "가입상품",
#     proba_col: "이탈률",
# }
# list_df.rename(columns={k: v for k, v in rename_map.items() if k in list_df.columns}, inplace=True)

# # 필터 적용
# list_df = list_df[(list_df["이탈률"] >= min_p) & (list_df["이탈률"] <= max_p)]

# # 연령대 필터
# if age_groups:
#     age_masks = []
#     for grp in age_groups:
#         if grp == "10대 (10-19)": age_masks.append(list_df["나이"].between(10, 19))
#         elif grp == "20대 (20-29)": age_masks.append(list_df["나이"].between(20, 29))
#         elif grp == "30대 (30-39)": age_masks.append(list_df["나이"].between(30, 39))
#         elif grp == "40대 (40-49)": age_masks.append(list_df["나이"].between(40, 49))
#         elif grp == "50대 (50-59)": age_masks.append(list_df["나이"].between(50, 59))
#         elif grp == "60대 이상 (60+)": age_masks.append(list_df["나이"] >= 60)
#     if age_masks:
#         list_df = list_df[pd.concat(age_masks, axis=1).any(axis=1)]

# # 신용점수 필터
# ranges = {
#     "Excellent (800-850)": (800, 850),
#     "Very Good (740-799)": (740, 799),
#     "Good (670-739)": (670, 739),
#     "Fair (580-669)": (580, 669),
#     "Poor (300-579)": (300, 579),
# }
# if credit_groups:
#     credit_masks = []
#     for grp in credit_groups:
#         lo, hi = ranges[grp]
#         credit_masks.append(list_df["신용점수"].between(lo, hi))
#     if credit_masks:
#         list_df = list_df[pd.concat(credit_masks, axis=1).any(axis=1)]

# # Complain 필터링
# if complain and "Complain" in list_df.columns:
#     comp_vals = [1 if c == "Yes" else 0 for c in complain]
#     list_df = list_df[list_df["Complain"].isin(comp_vals)]

# # 국가 / 성별
# if geos:
#     list_df = list_df[list_df["지역"].isin(geos)]
# if genders:
#     list_df = list_df[list_df["성별"].isin(genders)]

# # 검색어 필터링(성/ID)
# if keyword:
#     kw = keyword.strip()
#     if kw:
#         mask = pd.Series(False, index=list_df.index)
#         if "CustomerId" in list_df.columns:
#             mask |= list_df["CustomerId"].astype(str).str.contains(kw, na=False, regex=False)
#         if "Surname" in df.columns:
#             matched_ids = df.loc[
#                 df["Surname"].astype(str).str.contains(kw, case=False, na=False, regex=False),
#                 "CustomerId"
#             ].astype(str).tolist()
#             if matched_ids:
#                 mask |= list_df["CustomerId"].astype(str).isin(matched_ids)
#         list_df = list_df[mask]

# # ---------- 마스터(리스트) & 선택 ----------
# st.markdown('<div class="section-title">고객 리스트</div>', unsafe_allow_html=True)

# # 정렬
# sort_desc = st.toggle("확률 내림차순 정렬", value=True)
# list_df = list_df.sort_values("이탈률", ascending=not sort_desc)

# # 페이지 크기 + 전체 보기
# left, right = st.columns([1, 1])
# with left:
#     page_size = st.selectbox("페이지 크기", [25, 50, 100], index=1)
# with right:
#     show_all = st.toggle("전체 보기 (주의)", value=False)

# # 표시용 DF (행 매핑용 숨김 인덱스 추가)
# display_df = list_df.reset_index(drop=True).copy()
# if "_orig_idx" not in display_df.columns:
#     display_df.insert(0, "_orig_idx", display_df.index)

# # ---- AgGrid 옵션 구성 (다크 테마 적용)
# gob = GridOptionsBuilder.from_dataframe(display_df)
# gob.configure_column(
#     "이탈률",
#     type=["numericColumn"],
#     valueFormatter="(value == null) ? '' : (value * 100).toFixed(2) + ' %'"
# )
# gob.configure_column(
#     "Complain",
#     valueFormatter="(value == 1) ? 'Yes' : (value == 0 ? 'No' : value)"
# )
# gob.configure_default_column(sortable=True, filter=True, resizable=True)
# gob.configure_selection(selection_mode="single", use_checkbox=False)
# if show_all:
#     gob.configure_grid_options(pagination=False)
#     gob.configure_pagination(enabled=False)
# else:
#     gob.configure_pagination(paginationAutoPageSize=False, paginationPageSize=page_size)

# gob.configure_column("_orig_idx", hide=True)

# grid_options = gob.build()

# grid_resp = AgGrid(
#     display_df,
#     gridOptions=grid_options,
#     height=600 if show_all else 420,
#     fit_columns_on_grid_load=True,
#     update_on=["selectionChanged"],
#     allow_unsafe_jscode=True,
#     enable_enterprise_modules=False,
#     key="customers_grid",
#     theme="balham-dark",
#     custom_css={
#         ".ag-cell-focus": {"border": "none !important", "outline": "none !important"},
#         ".ag-row-hover": {"background-color": "#0f141a !important"},
#         ".ag-row-selected": {"background-color": "rgba(248,113,113,0.15) !important"},
#     },
# )

# # 선택된 행
# selected_rows = grid_resp.get("selected_rows", [])
# if isinstance(selected_rows, pd.DataFrame):
#     selected_rows = selected_rows.to_dict("records")
# if selected_rows:
#     sel_row = selected_rows[0]
#     sel_id = str(sel_row.get("CustomerId", sel_row.get("_orig_idx", "")))
# else:
#     sel_id = None

# st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# # ---------- 디테일(선택 고객 상세 + LLM 추천) ----------
# st.markdown('<div class="section-title">고객 상세</div>', unsafe_allow_html=True)

# if not sel_id:
#     st.info("리스트에서 고객 행을 클릭하면 상세 정보가 여기에 표시됩니다.")
# else:
#     detail_row = None
#     if "CustomerId" in df.columns:
#         try:
#             cid = int(sel_id)
#             detail_row = df[df["CustomerId"] == cid].head(1)
#         except ValueError:
#             detail_row = df[df["CustomerId"].astype(str) == sel_id].head(1)

#     if detail_row is None or detail_row.empty:
#         st.warning("선택한 고객의 상세정보를 찾을 수 없습니다.")
#         st.stop()

#     # 기본 지표
#     proba_col, label_col = detect_score_cols(df)
#     score_val = float(detail_row[proba_col].values[0] * 100)
#     label_val = int(detail_row[label_col].values[0])

#     def v(col, default="N/A"):
#         return detail_row[col].values[0] if col in detail_row.columns else default

#     st.subheader(f"👤 고객 : {v('Surname')} ({v('CustomerId')})")
#     st.markdown(' ')
#     c1, c2 = st.columns(2)
#     c1.markdown(
#         f"""
#         <div class='churn-score'>예측확률 (Churn)</div>
#         <div class='churn-value'>{score_val:.2f}%</div>
#         """,
#         unsafe_allow_html=True
#     )

#     color = "#ef4444" if label_val == 1 else "#22c55e"
#     label_txt = "이탈" if label_val == 1 else "유지"
#     c2.markdown(
#         f"""
#         <div style='margin-bottom:0.1rem; font-weight:600; color:#9ca3af;'>예측라벨</div>
#         <div style='font-size:2rem; font-weight:800; color:{color}; margin-top:0;'>{label_txt}</div>
#         """, unsafe_allow_html=True
#     )

#     st.markdown('    ')
#     left_box, right_box = st.columns(2)
#     with left_box:
#         st.markdown("**프로필**")
#         prof = {}
#         for c in ["Geography", "Gender", "Age", "Tenure", "NumOfProducts", "HasCrCard", "IsActiveMember","Complain"]:
#             if c in df.columns:
#                 prof[c] = v(c)
#         st.table(pd.DataFrame(prof.items(), columns=["항목", "값"]).astype({"값": "string"}))

#     with right_box:
#         st.markdown("**재무/점수**")
#         fin = {}
#         for c in ["CreditScore", "Balance", "EstimatedSalary"]:
#             if c in df.columns:
#                 fin[c] = v(c)
#         fin["predicted_proba"] = score_val
#         fin["predicted_label"] = label_val
#         st.table(pd.DataFrame(fin.items(), columns=["항목", "값"]).astype({"값": "string"}))

#     with st.expander("원본 레코드 전체 보기"):
#         st.dataframe(detail_row.T, use_container_width=True)

#     # ── LLM 추천 (디자인만 변경) ───────────────────────────
#     st.subheader("🤖 추천 상품")

#     row_for_prompt = {
#         "CustomerId": v("CustomerId"),
#         "Surname": v("Surname"),
#         "Geography": v("Geography"),
#         "Gender": v("Gender"),
#         "Age": float(v("Age", 0) or 0),
#         "Tenure": float(v("Tenure", 0) or 0),
#         "Balance": float(v("Balance", 0) or 0),
#         "NumOfProducts": int(v("NumOfProducts", 0) or 0),
#         "HasCrCard": int(v("HasCrCard", 0) or 0),
#         "IsActiveMember": int(v("IsActiveMember", 0) or 0),
#         "EstimatedSalary": float(v("EstimatedSalary", 0) or 0),
#         "CreditScore": float(v("CreditScore", 0) or 0),
#         "churn_probability": float(detail_row[proba_col].values[0]),
#     }

#     if recommend_for_user is not None:
#         reco = recommend_for_user(row_for_prompt)
#     else:
#         reco = {"summary": "LLM 모듈이 없습니다.", "top_products": [], "next_actions": [], "risk_level": "N/A"}

#     risk_level = str(reco.get("risk_level", "N/A")).upper()
#     risk_class = "red" if risk_level == "HIGH" else ("orange" if risk_level in ("MEDIUM","MID") else ("green" if risk_level == "LOW" else ""))

#     # 위험도 + 요약 상단 박스
#     st.markdown(
#         f"""
#         <div class='reco-row'>
#           <div class='risk-badge'>
#             <div class='risk-title'>위험도</div>
#             <div class='risk-pill {risk_class}'>{risk_level}</div>
#           </div>
#           <div class='summary-box'>{reco.get('summary','요약 없음')}</div>
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )

#     # 추천 카드 렌더링 (디자인만 변경)
#     recs = reco.get("top_products", [])
#     if recs:
#         for r in recs:
#             code = r.get("code", "").strip()
#             name = _PROD_MAP.get(code, {}).get("name", code)
#             reason = r.get("reason", "")
#             st.markdown(
#                 f"""
#                 <div class='reco-card'>
#                   <div class='reco-icon'>💡</div>
#                   <div class='reco-main'>
#                     <div class='reco-name'>{name} <span class='reco-code'>{code}</span></div>
#                     <div class='reco-reason'>{reason}</div>
#                   </div>
#                 </div>
#                 """,
#                 unsafe_allow_html=True,
#             )
#     else:
#         st.write("- (추천 없음)")

#     # 다음 액션 (디자인만 변경)
#     acts = reco.get("next_actions", [])
#     if acts:
#         st.markdown(
#             """
#             <div class='reco-actions'>
#               <h4>다음 액션</h4>
#               <ul>
#             """,
#             unsafe_allow_html=True,
#         )
#         for a in acts:
#             st.markdown(f"<li>{a}</li>", unsafe_allow_html=True)
#         st.markdown("</ul></div>", unsafe_allow_html=True)

#     # 키 없음 안내 (동일)
#     if not os.getenv("OPENAI_API_KEY"):
#         st.caption("※ LLM 키가 없어 정책 기반 폴백으로 동작 중입니다. (.env: OPENAI_API_KEY)")
#-----------------------------------------------------------------------
# import os
# import streamlit as st
# import pandas as pd
# from pages.app_bootstrap import render_sidebar  # 필수
# from st_aggrid import AgGrid, GridOptionsBuilder  # 리스트 클릭 상호작용
# from dotenv import load_dotenv
# import pymysql

# # ───────────────────────────────────────────────────────────────
# # 페이지 전역 설정 (다크 고정 느낌의 스타일을 코드로 주입)
# st.set_page_config(
#     page_title="고객 이탈률",
#     page_icon="📊",
#     layout="wide",
# )

# # 전역 다크 스타일 (Streamlit 다크/라이트 무관하게 어두운 톤 유지)
# DARK_CSS = """
#     <style>
#     html, body, [data-testid=\"stAppViewContainer\"] { background-color: #0f1216 !important; color: #e5e7eb !important; }
#     [data-testid=\"stHeader\"] { display: none; }
#     .erp-shell { padding: 8px 16px 20px; }

#     /* ─── 상단 네비게이션 바 (유지) ─── */
#     .erp-topbar { display:flex; align-items:center; gap:12px; background:#0b0f14; border:1px solid #232832; border-radius:12px; padding:10px 14px; margin-bottom:12px; }
#     .erp-brand { font-weight:800; color:#e5e7eb; letter-spacing:.3px; }
#     .erp-breadcrumb { color:#9aa4b2; font-size:12.5px; }
#     .erp-breadcrumb .sep { opacity:.45; padding:0 6px; }
#     .erp-actions { margin-left:auto; display:flex; gap:8px; }
#     .erp-btn { padding:6px 10px; font-size:12.5px; border:1px solid #2a303a; border-radius:8px; background:#0f141a; color:#cbd5e1; }
#     .erp-btn:disabled { opacity:.5; cursor:not-allowed; }

#     /* 헤더 카드 */
#     .erp-header { background: linear-gradient(180deg, #171b22 0%, #12161b 100%); border: 1px solid #262b33; border-radius: 12px; padding: 16px 18px; margin-bottom: 16px; box-shadow: 0 8px 20px rgba(0,0,0,.25); }
#     .erp-title { margin: 0; font-weight: 700; font-size: 20px; color: #f3f4f6; }
#     .erp-sub { margin: 2px 0 0; font-size: 13px; color: #94a3b8; }

#     /* 사이드바 */
#     [data-testid=\"stSidebar\"] { background-color: #0b0e12 !important; border-right: 1px solid #232832; }
#     [data-testid=\"stSidebar\"] .sidebar-title { font-weight: 700; color:#cbd5e1; margin-bottom:8px; font-size:14px; }
#     .sidebar-box { background: #0f141a; border:1px solid #232832; border-radius:12px; padding:10px; margin-bottom:12px; }
#     .sidebar-box .stMultiSelect > label, .sidebar-box .stSlider > label, .sidebar-box .stTextInput > label { color:#94a3b8 !important; }

#     /* 섹션 헤더/구분선 */
#     .section-title { font-weight:700; font-size:16px; margin: 6px 0 8px; color: #e2e8f0; }
#     .divider { height:1px; background: linear-gradient(90deg, transparent, #28303b, transparent); margin: 12px 0; }

#     /* 표/테이블 */
#     .stTable, .stTable *, .stDataFrame, .stDataFrame * { color:#eaeef6 !important; }

#     /* Ag-Grid 다크 룩 보정 */
#     .ag-theme-balham-dark {
#         --ag-background-color: #0f1216;
#         --ag-odd-row-background-color: #0c0f13;
#         --ag-header-background-color: #0c0f13;
#         --ag-border-color: #20232a;
#         --ag-foreground-color: #e5e7eb;
#         --ag-secondary-foreground-color: #cbd5e1;
#         --ag-row-hover-color: rgba(40, 42, 45, 0.1); /* 호버 = 선택과 동일 /회색 변경경*/
#         --ag-selected-row-background-color: rgba(59,130,246,0.25);
#     }
#     .ag-theme-balham-dark .ag-root-wrapper { border-radius: 12px; border:1px solid #232832; }
#     .ag-theme-balham-dark .ag-header-cell-label { justify-content: center; }
#     .ag-theme-balham-dark .ag-cell { font-size: 13px; padding: 6px 8px; }
#     .ag-theme-balham-dark .ag-row-hover .ag-cell,
#     .ag-theme-balham-dark .ag-row-selected .ag-cell { color:#ffffff !important; }
#     .ag-theme-balham-dark .ag-cell-focus { border-color:#60a5fa !important; box-shadow: inset 0 0 0 1px #60a5fa; }

#     /* metric-like 수치 텍스트 */
#     .churn-score { margin-bottom:0.1rem; font-weight:600; color:#9ca3af; }
#     .churn-value { font-size:2rem; font-weight:800; margin-top:0; color:#f8fafc; }

#     /* ─── 추천 섹션 커스텀 (디자인만 변경) ─── */
#     .reco-row { display:grid; grid-template-columns: 200px 1fr; gap:12px; align-items:center; margin: 10px 0 14px; }
#     .risk-badge { background:#12161b; border:1px solid #263042; border-radius:12px; padding:16px; text-align:center; }
#     .risk-title { font-size:12px; color:#93a4b8; margin:0 0 2px; font-weight:600; letter-spacing:.4px; }
#     .risk-pill { font-size:28px; font-weight:800; margin:0; }
#     .risk-pill.red { color:#ef4444; }
#     .risk-pill.orange { color:#f59e0b; }
#     .risk-pill.green { color:#22c55e; }
#     .summary-box { background:#0f1b27; border:1px solid #1f2a38; border-radius:12px; padding:14px 16px; color:#cfe0f4; }

#     .reco-card { display:flex; gap:12px; align-items:flex-start; background:#0f141a; border:1px solid #232832; border-radius:12px; padding:12px 14px; margin-bottom:10px; transition: background .15s ease, border-color .15s ease; }
#     .reco-card:hover { background:#11171e; border-color:#2b3542; }
#     .reco-icon { width:28px; height:28px; border-radius:8px; background:#111922; border:1px solid #243044; display:flex; align-items:center; justify-content:center; font-size:14px; opacity:.85; }
#     .reco-main { flex:1; }
#     .reco-name { font-weight:700; color:#e5e7eb; }
#     .reco-code { display:inline-block; margin-left:6px; padding:2px 6px; font-size:11px; border:1px solid #2a3545; color:#9fb2cc; border-radius:999px; }
#     .reco-reason { color:#cbd5e1; opacity:.9; margin-top:4px; }

#     .reco-actions { margin-top:10px; }
#     .reco-actions h4 { margin:0 0 6px; font-size:13px; color:#e5e7eb; }
#     .reco-actions ul { margin:0; padding-left:18px; }
#     .reco-actions li { margin:4px 0; color:#cbd5e1; }
    
#     /* ─── Controls: Search / Page Size / Toggle in White ─── */
#     /* Text input (검색) */
#     div[data-testid="stTextInput"] input {
#         background:#ffffff !important; color:#111827 !important;
#         border:1px solid #d1d5db !important; border-radius:10px !important;
#     }
#     div[data-testid="stTextInput"] input:focus {
#         outline:none !important; border-color:#60a5fa !important;
#         box-shadow:0 0 0 3px rgba(96,165,250,.25) !important;
#     }

#     /* Selectbox (페이지 크기) */
#     div[data-testid="stSelectbox"] div[role="combobox"],
#     div[data-testid="stSelectbox"] input {
#         background:#ffffff !important; color:#111827 !important;
#         border:1px solid #d1d5db !important; border-radius:10px !important;
#     }
#     div[data-testid="stSelectbox"] div[role="combobox"]:focus-within {
#         border-color:#60a5fa !important; box-shadow:0 0 0 3px rgba(96,165,250,.25) !important;
#     }
#     div[data-testid="stSelectbox"] svg { color:#111827 !important; opacity:1 !important; }

#     /* Toggle (전체 보기) */
#     div[data-testid="stSwitch"] label { color:#ffffff !important; }
#     div[data-testid="stSwitch"] [role="switch"] {
#         background:#ffffff !important; border:1px solid #d1d5db !important;
#     }
#     div[data-testid="stSwitch"] [role="switch"][aria-checked="true"] { background:#e5e7eb !important; }

#     /* ─── Bottom info tables: stronger borders ─── */
#     .stTable { border:1.5px solid #3b4252 !important; border-radius:12px !important; }
#     .stTable table { border-collapse:separate !important; border-spacing:0 !important; }
#     .stTable th, .stTable td { border-bottom:1px solid #2e3440 !important; }

#     /* ─── Force labels (검색/페이지 크기/전체 보기) to pure white ─── */
#     div[data-testid="stTextInput"] label,
#     div[data-testid="stTextInput"] label *,
#     div[data-testid="stSelectbox"] label,
#     div[data-testid="stSelectbox"] label *,
#     div[data-testid="stSwitch"] label,
#     div[data-testid="stSwitch"] label *,
#     div[data-testid="stSwitch"] p,
#     div[data-testid="stSwitch"] span { color:#ffffff !important; opacity:1 !important; }

#     /* Bottom info tables: white borders for clear visibility */
#     .stTable { border:1.5px solid #ffffff !important; border-radius:12px !important; }
#     .stTable table { border-collapse:separate !important; border-spacing:0 !important; }
#     .stTable th, .stTable td { border-bottom:1px solid #ffffff !important; }

#     /* ─── Sidebar palette override (match BCMS screenshot) ─── */
#     [data-testid="stSidebar"] {
#         background:#1f232b !important; /* deeper grey */
#         border-right:1px solid #2c313a !important;
#         color:#ffffff !important;
#     }
#     [data-testid="stSidebar"] * { color:#ffffff !important; }
#     [data-testid="stSidebar"] a, [data-testid="stSidebar"] button { color:#ffffff !important; text-decoration:none !important; }
#     [data-testid="stSidebar"] a:hover { background:#3a3f49 !important; border-radius:12px; }
#     /* active/selected nav item */
#     [data-testid="stSidebar"] a[aria-current="page"],
#     [data-testid="stSidebar"] a.active,
#     [data-testid="stSidebar"] .is-active {
#         background:#454a56 !important; /* pill highlight */
#         border:1px solid #676e79 !important;
#         border-radius:12px !important;
#         color:#ffffff !important;
#     }
#     [data-testid="stSidebar"] hr { border-color:#2c313a !important; }
# </style>
# """

# st.markdown(DARK_CSS, unsafe_allow_html=True)

# # ───────────────────────────────────────────────────────────────
# # LLM 추천 래퍼 (키가 없거나 에러여도 내부 폴백으로 안전 동작)
# try:
#     from utils.llm.reco_templates import recommend_for_user, PRODUCT_CATALOG
#     _PROD_MAP = {p["code"]: p for p in PRODUCT_CATALOG}
# except Exception:
#     recommend_for_user = None
#     PRODUCT_CATALOG = []
#     _PROD_MAP = {}

# # ───────────────────────────────────────────────────────────────
# # 공통 UI
# render_sidebar()

# st.markdown(
#     """
#     <div class=\"erp-shell\">
#       <div class=\"erp-topbar\">
#         <div class=\"erp-brand\">🏦 Bank ERP</div>
#         <div class=\"erp-breadcrumb\">고객관리 <span class=\"sep\">/</span> 이탈 관리</div>
#         <div class=\"erp-actions\">
#           <button class=\"erp-btn\" disabled>새로고침</button>
#           <button class=\"erp-btn\" disabled>설정</button>
#         </div>
#       </div>
#       <div class=\"erp-header\">
#         <h1 class=\"erp-title\">📉 고객 이탈률</h1>
#         <p class=\"erp-sub\">은행 ERP 스타일 — 리스트 선택 후 상세 정보를 확인하세요</p>
#       </div>
#     </div>
#     """,
#     unsafe_allow_html=True,
# )

# #------ 데이터 획득 영역-------
# load_dotenv()

# def _get_conn_tuple():
#     return pymysql.connect(
#         host=os.getenv("DB_HOST", "127.0.0.1"),
#         port=int(os.getenv("DB_PORT", "3306")),
#         user=os.getenv("DB_USER", "root"),
#         password=os.getenv("DB_PASS", "rootpass"),
#         database=os.getenv("DB_NAME", "sknproject2"),
#         charset="utf8mb4",
#         cursorclass=pymysql.cursors.Cursor,
#         autocommit=True,
#     )


# def read_df(sql: str, params=None) -> pd.DataFrame:
#     conn = _get_conn_tuple()
#     try:
#         return pd.read_sql(sql, conn, params=params)
#     finally:
#         conn.close()

# @st.cache_data(ttl=60)
# def load_from_db() -> pd.DataFrame:
#     sql = """
#     SELECT
#       b.CustomerId, b.Surname, b.CreditScore, b.Geography, b.Gender, b.Complain, 
#       b.Age, b.Tenure, b.Balance, b.NumOfProducts, b.HasCrCard, b.IsActiveMember,
#       b.EstimatedSalary, b.Exited,
#       s.churn_probability AS predicted_proba
#     FROM bank_customer b
#     LEFT JOIN stg_churn_score s
#       ON s.customer_id = b.CustomerId
#     """
#     df = read_df(sql)
#     # 예측 라벨 파생
#     if "predicted_proba" in df.columns:
#         df["predicted_exited"] = (df["predicted_proba"] >= 0.5).astype(int)
#     return df


# def detect_score_cols(df: pd.DataFrame) -> tuple[str, str]:
#     proba_candidates = ["predicted_proba_oof", "predicted_proba"]
#     label_candidates = ["predicted_exited_oof", "predicted_exited"]
#     proba_col = next((c for c in proba_candidates if c in df.columns), None)
#     label_col = next((c for c in label_candidates if c in df.columns), None)
#     if not proba_col or not label_col:
#         raise ValueError("예측 컬럼을 찾을 수 없습니다")
#     return proba_col, label_col

# #------ 데이터 표출 영역-------
# df = load_from_db()
# proba_col, label_col = detect_score_cols(df)

# # ───────── 사이드바 필터 (디자인만 조정) ─────────
# with st.sidebar:
#     st.markdown('<div class="sidebar-title">고객 정보 필터</div>', unsafe_allow_html=True)
#     with st.container(border=False):
#         st.markdown('<div class="sidebar-box">', unsafe_allow_html=True)
#         min_p, max_p = st.slider("예측 확률 범위", 0.0, 1.0, (0.0, 1.0), 0.01)
#         complain = st.selectbox("Complain 여부", ["전체", "Yes", "No"], index=0)
#         geos = st.multiselect("국가(Geography)", sorted(df["Geography"].unique()))
#         genders  = st.selectbox("성별(Gender)", ["전체"] + sorted(df["Gender"].dropna().unique().tolist()), index=0)
#         age_groups = st.multiselect(
#             "연령대 선택",
#             [
#                 "10대 (10-19)", "20대 (20-29)", "30대 (30-39)",
#                 "40대 (40-49)", "50대 (50-59)", "60대 이상 (60+)"
#             ],
#             default=[]
#         )
#         credit_groups = st.multiselect(
#             "신용점수 등급",
#             [
#                 "Excellent (800-850)", "Very Good (740-799)", "Good (670-739)",
#                 "Fair (580-669)", "Poor (300-579)"
#             ],
#             default=[]
#         )
#         st.markdown('</div>', unsafe_allow_html=True)

# keyword = st.text_input("검색(ID/성명)")

# base_cols = [c for c in ["CustomerId", "Complain", "Age", "Gender", "Geography", "CreditScore", "NumOfProducts"] if c in df.columns]
# list_cols = base_cols + [proba_col]
# list_df = df[list_cols].copy()

# rename_map = {
#     "CustomerId": "CustomerId",
#     "Complain": "Complain",          # 표시명 그대로 유지
#     "Age": "나이",
#     "Gender": "성별",
#     "Geography": "지역",
#     "CreditScore": "신용점수",
#     "NumOfProducts": "가입상품",
#     proba_col: "이탈률",
# }
# list_df.rename(columns={k: v for k, v in rename_map.items() if k in list_df.columns}, inplace=True)

# # 필터 적용
# list_df = list_df[(list_df["이탈률"] >= min_p) & (list_df["이탈률"] <= max_p)]

# # 연령대 필터
# if age_groups:
#     age_masks = []
#     for grp in age_groups:
#         if grp == "10대 (10-19)": age_masks.append(list_df["나이"].between(10, 19))
#         elif grp == "20대 (20-29)": age_masks.append(list_df["나이"].between(20, 29))
#         elif grp == "30대 (30-39)": age_masks.append(list_df["나이"].between(30, 39))
#         elif grp == "40대 (40-49)": age_masks.append(list_df["나이"].between(40, 49))
#         elif grp == "50대 (50-59)": age_masks.append(list_df["나이"].between(50, 59))
#         elif grp == "60대 이상 (60+)": age_masks.append(list_df["나이"] >= 60)
#     if age_masks:
#         list_df = list_df[pd.concat(age_masks, axis=1).any(axis=1)]

# # 신용점수 필터
# ranges = {
#     "Excellent (800-850)": (800, 850),
#     "Very Good (740-799)": (740, 799),
#     "Good (670-739)": (670, 739),
#     "Fair (580-669)": (580, 669),
#     "Poor (300-579)": (300, 579),
# }
# if credit_groups:
#     credit_masks = []
#     for grp in credit_groups:
#         lo, hi = ranges[grp]
#         credit_masks.append(list_df["신용점수"].between(lo, hi))
#     if credit_masks:
#         list_df = list_df[pd.concat(credit_masks, axis=1).any(axis=1)]

# # Complain 필터링
# if "Complain" in list_df.columns and complain != "전체":
#     comp_val = 1 if complain == "Yes" else 0
#     list_df = list_df[list_df["Complain"] == comp_val]

# # 국가 / 성별
# if geos:
#     list_df = list_df[list_df["지역"].isin(geos)]

# if "성별" in list_df.columns and genders != "전체":
#     list_df = list_df[list_df["성별"] == genders]

# # 검색어 필터링(성/ID)
# if keyword:
#     kw = keyword.strip()
#     if kw:
#         mask = pd.Series(False, index=list_df.index)
#         if "CustomerId" in list_df.columns:
#             mask |= list_df["CustomerId"].astype(str).str.contains(kw, na=False, regex=False)
#         if "Surname" in df.columns:
#             matched_ids = df.loc[
#                 df["Surname"].astype(str).str.contains(kw, case=False, na=False, regex=False),
#                 "CustomerId"
#             ].astype(str).tolist()
#             if matched_ids:
#                 mask |= list_df["CustomerId"].astype(str).isin(matched_ids)
#         list_df = list_df[mask]

# # ---------- 마스터(리스트) & 선택 ----------
# st.markdown('<div class="section-title">고객 리스트</div>', unsafe_allow_html=True)

# # 정렬
# sort_desc = st.toggle("확률 내림차순 정렬", value=True)
# list_df = list_df.sort_values("이탈률", ascending=not sort_desc)

# # 페이지 크기 + 전체 보기
# left, right = st.columns([1, 1])
# with left:
#     page_size = st.selectbox("페이지 크기", [25, 50, 100], index=1)
# with right:
#     show_all = st.toggle("전체 보기 (주의)", value=False)

# # 표시용 DF (행 매핑용 숨김 인덱스 추가)
# display_df = list_df.reset_index(drop=True).copy()
# if "_orig_idx" not in display_df.columns:
#     display_df.insert(0, "_orig_idx", display_df.index)

# # ---- AgGrid 옵션 구성 (다크 테마 적용)
# gob = GridOptionsBuilder.from_dataframe(display_df)
# gob.configure_column(
#     "이탈률",
#     type=["numericColumn"],
#     valueFormatter="(value == null) ? '' : (value * 100).toFixed(2) + ' %'"
# )
# gob.configure_column(
#     "Complain",
#     valueFormatter="(value == 1) ? 'Yes' : (value == 0 ? 'No' : value)"
# )
# gob.configure_default_column(sortable=True, filter=True, resizable=True)
# gob.configure_selection(selection_mode="single", use_checkbox=False)
# if show_all:
#     gob.configure_grid_options(pagination=False)
#     gob.configure_pagination(enabled=False)
# else:
#     gob.configure_pagination(paginationAutoPageSize=False, paginationPageSize=page_size)

# gob.configure_column("_orig_idx", hide=True)

# grid_options = gob.build()

# grid_resp = AgGrid(
#     display_df,
#     gridOptions=grid_options,
#     height=600 if show_all else 420,
#     fit_columns_on_grid_load=True,
#     update_on=["selectionChanged"],
#     allow_unsafe_jscode=True,
#     enable_enterprise_modules=False,
#     key="customers_grid",
#     theme="balham-dark",
#     custom_css={
#         ".ag-cell-focus": {"border": "none !important", "outline": "none !important"},
#         ".ag-row-hover": {"background-color": "rgba(54, 42, 95, 0.25) !important"},
#         ".ag-row-hover .ag-cell": {"color": "#ffffff !important"},
#         ".ag-row-selected": {"background-color": "rgba(54, 42, 95, 0.25) !important"},
#         ".ag-row-selected .ag-cell": {"color": "#ffffff !important"},
#     },
# )

# # 선택된 행
# selected_rows = grid_resp.get("selected_rows", [])
# if isinstance(selected_rows, pd.DataFrame):
#     selected_rows = selected_rows.to_dict("records")
# if selected_rows:
#     sel_row = selected_rows[0]
#     sel_id = str(sel_row.get("CustomerId", sel_row.get("_orig_idx", "")))
# else:
#     sel_id = None

# st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# # ---------- 디테일(선택 고객 상세 + LLM 추천) ----------
# st.markdown('<div class="section-title">고객 상세</div>', unsafe_allow_html=True)

# if not sel_id:
#     st.info("리스트에서 고객 행을 클릭하면 상세 정보가 여기에 표시됩니다.")
# else:
#     detail_row = None
#     if "CustomerId" in df.columns:
#         try:
#             cid = int(sel_id)
#             detail_row = df[df["CustomerId"] == cid].head(1)
#         except ValueError:
#             detail_row = df[df["CustomerId"].astype(str) == sel_id].head(1)

#     if detail_row is None or detail_row.empty:
#         st.warning("선택한 고객의 상세정보를 찾을 수 없습니다.")
#         st.stop()

#     # 기본 지표
#     proba_col, label_col = detect_score_cols(df)
#     score_val = float(detail_row[proba_col].values[0] * 100)
#     label_val = int(detail_row[label_col].values[0])

#     def v(col, default="N/A"):
#         return detail_row[col].values[0] if col in detail_row.columns else default

#     st.subheader(f"👤 고객 : {v('Surname')} ({v('CustomerId')})")
#     st.markdown(' ')
#     c1, c2 = st.columns(2)
#     c1.markdown(
#         f"""
#         <div class='churn-score'>예측확률 (Churn)</div>
#         <div class='churn-value'>{score_val:.2f}%</div>
#         """,
#         unsafe_allow_html=True
#     )

#     color = "#ef4444" if label_val == 1 else "#22c55e"
#     label_txt = "이탈" if label_val == 1 else "유지"
#     c2.markdown(
#         f"""
#         <div style='margin-bottom:0.1rem; font-weight:600; color:#9ca3af;'>예측라벨</div>
#         <div style='font-size:2rem; font-weight:800; color:{color}; margin-top:0;'>{label_txt}</div>
#         """, unsafe_allow_html=True
#     )

#     st.markdown('    ')
#     left_box, right_box = st.columns(2)
#     with left_box:
#         st.markdown("**프로필**")
#         prof = {}
#         for c in ["Geography", "Gender", "Age", "Tenure", "NumOfProducts", "HasCrCard", "IsActiveMember","Complain"]:
#             if c in df.columns:
#                 prof[c] = v(c)
#         st.table(pd.DataFrame(prof.items(), columns=["항목", "값"]).astype({"값": "string"}))

#     with right_box:
#         st.markdown("**재무/점수**")
#         fin = {}
#         for c in ["CreditScore", "Balance", "EstimatedSalary"]:
#             if c in df.columns:
#                 fin[c] = v(c)
#         fin["predicted_proba"] = score_val
#         fin["predicted_label"] = label_val
#         st.table(pd.DataFrame(fin.items(), columns=["항목", "값"]).astype({"값": "string"}))

#     with st.expander("원본 레코드 전체 보기"):
#         st.dataframe(detail_row.T, use_container_width=True)

#     # ── LLM 추천 (디자인만 변경) ───────────────────────────
#     st.subheader("🤖 추천 상품")

#     row_for_prompt = {
#         "CustomerId": v("CustomerId"),
#         "Surname": v("Surname"),
#         "Geography": v("Geography"),
#         "Gender": v("Gender"),
#         "Age": float(v("Age", 0) or 0),
#         "Tenure": float(v("Tenure", 0) or 0),
#         "Balance": float(v("Balance", 0) or 0),
#         "NumOfProducts": int(v("NumOfProducts", 0) or 0),
#         "HasCrCard": int(v("HasCrCard", 0) or 0),
#         "IsActiveMember": int(v("IsActiveMember", 0) or 0),
#         "EstimatedSalary": float(v("EstimatedSalary", 0) or 0),
#         "CreditScore": float(v("CreditScore", 0) or 0),
#         "churn_probability": float(detail_row[proba_col].values[0]),
#     }

#     if recommend_for_user is not None:
#         reco = recommend_for_user(row_for_prompt)
#     else:
#         reco = {"summary": "LLM 모듈이 없습니다.", "top_products": [], "next_actions": [], "risk_level": "N/A"}

#     risk_level = str(reco.get("risk_level", "N/A")).upper()
#     risk_class = "red" if risk_level == "HIGH" else ("orange" if risk_level in ("MEDIUM","MID") else ("green" if risk_level == "LOW" else ""))

#     # 위험도 + 요약 상단 박스
#     st.markdown(
#         f"""
#         <div class='reco-row'>
#           <div class='risk-badge'>
#             <div class='risk-title'>위험도</div>
#             <div class='risk-pill {risk_class}'>{risk_level}</div>
#           </div>
#           <div class='summary-box'>{reco.get('summary','요약 없음')}</div>
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )

#     # 추천 카드 렌더링 (디자인만 변경)
#     recs = reco.get("top_products", [])
#     if recs:
#         for r in recs:
#             code = r.get("code", "").strip()
#             name = _PROD_MAP.get(code, {}).get("name", code)
#             reason = r.get("reason", "")
#             st.markdown(
#                 f"""
#                 <div class='reco-card'>
#                   <div class='reco-icon'>💡</div>
#                   <div class='reco-main'>
#                     <div class='reco-name'>{name} <span class='reco-code'>{code}</span></div>
#                     <div class='reco-reason'>{reason}</div>
#                   </div>
#                 </div>
#                 """,
#                 unsafe_allow_html=True,
#             )
#     else:
#         st.write("- (추천 없음)")

#     # 다음 액션 (디자인만 변경)
#     acts = reco.get("next_actions", [])
#     if acts:
#         st.markdown(
#             """
#             <div class='reco-actions'>
#               <h4>다음 액션</h4>
#               <ul>
#             """,
#             unsafe_allow_html=True,
#         )
#         for a in acts:
#             st.markdown(f"<li>{a}</li>", unsafe_allow_html=True)
#         st.markdown("</ul></div>", unsafe_allow_html=True)

#     # 키 없음 안내 (동일)
#     if not os.getenv("OPENAI_API_KEY"):
#         st.caption("※ LLM 키가 없어 정책 기반 폴백으로 동작 중입니다. (.env: OPENAI_API_KEY)")
#-----------------------------------------------------------------
import os
import streamlit as st
import pandas as pd
from pages.app_bootstrap import render_sidebar  # 필수
from st_aggrid import AgGrid, GridOptionsBuilder  # 리스트 클릭 상호작용
from dotenv import load_dotenv
import pymysql

# ───────────────────────────────────────────────────────────────
# 페이지 전역 설정 (다크 고정 느낌의 스타일을 코드로 주입)
st.set_page_config(
    page_title="고객 이탈률",
    page_icon="📉",
    layout="wide",
)

# 전역 다크 스타일 (Streamlit 다크/라이트 무관하게 어두운 톤 유지)
DARK_CSS = """
    <style>
    html, body, [data-testid=\"stAppViewContainer\"] { background-color: #0f1216 !important; color: #e5e7eb !important; }
    [data-testid=\"stHeader\"] { display: none; }
    .erp-shell { padding: 8px 16px 20px; }

    /* ─── 상단 네비게이션 바 (유지) ─── */
    .erp-topbar { display:flex; align-items:center; gap:12px; background:#0b0f14; border:1px solid #232832; border-radius:12px; padding:10px 14px; margin-bottom:12px; }
    .erp-brand { font-weight:800; color:#e5e7eb; letter-spacing:.3px; }
    .erp-breadcrumb { color:#9aa4b2; font-size:12.5px; }
    .erp-breadcrumb .sep { opacity:.45; padding:0 6px; }
    .erp-actions { margin-left:auto; display:flex; gap:8px; }
    .erp-btn { padding:6px 10px; font-size:12.5px; border:1px solid #2a303a; border-radius:8px; background:#0f141a; color:#cbd5e1; }
    .erp-btn:disabled { opacity:.5; cursor:not-allowed; }

    /* 헤더 카드 */
    .erp-header { background: linear-gradient(180deg, #171b22 0%, #12161b 100%); border: 1px solid #262b33; border-radius: 12px; padding: 16px 18px; margin-bottom: 16px; box-shadow: 0 8px 20px rgba(0,0,0,.25); }
    .erp-title { margin: 0; font-weight: 700; font-size: 20px; color: #f3f4f6; }
    .erp-sub { margin: 2px 0 0; font-size: 13px; color: #94a3b8; }

    /* 사이드바 */
    [data-testid=\"stSidebar\"] { background-color: #0b0e12 !important; border-right: 1px solid #232832; }
    [data-testid=\"stSidebar\"] .sidebar-title { font-weight: 700; color:#cbd5e1; margin-bottom:8px; font-size:14px; }
    .sidebar-box { background: #0f141a; border:1px solid #232832; border-radius:12px; padding:10px; margin-bottom:12px; }
    .sidebar-box .stMultiSelect > label, .sidebar-box .stSlider > label, .sidebar-box .stTextInput > label { color:#94a3b8 !important; }

    /* 섹션 헤더/구분선 */
    .section-title { font-weight:700; font-size:16px; margin: 6px 0 8px; color: #e2e8f0; }
    .divider { height:1px; background: linear-gradient(90deg, transparent, #28303b, transparent); margin: 12px 0; }

    /* 표/테이블 */
    .stTable, .stTable *, .stDataFrame, .stDataFrame * { color:#eaeef6 !important; }

    /* Ag-Grid 다크 룩 보정 */
    .ag-theme-balham-dark {
        --ag-background-color: #0f1216;
        --ag-odd-row-background-color: #0c0f13;
        --ag-header-background-color: #0c0f13;
        --ag-border-color: #20232a;
        --ag-foreground-color: #e5e7eb;
        --ag-secondary-foreground-color: #cbd5e1;
        --ag-row-hover-color: rgba(255,255,255,0.12); /* 호버 = 선택과 동일 */
        --ag-selected-row-background-color: rgba(255,255,255,0.20);
    }
    .ag-theme-balham-dark .ag-root-wrapper { border-radius: 12px; border:1px solid #232832; }
    .ag-theme-balham-dark .ag-header-cell-label { justify-content: center; }
    .ag-theme-balham-dark .ag-cell { font-size: 13px; padding: 6px 8px; }
    .ag-theme-balham-dark .ag-row-hover .ag-cell,
    .ag-theme-balham-dark .ag-row-selected .ag-cell { color:#111827 !important; }
    .ag-theme-balham-dark .ag-cell-focus { border-color:#60a5fa !important; box-shadow: inset 0 0 0 1px #60a5fa; }

    /* metric-like 수치 텍스트 */
    .churn-score { margin-bottom:0.1rem; font-weight:600; color:#9ca3af; }
    .churn-value { font-size:2rem; font-weight:800; margin-top:0; color:#f8fafc; }

    /* ─── 추천 섹션 커스텀 (디자인만 변경) ─── */
    .reco-row { display:grid; grid-template-columns: 200px 1fr; gap:12px; align-items:center; margin: 10px 0 14px; }
    .risk-badge { background:#12161b; border:1px solid #263042; border-radius:12px; padding:16px; text-align:center; }
    .risk-title { font-size:12px; color:#93a4b8; margin:0 0 2px; font-weight:600; letter-spacing:.4px; }
    .risk-pill { font-size:28px; font-weight:800; margin:0; }
    .risk-pill.red { color:#ef4444; }
    .risk-pill.orange { color:#f59e0b; }
    .risk-pill.green { color:#22c55e; }
    .summary-box { background:#0f1b27; border:1px solid #1f2a38; border-radius:12px; padding:14px 16px; color:#cfe0f4; }

    .reco-card { display:flex; gap:12px; align-items:flex-start; background:#0f141a; border:1px solid #232832; border-radius:12px; padding:12px 14px; margin-bottom:10px; transition: background .15s ease, border-color .15s ease; }
    .reco-card:hover { background:#11171e; border-color:#2b3542; }
    .reco-icon { width:28px; height:28px; border-radius:8px; background:#111922; border:1px solid #243044; display:flex; align-items:center; justify-content:center; font-size:14px; opacity:.85; }
    .reco-main { flex:1; }
    .reco-name { font-weight:700; color:#e5e7eb; }
    .reco-code { display:inline-block; margin-left:6px; padding:2px 6px; font-size:11px; border:1px solid #2a3545; color:#9fb2cc; border-radius:999px; }
    .reco-reason { color:#cbd5e1; opacity:.9; margin-top:4px; }

    .reco-actions { margin-top:10px; }
    .reco-actions h4 { margin:0 0 6px; font-size:13px; color:#e5e7eb; }
    .reco-actions ul { margin:0; padding-left:18px; }
    .reco-actions li { margin:4px 0; color:#cbd5e1; }
    
    /* ─── Controls: Search / Page Size / Toggle in White ─── */
    /* Text input (검색) */
    div[data-testid="stTextInput"] input {
        background:#ffffff !important; color:#111827 !important;
        border:1px solid #d1d5db !important; border-radius:10px !important;
    }
    div[data-testid="stTextInput"] input:focus {
        outline:none !important; border-color:#60a5fa !important;
        box-shadow:0 0 0 3px rgba(96,165,250,.25) !important;
    }

    /* Selectbox (페이지 크기) */
    div[data-testid="stSelectbox"] div[role="combobox"],
    div[data-testid="stSelectbox"] input {
        background:#ffffff !important; color:#111827 !important;
        border:1px solid #d1d5db !important; border-radius:10px !important;
    }
    div[data-testid="stSelectbox"] div[role="combobox"]:focus-within {
        border-color:#60a5fa !important; box-shadow:0 0 0 3px rgba(96,165,250,.25) !important;
    }
    div[data-testid="stSelectbox"] svg { color:#111827 !important; opacity:1 !important; }

    /* Toggle (전체 보기) */
    div[data-testid="stSwitch"] label { color:#ffffff !important; }
    div[data-testid="stSwitch"] [role="switch"] {
        background:#ffffff !important; border:1px solid #d1d5db !important;
    }
    div[data-testid="stSwitch"] [role="switch"][aria-checked="true"] { background:#e5e7eb !important; }

    /* ─── Bottom info tables: stronger borders ─── */
    .stTable { border:1.5px solid #3b4252 !important; border-radius:12px !important; }
    .stTable table { border-collapse:separate !important; border-spacing:0 !important; }
    .stTable th, .stTable td { border-bottom:1px solid #2e3440 !important; }

    /* ─── Force labels (검색/페이지 크기/전체 보기) to pure white ─── */
    div[data-testid="stTextInput"] label,
    div[data-testid="stTextInput"] label *,
    div[data-testid="stSelectbox"] label,
    div[data-testid="stSelectbox"] label *,
    div[data-testid="stSwitch"] label,
    div[data-testid="stSwitch"] label *,
    div[data-testid="stSwitch"] p,
    div[data-testid="stSwitch"] span { color:#ffffff !important; opacity:1 !important; }

    /* Bottom info tables: white borders for clear visibility */
    .stTable { border:1.5px solid #ffffff !important; border-radius:12px !important; }
    .stTable table { border-collapse:separate !important; border-spacing:0 !important; }
    .stTable th, .stTable td { border-bottom:1px solid #ffffff !important; }

    /* ─── Sidebar palette override (match BCMS screenshot) ─── */
    [data-testid="stSidebar"] {
        background:#1f232b !important; /* deeper grey */
        border-right:1px solid #2c313a !important;
        color:#ffffff !important;
    }
    [data-testid="stSidebar"] * { color:#ffffff !important; }
    [data-testid="stSidebar"] a, [data-testid="stSidebar"] button { color:#ffffff !important; text-decoration:none !important; }
    [data-testid="stSidebar"] a:hover { background:#3a3f49 !important; border-radius:12px; }
    /* active/selected nav item */
    [data-testid="stSidebar"] a[aria-current="page"],
    [data-testid="stSidebar"] a.active,
    [data-testid="stSidebar"] .is-active {
        background:#454a56 !important; /* pill highlight */
        border:1px solid #676e79 !important;
        border-radius:12px !important;
        color:#ffffff !important;
    }
    [data-testid="stSidebar"] hr { border-color:#2c313a !important; }

    /* Make all Streamlit selectboxes look read-only: hide caret and disable typing */
    div[data-testid="stSelectbox"] input {
        caret-color: transparent !important; /* hide | */
        user-select: none !important;        /* no text selection */
        pointer-events: none !important;     /* typing disabled, click container still works */
    }
    div[data-testid="stSelectbox"] div[role="combobox"] { cursor: pointer !important; }

    /* ── 상세정보: 폼 레이아웃 ── */
    .detail-box{background:#0f141a;border:1px solid #2b3542;border-radius:12px;}
    .detail-row{display:grid;grid-template-columns:160px 1fr;gap:8px 16px;padding:10px 12px;border-top:1px solid #2e3440;}
    .detail-row:first-child{border-top:0;}
    .detail-key{color:#93a4b8;font-size:12px;}
    .detail-val{color:#e5e7eb;font-weight:700;}
    </style>
"""

st.markdown(DARK_CSS, unsafe_allow_html=True)

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

st.markdown(
    """
    <div class=\"erp-shell\">
      <div class=\"erp-topbar\">
        <div class=\"erp-brand\">🏦 Bank ERP</div>
        <div class=\"erp-breadcrumb\">고객관리 <span class=\"sep\">/</span> 이탈 관리</div>
        <div class=\"erp-actions\">
          <button class=\"erp-btn\" disabled>새로고침</button>
          <button class=\"erp-btn\" disabled>설정</button>
        </div>
      </div>
      <div class=\"erp-header\">
        <h1 class=\"erp-title\">📉 고객 이탈률</h1>
        <p class=\"erp-sub\"></p>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

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
        cursorclass=pymysql.cursors.Cursor,
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

# ───────── 사이드바 필터 (디자인만 조정) ─────────
with st.sidebar:
    st.markdown('<div class="sidebar-title">고객 정보 필터</div>', unsafe_allow_html=True)
    with st.container(border=False):
        st.markdown('<div class="sidebar-box">', unsafe_allow_html=True)
        min_p, max_p = st.slider("예측 확률 범위", 0.0, 1.0, (0.0, 1.0), 0.01)
        complain = st.selectbox("Complain 여부", ["전체", "Yes", "No"], index=0)
        geos = st.multiselect("국가(Geography)", sorted(df["Geography"].unique()))
        genders  = st.selectbox("성별(Gender)", ["전체"] + sorted(df["Gender"].dropna().unique().tolist()), index=0)
        age_groups = st.multiselect(
            "연령대 선택",
            [
                "10대 (10-19)", "20대 (20-29)", "30대 (30-39)",
                "40대 (40-49)", "50대 (50-59)", "60대 이상 (60+)"
            ],
            default=[]
        )
        credit_groups = st.multiselect(
            "신용점수 등급",
            [
                "Excellent (800-850)", "Very Good (740-799)", "Good (670-739)",
                "Fair (580-669)", "Poor (300-579)"
            ],
            default=[]
        )
        st.markdown('</div>', unsafe_allow_html=True)

keyword = st.text_input("검색(ID/성명)")

base_cols = [c for c in ["CustomerId", "Complain", "Age", "Gender", "Geography", "CreditScore", "NumOfProducts"] if c in df.columns]
list_cols = base_cols + [proba_col]
list_df = df[list_cols].copy()

rename_map = {
    "CustomerId": "CustomerId",
    "Complain": "Complain",          # 표시명 그대로 유지
    "Age": "나이",
    "Gender": "성별",
    "Geography": "지역",
    "CreditScore": "신용점수",
    "NumOfProducts": "가입상품",
    proba_col: "이탈률",
}
list_df.rename(columns={k: v for k, v in rename_map.items() if k in list_df.columns}, inplace=True)

# 필터 적용
list_df = list_df[(list_df["이탈률"] >= min_p) & (list_df["이탈률"] <= max_p)]

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

# Complain / Gender 필터 (selectbox 전용)
if "Complain" in list_df.columns and complain != "전체":
    comp_val = 1 if complain == "Yes" else 0
    list_df = list_df[list_df["Complain"] == comp_val]

if "성별" in list_df.columns and genders != "전체":
    list_df = list_df[list_df["성별"] == genders]

# 검색어 필터링(성/ID)
if keyword:
    kw = keyword.strip()
    if kw:
        mask = pd.Series(False, index=list_df.index)
        if "CustomerId" in list_df.columns:
            mask |= list_df["CustomerId"].astype(str).str.contains(kw, na=False, regex=False)
        if "Surname" in df.columns:
            matched_ids = df.loc[
                df["Surname"].astype(str).str.contains(kw, case=False, na=False, regex=False),
                "CustomerId"
            ].astype(str).tolist()
            if matched_ids:
                mask |= list_df["CustomerId"].astype(str).isin(matched_ids)
        list_df = list_df[mask]

# ---------- 마스터(리스트) & 선택 ----------
st.markdown('<div class="section-title">고객 리스트</div>', unsafe_allow_html=True)

# 정렬
sort_desc = st.toggle("확률 내림차순 정렬", value=True)
list_df = list_df.sort_values("이탈률", ascending=not sort_desc)

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

# ---- AgGrid 옵션 구성 (다크 테마 적용)
gob = GridOptionsBuilder.from_dataframe(display_df)
gob.configure_column(
    "이탈률",
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
    theme="balham-dark",
    custom_css={
        ".ag-cell-focus": {"border": "none !important", "outline": "none !important"},
        ".ag-row-hover": {"background-color": "rgba(255,255,255,0.12) !important"},
        ".ag-row-hover .ag-cell": {"color": "#111827 !important"},
        ".ag-row-selected": {"background-color": "rgba(255,255,255,0.20) !important"},
        ".ag-row-selected .ag-cell": {"color": "#111827 !important"},
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

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ---------- 디테일(선택 고객 상세 + LLM 추천) ----------
st.markdown('<div class="section-title">고객 상세</div>', unsafe_allow_html=True)

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
        <div class='churn-score'>예측확률 (Churn)</div>
        <div class='churn-value'>{score_val:.2f}%</div>
        """,
        unsafe_allow_html=True
    )

    color = "#ef4444" if label_val == 1 else "#22c55e"
    label_txt = "이탈" if label_val == 1 else "유지"
    c2.markdown(
        f"""
        <div style='margin-bottom:0.1rem; font-weight:600; color:#9ca3af;'>예측라벨</div>
        <div style='font-size:2rem; font-weight:800; color:{color}; margin-top:0;'>{label_txt}</div>
        """, unsafe_allow_html=True
    )

    st.markdown('    ')
    # left_box, right_box = st.columns(2)
    # with left_box:
    #     st.markdown("**프로필**")
    #     prof = {}
    #     for c in ["Geography", "Gender", "Age", "Tenure", "NumOfProducts", "HasCrCard", "IsActiveMember","Complain"]:
    #         if c in df.columns:
    #             prof[c] = v(c)
    #     st.table(pd.DataFrame(prof.items(), columns=["항목", "값"]).astype({"값": "string"}))

    # with right_box:
    #     st.markdown("**재무/점수**")
    #     fin = {}
    #     for c in ["CreditScore", "Balance", "EstimatedSalary"]:
    #         if c in df.columns:
    #             fin[c] = v(c)
    #     fin["predicted_proba"] = score_val
    #     fin["predicted_label"] = label_val
    #     st.table(pd.DataFrame(fin.items(), columns=["항목", "값"]).astype({"값": "string"}))

    left_box, right_box = st.columns(2)

    def render_detail_box(title: str, items: dict):
        st.markdown(f"**{title}**")
        rows = []
        for k, v in items.items():
            rows.append(f"""
                <div class="detail-row">
                <div class="detail-key">{k}</div>
                <div class="detail-val">{v}</div>
                </div>""")
        st.markdown(f"<div class='detail-box'>{''.join(rows)}</div>", unsafe_allow_html=True)

    with left_box:
        prof = {}
        for c in ["Geography", "Gender", "Age", "Tenure", "NumOfProducts", "HasCrCard", "IsActiveMember","Complain"]:
            if c in df.columns:
                prof[c] = v(c)
        render_detail_box("프로필", prof)

    with right_box:
        fin = {}
        for c in ["CreditScore", "Balance", "EstimatedSalary"]:
            if c in df.columns:
                fin[c] = v(c)
        fin["predicted_proba"] = f"{score_val:.2f}%"
        fin["predicted_label"] = label_val
        render_detail_box("재무/점수", fin)

    with st.expander("원본 레코드 전체 보기"):
        st.dataframe(detail_row.T, use_container_width=True)

    # ── LLM 추천 (디자인만 변경) ───────────────────────────
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

    risk_level = str(reco.get("risk_level", "N/A")).upper()
    risk_class = "red" if risk_level == "HIGH" else ("orange" if risk_level in ("MEDIUM","MID") else ("green" if risk_level == "LOW" else ""))

    # 위험도 + 요약 상단 박스
    st.markdown(
        f"""
        <div class='reco-row'>
          <div class='risk-badge'>
            <div class='risk-title'>위험도</div>
            <div class='risk-pill {risk_class}'>{risk_level}</div>
          </div>
          <div class='summary-box'>{reco.get('summary','요약 없음')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 추천 카드 렌더링 (디자인만 변경)
    recs = reco.get("top_products", [])
    if recs:
        for r in recs:
            code = r.get("code", "").strip()
            name = _PROD_MAP.get(code, {}).get("name", code)
            reason = r.get("reason", "")
            st.markdown(
                f"""
                <div class='reco-card'>
                  <div class='reco-icon'>💡</div>
                  <div class='reco-main'>
                    <div class='reco-name'>{name} <span class='reco-code'>{code}</span></div>
                    <div class='reco-reason'>{reason}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.write("- (추천 없음)")



    # 다음 액션 (디자인만 변경)
    acts = reco.get("next_actions", [])
    if acts:
        st.markdown(
            """
            <div class='reco-actions'>
              <h4>다음 액션</h4>
              <ul>
            """,
            unsafe_allow_html=True,
        )
        for a in acts:
            st.markdown(f"<li>{a}</li>", unsafe_allow_html=True)
        st.markdown("</ul></div>", unsafe_allow_html=True)

    # 키 없음 안내 (동일)
    if not os.getenv("OPENAI_API_KEY"):
        st.caption("※ LLM 키가 없어 정책 기반 폴백으로 동작 중입니다. (.env: OPENAI_API_KEY)")
