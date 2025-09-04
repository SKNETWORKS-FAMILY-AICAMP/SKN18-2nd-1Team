
#  DB 최초 한 번 적재 
> 데이터셋 -> 데이터베이스 
> 데이터도구 페이지에서 호출 예정
- 확인 사항 : 도커 실행 -> mysql 실행
```bash
cd SKN18-2nd-1Team/
python ./3-application/db/csv_to_db.py
```

# RFM 데이터 확인
> 화면 실행해서 데이터 확인 가능
```bash
cd SKN18-2nd-1Team/
streamlit run ./3-application/pages/customer_rfm.py
```
 
## 은행에서도 RFM을 쓰나?
은행은 고객이 직접 돈을 쓰거나 입금·출금하는 행동 데이터를 풍부하게 가지고 있습니다.
고객 가치(LTV, Lifetime Value)를 평가하려면,
- 얼마나 오랫동안 관계를 유지했는지 (Recency)
- 얼마나 다양하고 자주 서비스를 쓰는지 (Frequency)
- 얼마나 많은 수익/거래를 창출하는지 (Monetary)
이 3요소가 핵심이며 고객 세분화에 이용

## 🔹 BCMS RFM
- 핵심 고객(VIP) > 충성 고객(LOYAL) > 위험 고객(AT_RISK) > 저활성 고객(LOW)
- R/F/M 점수 산출 기준 : tmp_rfm → tmp_scored 참고
  - 1. ==Recency (최근성)==
    - (6 - NTILE(5) OVER (ORDER BY recency_days DESC)) AS r_score
    - Kaggle Bank Churn 데이터에는 실제 거래일시가 없기 때문에 **Tenure(거래 년수)**를 사용.
    - Tenure가 클수록 오래 거래 → 최근성이 낮다고 가정.
    - 임의로 3650 – Tenure×365를 넣어서 “최근성 지표” 비슷하게 만든 것.
    - Tenure=10 → recency_days ≈ 0 (아주 최근/충성)
    - Tenure=0 → recency_days ≈ 3650 (아주 오래됨 → 최근성 낮음)
  - 2. ==Frequency (빈도)==
    - COALESCE(s.NumOfProducts, 0) AS frequency_90d
    - 실제 거래 횟수가 없으므로 **보유 상품 개수(NumOfProducts)**를 빈도의 대용값으로 사용.
    - 상품이 많을수록 은행과의 접점이 많다고 가정.
    - f_score : 상품 개수를 기준으$$로 5등분 → 많을수록 높은 점수.
  - 3. ==Monetary (M: 금액)==
    - COALESCE(s.Balance, 0.0) AS monetary_90d
    - 실제 최근 90일 금액이 없으므로 **잔액(Balance)**을 금액 가치의 대용값으로 사용.
    - m_score : 잔액 기준으로 5등분 → 금액이 클수록 높은 점수
- RFM 평균 R=3.0 / F=3.0 / M=3.0 이라는 건
  - 전체 고객의 평균적인 위치가 정확히 중간값이라는 뜻이에요.
  - 즉, 대부분 고객이 **너무 우수하지도, 너무 저활성도 아닌 “중간층”** 에 몰려 있다는 의미로 해석할 수 있습니다.
  - 활용 인사이트
    - 고객 풀 전체가 평균적 수준에 고르게 분포되어 있다고 볼 수 있음.
    - 만약 VIP(4~5점) 고객 비율을 늘리고 싶다면,
    - R을 높이는 전략: 리텐션 마케팅(재방문 유도)
    - F를 높이는 전략: 구매 주기 단축(구독/혜택)
    - M을 높이는 전략: 업셀링/크로스셀링

