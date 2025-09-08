import os
import streamlit as st
from textwrap import dedent
from utils.ui.ui_tools import seg_label
from utils.ui.style import apply_inline_css

# 공용 아이콘 매핑 (RFM/개인 추천 모두 동일 사용)
ICON_MAP = {
    "CHK_FREE": "🏦",
    "SAV_PLUS": "💰",
    "SAV_HIGH": "📈",
    "CRD_CASH": "💳",
    "CRD_TRAVEL": "🧳",
    "LOAN_DC": "🔁",
    "LOAN_PL": "💸",
    "WEALTH_ETF": "📊",
    "INS_SAFE": "🛡️",
}

def mount_llm_styles() -> None:
    """
    모달/카드 스타일은 ui/style.py(COMMON_CSS)에서 일괄 주입한다.
    여기서는 추가 CSS를 넣지 않고 공통 CSS만 보장 호출.
    """
    apply_inline_css()


def render_bundle_cards(bundle: list[dict], prod_map: dict, icon_map: dict, show_reason: bool = True) -> None:
    """
    카드 그리드 렌더러 (RFM/개인 공용).
    bundle = [{'code': '...', 'reason': '...'}, ...]
    """
    cards: list[str] = []
    for b in bundle:
        code = (b.get("code") or "").strip()
        prod = prod_map.get(code, {"name": code, "tags": []})
        name = prod.get("name", code)
        tags = prod.get("tags", [])
        icon = icon_map.get(code, "📦")
        tag_html = "".join(f'<span class="tag">#{t}</span>' for t in tags)
        reason = (b.get("reason") or "").strip()
        reason_html = f'<div class="reason">{reason}</div>' if (show_reason and reason) else ""

        cards.append(dedent(f"""
        <div class="bundle-card" tabindex="0">
          <span class="strategy-badge">STRATEGY</span>
          <div class="bundle-header">
            <div class="icon-badge">{icon}</div>
            <div class="bundle-title">
              <div class="name">{name} <span class="code">({code})</span></div>
            </div>
          </div>
          <div class="tags">{tag_html}</div>
          {reason_html}
          <div class="card-actions">
            <button class="btn primary">전략 실행</button>
            <button class="btn">자세히</button>
          </div>
        </div>
        """).strip())

    if cards:
        st.markdown('<div class="bundle-grid">' + "".join(cards) + "</div>", unsafe_allow_html=True)
    else:
        st.info("추천 없음")


def show_user_list_LLM_strategy(row_for_prompt: dict) -> None:
    """
    사용자 상세(개별 고객) 모달에서 LLM 추천 렌더링.
    row_for_prompt = {
      'CustomerId','Surname','Geography','Gender','Age','Tenure',
      'Balance','NumOfProducts','HasCrCard','IsActiveMember',
      'EstimatedSalary','CreditScore','churn_probability'
    }
    """
    # 공통 CSS(모달/카드)는 ui/style.py에서 처리
    mount_llm_styles()

    # LLM 추천 래퍼
    try:
        from utils.llm.reco_templates import recommend_for_user, PRODUCT_CATALOG
        _PROD_MAP = {p["code"]: p for p in PRODUCT_CATALOG}
    except Exception:
        recommend_for_user = None
        PRODUCT_CATALOG = []
        _PROD_MAP = {}

    # LLM 호출 (폴백)
    if recommend_for_user is not None:
        reco = recommend_for_user(row_for_prompt)
    else:
        fallback_codes = [p.get("code", "") for p in PRODUCT_CATALOG][:3]
        reco = {
            "summary": "LLM 모듈이 없어 정책 번들을 표시합니다.",
            "top_products": [{"code": c, "reason": "표준 번들"} for c in fallback_codes if c],
            "next_actions": ["표준 오퍼 발송", "A/B 테스트로 캠페인 최적화"],
            "risk_level": "N/A",
        }

    # 상단 인트로 패널
    name = row_for_prompt.get("Surname", "고객")
    cid  = row_for_prompt.get("CustomerId", "")
    churn = row_for_prompt.get("churn_probability")
    churn_txt = f"{float(churn)*100:.2f}%" if isinstance(churn, (int,float)) else "N/A"

    st.markdown(dedent(f"""
    <div style="font-size:1.1rem; line-height:1.6; margin:0 0 12px 0; padding:16px 30px;
                background-color:#111418; border-radius:10px; border:1px solid #252a31;">
      <div style="font-size:1.3rem; font-weight:600; margin-bottom:6px;">
        {name} ({cid})
      </div>
      <div style="margin-bottom:6px;">
        예측 이탈확률 <b style="font-size:1.4rem; color:#3b82f6;">{churn_txt}</b>
      </div>
      <div style="color:#cfd7e2;">💬 이 고객에게는 다음과 같은 전략을 실행할 수 있습니다.</div>
    </div>
    """).strip(), unsafe_allow_html=True)

    # 카드 렌더
    render_bundle_cards(reco.get("top_products", []), _PROD_MAP, icon_map=ICON_MAP, show_reason=True)

    # 다음 액션
    acts = reco.get("next_actions", [])
    if acts:
        st.markdown("<div class='reco-actions'><h4>다음 액션</h4><ul>", unsafe_allow_html=True)
        for a in acts:
            st.markdown(f"<li>{a}</li>", unsafe_allow_html=True)
        st.markdown("</ul></div>", unsafe_allow_html=True)



# 고객 그룹(RFM) LLM 추천
def show_RFM_LLM_strategy(seg_df, seg):
    # ───────────────────────────────────────────────────────────────
    # LLM 추천 래퍼
    try:
        from utils.llm.reco_templates import recommend_for_segment, SEGMENT_BUNDLES, PRODUCT_CATALOG
        _PROD_MAP = {p["code"]: p for p in PRODUCT_CATALOG}
    except Exception:
        recommend_for_segment = None
        SEGMENT_BUNDLES = {}
        PRODUCT_CATALOG = []
        _PROD_MAP = {}
    # ───────────────────────────────────────────────────────────────
    
    # ── 세그먼트 대표 추천/플레이북 (래퍼 사용: 키 없으면 폴백)
    stats = {
        "count": len(seg_df),
        "avg_churn": round(seg_df["churn_probability"].mean() if len(seg_df) else float("nan"), 4),
        "avg_r": round(seg_df["r_score"].mean() if len(seg_df) else float("nan"), 2),
        "avg_f": round(seg_df["f_score"].mean() if len(seg_df) else float("nan"), 2),
        "avg_m": round(seg_df["m_score"].mean() if len(seg_df) else float("nan"), 2),
    }

    if recommend_for_segment is not None:
        seg_reco = recommend_for_segment(seg, stats)
    else:
        bundle = SEGMENT_BUNDLES.get(seg, [])
        seg_reco = {
            "segment": seg,
            "summary": "LLM 모듈이 없어 정책 번들을 표시합니다.",
            "recommended_bundle": [{"code": c, "reason": "세그먼트 표준 번들"} for c in bundle],
            "playbook": ["표준 오퍼 발송", "A/B 테스트로 캠페인 최적화"],
        }

    # st.info(seg_reco.get("summary", "요약 없음"))
    # 교체
    group_name = seg  # 혹은 seg_reco["segment"] 에서 가져와도 됨
    count = len(seg_df) if seg_df is not None else 0
    st.markdown(
        f"""
        <div style="font-size:1.1rem; line-height:1.6; margin:0 0 12px 0; padding:16px 30px; 
                    background-color:#111418; border-radius:10px; border:1px solid #252a31;">
            <div style="font-size:1.3rem; font-weight:600; margin-bottom:6px;">
                {seg_label(group_name)} 고객 그룹
            </div>
            <div style="margin-bottom:6px;">
                총 <b style="font-size:1.4rem; color:#3b82f6;">{count:,}명</b>의 고객이 있습니다.
            </div>
            <div style="color:#cfd7e2;">💬 이 그룹 고객에게는 다음과 같은 전략을 실행할 수 있습니다.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 3열 카드 렌더링
    bundle = seg_reco.get("recommended_bundle", [])
    if bundle:
        # st.markdown("** 추천 전략 **")

        cards_html = []
        for b in bundle:
            code = b.get("code","")
            prod = _PROD_MAP.get(code, {"name": code, "tags": []})
            name = prod.get("name", code)
            tags = prod.get("tags", [])
            reason = b.get("reason","세그먼트 표준 번들")
            icon = ICON_MAP.get(code, "📦")
            tag_html = "".join([f'<span class="tag">#{t}</span>' for t in tags])

            # ← 앞줄이 바로 '<'로 시작하게, 그리고 dedent로 들여쓰기 제거
            cards_html.append(dedent(f"""
                <div class="bundle-card" tabindex="0">
                    <span class="strategy-badge">STRATEGY</span>
                    <div class="bundle-header">
                        <div class="icon-badge">{icon}</div>
                        <div class="bundle-title">
                            <div class="name">{name}</div>
                            <div class="code">({code})</div>
                        </div>
                    </div>
                    <div class="tags">{tag_html}</div>
                    <!-- 필요 시 CTA 버튼 노출 -->
                    <div class="card-actions">
                        <button class="btn primary">전략 실행</button>
                        <button class="btn">자세히</button>
                    </div>
                </div>
            """).strip())
        grid_html = '<div class="bundle-grid">' + "".join(cards_html) + '</div>'
        st.markdown(grid_html, unsafe_allow_html=True)