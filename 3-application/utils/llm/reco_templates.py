# 3-application/utils/llm/reco_templates.py
from __future__ import annotations
import os
from typing import Dict, Any, List, Tuple

# LLM 호출 (JSON 보장)
from utils.llm.llm_client import chat_json, chat_text  # ← 중요

# LLM 키가 없으면 룰베이스 폴백 사용
USE_LLM = bool(os.getenv("OPENAI_API_KEY"))

# ───────────────────────────────────────────────────────────────
# 카탈로그(필요하면 SKU/혜택/제한조건 등 상세 확장 가능)
PRODUCT_CATALOG = [
    {"code": "CHK_FREE",   "name": "수수료무료 체크계좌",          "tags": ["입출금", "수수료면제"]},
    {"code": "SAV_PLUS",   "name": "세이빙 플러스(오토세이브)",    "tags": ["적립", "자동이체", "소액저축"]},
    {"code": "SAV_HIGH",   "name": "고금리 예금(12/36개월)",       "tags": ["예금", "금리우대"]},
    {"code": "CRD_CASH",   "name": "캐시백 신용카드",              "tags": ["리워드", "생활비"]},
    {"code": "CRD_TRAVEL", "name": "여행 리워드 카드",             "tags": ["마일리지", "여행"]},
    {"code": "LOAN_DC",    "name": "부채통합 대출",                "tags": ["이자절감", "리파이낸싱"]},
    {"code": "LOAN_PL",    "name": "개인 신용대출(중금리)",        "tags": ["대출", "유동성"]},
    {"code": "WEALTH_ETF", "name": "Wealth Starter(ETF 적립)",    "tags": ["투자", "초보"]},
    {"code": "INS_SAFE",   "name": "안심케어(체크카드 보험 번들)", "tags": ["보장", "번들"]},
]
_catalog_map = {p["code"]: p for p in PRODUCT_CATALOG}

def _catalog_text() -> str:
    return "\n".join(
        [f"- {p['code']}: {p['name']} (tags: {', '.join(p['tags'])})" for p in PRODUCT_CATALOG]
    )

# ───────────────────────────────────────────────────────────────
# 환경변수로 손쉽게 경계값 조정 가능 (없으면 기본값 사용)
def _get_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default

CHURN_TH_HIGH = _get_float("CHURN_TH_HIGH", 0.60)
CHURN_TH_MED  = _get_float("CHURN_TH_MED",  0.35)
BAL_HIGH      = _get_float("BAL_HIGH",     100_000)
SAL_HIGH      = _get_float("SAL_HIGH",      90_000)
CREDIT_LOW, CREDIT_MID = 550, 700   # <550: low, 550~699: mid, >=700: high
AGE_YOUNG, AGE_ADULT, AGE_MATURE = 30, 45, 60

# ───────────────────────────────────────────────────────────────
# 파생 플래그/밴드 산출
def _risk_level(churn: float) -> str:
    if churn >= CHURN_TH_HIGH: return "HIGH"
    if churn >= CHURN_TH_MED:  return "MEDIUM"
    return "LOW"

def _credit_band(cs: float) -> str:
    if cs < CREDIT_LOW:  return "low"
    if cs < CREDIT_MID:  return "mid"
    return "high"

def _age_band(age: float) -> str:
    if age < AGE_YOUNG:  return "youth"
    if age < AGE_ADULT:  return "adult"
    if age < AGE_MATURE: return "mature"
    return "senior"

def derive_flags(row: Dict[str, Any]) -> Dict[str, Any]:
    bal = float(row.get("Balance", 0) or 0)
    sal = float(row.get("EstimatedSalary", 0) or 0)
    cs  = float(row.get("CreditScore", 0) or 0)
    age = float(row.get("Age", 0) or 0)

    flags = {
        "risk": _risk_level(float(row.get("churn_probability", 0.0))),
        "credit_band": _credit_band(cs),
        "age_band": _age_band(age),

        "high_balance": bal >= BAL_HIGH,
        "high_income":  sal >= SAL_HIGH,

        "inactive": int(row.get("IsActiveMember", 0) or 0) == 0,
        "has_card":  int(row.get("HasCrCard", 0) or 0) == 1,
        "few_products": int(row.get("NumOfProducts", 0) or 0) <= 1,
    }
    return flags

# ───────────────────────────────────────────────────────────────
# 결정 규칙: 상품 코드 선택(순서=우선순위). 최대 3개 추천.
def select_products(row: Dict[str, Any]) -> List[str]:
    f = derive_flags(row)
    out: List[str] = []

    def add(code: str):
        if code in _catalog_map and code not in out and len(out) < 3:
            out.append(code)

    # 1) 위험도가 높을수록 유지/활성화/혜택 중심
    if f["risk"] == "HIGH":
        add("CHK_FREE")                                # 수수료 면제 → 유지
        if f["few_products"] or f["inactive"]:
            add("SAV_PLUS")                            # 자동저축으로 재방문 유도
        if f["credit_band"] != "low":
            add("CRD_CASH")                            # 생활비 캐시백(가맹점 혜택)
        if len(out) < 3 and f["credit_band"] == "mid":
            add("LOAN_PL")                             # 유동성 니즈 대응(중금리)
        if len(out) < 3 and f["has_card"]:
            add("INS_SAFE")                            # 번들로 이탈방지(보장)

    elif f["risk"] == "MEDIUM":
        if f["inactive"]:
            add("CHK_FREE")
        if f["few_products"]:
            add("SAV_PLUS")
        if f["high_balance"] or f["high_income"]:
            add("SAV_HIGH")
        if f["credit_band"] != "low" and len(out) < 3:
            add("CRD_CASH")

    else:  # LOW
        if f["high_balance"]:
            add("SAV_HIGH")
        add("WEALTH_ETF")                              # 소액 ETF 적립(업셀링)
        if f["credit_band"] != "low":
            # 여행/혜택형은 성인~장년층 위주
            add("CRD_TRAVEL" if f["age_band"] in ("adult", "mature") else "CRD_CASH")
        if len(out) < 3 and f["few_products"]:
            add("SAV_PLUS")

    return out

# 세그먼트 기본 번들 (집합 추천) — DB의 segment_code 기준
SEGMENT_BUNDLES = {
    "VIP":     ["WEALTH_ETF", "SAV_HIGH", "CRD_TRAVEL"],
    "LOYAL":   ["SAV_HIGH", "CRD_CASH", "WEALTH_ETF"],
    "AT_RISK": ["CHK_FREE", "SAV_PLUS", "CRD_CASH"],
    "LOW":     ["SAV_PLUS", "CRD_CASH", "CHK_FREE"],
}

# ───────────────────────────────────────────────────────────────
# [고객 단건] 프롬프트: 선택된 코드(룰 기반)를 고정하고, LLM은 이유/요약/액션만 생성
def build_user_messages(row: Dict[str, Any]) -> List[Dict[str, str]]:
    chosen = select_products(row)               # ★ 결정 규칙으로 확정
    flags  = derive_flags(row)
    chosen_verbose = [f"{c} ({_catalog_map[c]['name']})" for c in chosen]

    sys = f"""\
당신은 은행 CRM의 상품 추천 엔진입니다.
아래 '선정된 코드(selected_codes)'는 이미 비즈니스 룰에 의해 결정되었습니다.
당신의 역할은 (1) 고객 특성 요약, (2) 각 코드에 대한 아주 짧은 이유, (3) 다음 액션을 제시하는 것입니다.
규칙:
- 반드시 JSON으로만 응답하십시오(설명 텍스트 금지).
- 'top_products' 배열에는 제공된 selected_codes만 그대로 사용합니다(순서 유지, 다른 코드를 추가/변경 금지).
- 톤: 간결, 실무형, 비차별적.
- 법/내부정책 위반 가능성이 있는 제안은 금지.

JSON 스키마:
{{
  "risk_level": "LOW|MEDIUM|HIGH",
  "summary": "고객 특성 요약 한 줄",
  "top_products": [{{"code": "CHK_FREE", "reason": "간단 근거"}}, ...],
  "next_actions": ["실행 항목", "..."]
}}

[상품 카탈로그]
{_catalog_text()}
"""
    usr = f"""\
고객 특성:
- 지역: {row.get("Geography")}
- 성별: {row.get("Gender")}
- 나이: {row.get("Age")}
- 재직/거래기간(Tenure): {row.get("Tenure")}
- 잔액(Balance): {row.get("Balance")}
- 보유상품수: {row.get("NumOfProducts")}
- 신용카드 보유: {row.get("HasCrCard")}
- 활동회원 여부: {row.get("IsActiveMember")}
- 연봉(추정): {row.get("EstimatedSalary")}
- 신용점수: {row.get("CreditScore")}
- 이탈확률: {float(row.get("churn_probability", 0.0)):.2f}
- 파생 플래그: risk={flags['risk']}, credit={flags['credit_band']}, age_band={flags['age_band']},
              high_balance={flags['high_balance']}, high_income={flags['high_income']},
              inactive={flags['inactive']}, few_products={flags['few_products']}, has_card={flags['has_card']}

selected_codes (순서 고정, 그대로 top_products.code에 사용): {", ".join(chosen_verbose)}
"""
    return [
        {"role": "system", "content": sys},
        {"role": "user",   "content": usr},
    ]

# [세그먼트 집합] 프롬프트: 세그먼트 기본 번들을 고정하고, LLM이 요약/플레이북만 작성
def build_segment_messages(segment_code: str, stats: Dict[str, Any]) -> List[Dict[str, str]]:
    bundle = SEGMENT_BUNDLES.get(segment_code.upper(), ["SAV_PLUS", "CRD_CASH", "CHK_FREE"])
    bundle_verbose = [f"{c} ({_catalog_map[c]['name']})" for c in bundle]

    sys = f"""\
당신은 은행 CRM의 세그먼트 대표 추천 엔진입니다.
아래 'segment_bundle'은 이미 정책에 의해 결정되었습니다. 당신은 요약과 운영 플레이북만 작성합니다.
규칙:
- JSON으로만 응답.
- recommended_bundle에는 제공된 segment_bundle만 사용(순서 유지).
- 플레이북은 실행 가능한 문장 형태 2~4개.
- 톤: 간결, 실무형.

JSON 스키마:
{{
  "segment": "{segment_code}",
  "summary": "세그먼트 특성 한 줄 요약",
  "recommended_bundle": [{{"code": "SAV_HIGH", "reason": "간단 근거"}}, ...],
  "playbook": ["캠페인/오퍼 제안", "..."]
}}

[상품 카탈로그]
{_catalog_text()}
"""
    usr = f"""\
세그먼트: {segment_code}
집계치:
- 고객수: {stats.get("count")}
- 평균 Churn: {stats.get("avg_churn")}
- 평균 R/F/M: {stats.get("avg_r")}/{stats.get("avg_f")}/{stats.get("avg_m")}

segment_bundle (순서 고정, 그대로 recommended_bundle.code에 사용): {", ".join(bundle_verbose)}
"""
    return [
        {"role": "system", "content": sys},
        {"role": "user",   "content": usr},
    ]

# ───────────────────────────────────────────────────────────────
# LLM 호출 + 폴백
USER_SCHEMA = {
    "type": "object",
    "properties": {
        "risk_level": {"type": "string"},
        "summary": {"type": "string"},
        "top_products": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["code", "reason"]
            }
        },
        "next_actions": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["risk_level", "summary", "top_products"]
}

SEG_SCHEMA = {
    "type": "object",
    "properties": {
        "segment": {"type": "string"},
        "summary": {"type": "string"},
        "recommended_bundle": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "reason": {"type": "string"}
                },
                "required": ["code", "reason"]
            }
        },
        "playbook": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["segment", "summary", "recommended_bundle"]
}

def _fallback_user(row: Dict[str, Any]) -> Dict[str, Any]:
    # 간단 룰베이스(LLM 키 없거나 에러 시)
    risk = derive_flags(row)["risk"]
    chosen = select_products(row)
    tops = [{"code": c, "reason": "정책 기반 추천"} for c in chosen]
    return {
        "risk_level": risk,
        "summary": "기본 정책에 따른 추천입니다.",
        "top_products": tops,
        "next_actions": ["담당자 상담 연결", "앱에서 바로 신청 유도"]
    }

def _fallback_segment(segment_code: str) -> Dict[str, Any]:
    bundle = SEGMENT_BUNDLES.get(segment_code.upper(), ["SAV_PLUS", "CRD_CASH", "CHK_FREE"])
    return {
        "segment": segment_code,
        "summary": "정책 기반 번들 추천입니다.",
        "recommended_bundle": [{"code": c, "reason": "세그먼트 표준 번들"} for c in bundle],
        "playbook": ["표준 오퍼 발송", "A/B 테스트로 캠페인 최적화"]
    }

def recommend_for_user(row: Dict[str, Any]) -> Dict[str, Any]:
    if not USE_LLM:
        return _fallback_user(row)
    try:
        return chat_json(build_user_messages(row), schema=USER_SCHEMA)
    except Exception:
        return _fallback_user(row)

def recommend_for_segment(segment_code: str, stats: Dict[str, Any]) -> Dict[str, Any]:
    if not USE_LLM:
        return _fallback_segment(segment_code)
    try:
        return chat_json(build_segment_messages(segment_code, stats), schema=SEG_SCHEMA)
    except Exception:
        return _fallback_segment(segment_code)
