# SKN18-2nd-1Teams
## 은행 고객 이탈율 분석 시스템

---

## Team Information
Team Name : SKN18기 2ND 1조  

| 이름    | 역할   | 세부 역할              | Github     |
|:------: |:-----: |:-------------------: |:----------:|
| 장이건  | 팀장   | 모델링, 화면개발  | [@poolbbang](https://github.com/poolbbang)  |
| 김준규  | 팀원   | 모델링, 화면개발  | [@JungyuOO](https://github.com/JungyuOO) |
| 김영우  | 팀원   | 모델링, 화면개발    | [@youngwookim1006](https://github.com/youngwookim1006) |
| 박세영  | 팀원   | 모델링, 화면개발  | [@seyung000](https://github.com/seyung000) |
| 황혜진  | 팀원   | 모델링, 화면개발      | [@HJincode](https://github.com/HJincode) |

---

## 프로젝트 기간
📆2025.09.01 ~ 2025.09.08

---

## 🛠️ Stacks
- **Environment**  
![Visual Studio Code](https://img.shields.io/badge/Visual%20Studio%20Code-007ACC?style=for-the-badge&logo=Visual%20Studio%20Code&logoColor=white)  
![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=Git&logoColor=white)  
![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=GitHub&logoColor=white)  

- **Development**  
![Python](https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white)  
![MySQL](https://img.shields.io/badge/mysql-4479A1?style=for-the-badge&logo=mysql&logoColor=white)  
![Streamlit](https://img.shields.io/badge/streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)  
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)  

- **Communication**  
![Discord](https://img.shields.io/badge/discord-5865F2?style=for-the-badge&logo=discord&logoColor=white)  

![alt text](image-7.png)
---

# 프로젝트 개요 
> ## 은행 고객 이탈율 분석
---
최근 금융 산업의 디지털 전환과 경쟁 심화로 인해, **은행 고객 이탈 방지(Customer Retention)**가 중요한 과제로 부상하고 있습니다.

본 프로젝트에서는 은행의 거래 데이터와 고객 정보를 기반으로, 고객의 이탈 여부(Churn)를 사전에 예측하고자 합니다.

이를 위해 고객의 계좌 사용 패턴, 대출 및 카드 이용 내역, 상담 이력 등 다양한 데이터를 분석하고, 이탈 가능성이 높은 고객을 조기에 식별할 수 있는 머신러닝 예측 모델을 개발했습니다.

이 프로젝트는 은행의 맞춤형 금융 상품 제안, 고객 관리, 타겟 마케팅 전략 수립 등에 활용될 수 있는 핵심 인사이트를 제공합니다.

## ✔️ 은행 고객 이탈의 주요 원인 초기 예측

## ✅ 1. 은행 고객 이탈의 구조적 요인 예측 

| 원인 | 설명 |
|------|------|
| ❗ 낮은 고객 신용 점수(CreditScore) | 신용 점수가 낮은 고객은 대출·카드 한도가 제한되고, 불리한 조건 때문에 다른 은행으로 이동할 가능성이 높음 |
| ❗ 짧은 거래 기간(Tenure) | 고객 평균 거래 기간이 짧고, 신규 고객(0~1년)의 이탈률이 높음 → 초기 서비스 경험 부족 시 조기 이탈 위험 |
| ❗ 낮은 금융 상품 다양성(NumOfProducts) | 대부분의 고객이 **1~2개 상품만 이용** → 추가 상품으로 확장되지 않으면 장기 충성 고객으로 이어지기 어려움 |
| ❗ 낮은 활동성(IsActiveMember) | **비활성 고객 비율**이 높아 실제 거래가 단절되는 경우가 많음 → 서비스 관계 유지 실패 |
| ❗ 불만 제기(Complain) | 불만을 제기한 고객은 **이탈 확률이 급격히 상승**하며, 고객 클레임 대응 미흡 시 신뢰도 저하로 이어짐 |

---

## ✅ 2. 고객 개인 특성 요인 예측

| 요인 | 설명 |
|------|------|
| 🔍 연령대 특성(Age) | **젊은 고객층**은 다양한 금융 서비스 실험 후 다른 은행으로 쉽게 이동, **고령층**은 디지털 채널 적응 어려움으로 불편함 경험 |
| 🔍 성별/지역 차이(Gender, Geography) | 특정 지역(Geography) 고객은 경쟁 은행 서비스 선호도가 높고, 성별에 따라 금융 상품 이용 패턴 차이가 발생 |
| 🔍 소득 수준 차이(EstimatedSalary) | 고소득층 고객은 더 나은 조건을 찾아 이탈하고, 저소득층 고객은 수수료·금리에 민감하여 잦은 이탈 발생 |
| 🔍 카드 및 포인트 혜택(Card Type, Point Earned) | 카드 혜택이나 포인트 적립이 부족한 고객은 **경쟁 은행의 리워드 프로그램**으로 이동할 가능성이 높음 |
| 🔍 만족도(Satisfaction Score) | 만족도가 낮은 고객은 장기적으로 이탈 확률이 매우 높으며, 서비스 품질 개선이 이루어지지 않을 경우 충성 고객 전환이 어려움 |

---
### 🎯 프로젝트 목표
- 은행 고객의 정보를 바탕으로 이탈 가능성을 정량적으로 예측하고,
- 실제 이탈 예측율을 기반으로 마케팅/운영 전략에 즉시 활용 가능한 인사이트와 모델을 제공하는 것이 본 프로젝트의 목표입니다.

### 〽️ **프로젝트 기획**
**은행 고객 이탈 예측을 위한 최적의 머신러닝 모델 구축**  
(데이터 전처리 → 피처 엔지니어링 → 모델 학습 및 하이퍼파라미터 튜닝 → 최종 모델 평가)

--- 


###  요구사항
- 은행 고객 이탈 데이터 수집 및 전처리  
- 데이터베이스 설계 및 구축  
- 고객 이탈율 예측 모델 개발 (XGBoost, CatBoost, RandomForest 등)  
- 예측 결과 시각화 및 대시보드 구현  
- 고객 이탈 방지 전략 인사이트 도출  

---
### 데이터셋
- Kaggle Bank Customer Churn Dataset  
- 금융 관련 고객 행동 및 이탈 통계  
- 외부 지표 (경제 지표, 대출/금리 관련 데이터 등)  
- [데이터링크](https://www.kaggle.com/datasets/radheshyamkollipara/bank-customer-churn)

**✅ 원본 데이터셋 구성**

> RowNumber, CustomerId, Surname 은 분석에 사용하지 않으므로 제외

| **변수명**                      | **변수 설명**                                       |
|-------------------------------|----------------------------------------------------|
| `Surname`                     | 고객 성(姓, Last name) — 일부 연구에서는 가족 단위 이탈 가능성을 고려해 사용하기도 함 |
| `CreditScore`                 | 신용 점수 (높을수록 신용도가 높음, 대출·카드 조건에 직접적 영향)                      |
| `Geography`                   | 거주 지역 (예: France, Germany, Spain 등)                                             |
| `Gender`                      | 성별 (Male/Female)                                                                    |
| `Age`                         | 나이 (숫자형, 고객 생애주기별 이탈 요인 분석 가능)                                    |
| `Tenure`                      | 은행 거래 기간(연 단위, 0~10년)                                                       |
| `Balance`                     | 계좌 잔액                                                                             |
| `NumOfProducts`               | 이용 중인 은행 금융상품 개수 (예: 예금, 대출, 신용카드 등)                            |
| `HasCrCard`                   | 신용카드 보유 여부 (1 = 보유, 0 = 없음)                                               |
| `IsActiveMember`              | 활동 고객 여부 (1 = 활동적, 0 = 비활동적)                                             |
| `EstimatedSalary`             | 추정 연봉 (고객 소득 수준, 일반적으로 은행 내부 추정치)                               |
| `Exited`                      | 이탈 여부 (1 = 이탈 고객, 0 = 유지 고객, 타겟 변수)                                   |
| `Complain`                    | 불만 제기 여부 (1 = 불만 있음, 0 = 없음)                                              |
| `Satisfaction Score`          | 고객 만족도 점수 (보통 1~5점 척도)                                                    |
| `Card Type`                   | 보유 카드 종류 (예: Silver, Gold, Platinum 등)                                        |
| `Point Earned`                | 고객이 적립한 포인트 (리워드 프로그램 지표)                                           |

---
# 2. 탐색적 데이터 분석(EDA)

---
### 1. 데이터 전처리 🧹

본 프로젝트에서는 고객 이탈 예측 모델링을 위한 데이터 전처리를 다음과 같이 수행했습니다.

---

#### 1) 불필요 컬럼 제거
- `CustomerId`, `Surname` : 단순 식별자 성격으로 분석 목적과 무관하여 제거

---

#### 2) 타깃 변수 생성
- `Exited` → `target` 으로 재명명  
- 이진 분류 구조 유지 (0 = 유지 고객, 1 = 이탈 고객)

---

#### 3) 결측치 처리
- **수치형 변수** : 평균값으로 대체 (`CreditScore`, `Age`, `Balance`, `EstimatedSalary` 등)  
- **범주형 변수** : 최빈값(Mode)으로 대체 (`Geography`, `Gender`, `Card Type` 등)  
- 👉 데이터 손실을 최소화하고 전체 분포를 유지하는 방향

---

#### 4) 범주형 인코딩
- `Geography`, `Age_Group`, `Satisfaction_Level`, `Card Type` 등은 One-Hot Encoding  
- 단순 참/거짓(binary) 변수는 그대로 유지 (`IsActiveMember`, `Senior_Flag` 등)

---

#### 5) 파생 피처 생성 (Feature Engineering)
- **구간화/Flag**
  - `Age_Group` : 연령대(18–30, 31–40, 41–50, 51+) 구간화
  - `Senior_Flag` : 45세 이상 여부
  - `Satisfaction_Level` : 만족도 점수(1–2 = Low, 3–4 = Medium, 5 = High)
  - `Germany_Flag` : 독일 고객 여부

- **비율/상호작용**
  - `Balance_per_Product` : 고객 잔액 ÷ 보유 상품 수
  - `Germany_HighBalance` : 독일 + 중앙값 초과 잔액 고객
  - `LowActive_LowProduct` : 비활동 + 상품 1개 고객 (고위험군)

- **조합형 범주 (One-Hot 대상)**
  - `ia_x_card` : IsActiveMember × HasCrCard
  - `geo_x_gender` : Geography × Gender
  - `agebin_x_salbin` : 연령 구간 × 소득 구간
  - `tenbin_x_ia` : 근속연수 구간 × 활동 여부
  - `cardtype_x_ia` : Card Type × 활동 여부

- **수치형 상호작용**
  - `age_x_balance` : Age × Balance
  - `age_x_products` : Age × NumOfProducts
  - `balance_x_products` : Balance × NumOfProducts

---
#### 6) 학습용 데이터셋 구성 (Feature Engineering)
| **변수명**                      | **변수 설명**                                       |
|-------------------------------|----------------------------------------------------|
| `Exited`                     | (타깃변수)고객 이탈 여부 (0 = 유지, 1 = 이탈) |
| `Geography`                 | 고객 거주 지역 (France, Germany, Spain 등)                     |
| `Gender`                   | 거주 지역 (예: France, Germany, Spain 등)                                             |
| `Age`                      | 성별 (Male/Female)                                                                    |
| `Balance`                         | 계좌 잔액                               |
| `NumOfProducts`                      | 보유 중인 금융상품 개수                                                      |
| `IsActiveMember`                     | 활동 회원 여부 (1 = 활동, 0 = 비활동)                                         |
| `ia_x_card`               | 활동성(IsActiveMember) × 신용카드 보유 여부(HasCrCard) 상호작용 변수                            |
| `geo_x_gender`                   | 지역(Geography) × 성별(Gender) 상호작용 변수                                            |
| `agebin_x_salbin`              | 연령대 구간(Age bin) × 소득 구간(Salary bin) 상호작용 변수                                             |
| `cardtype_x_ia`             | 카드 유형(Card Type) × 활동성(IsActiveMember) 상호작용 변수                               |
| `Germany_Flag`                      | 독일 거주 고객 여부 (Germany = 1, else 0)                                   |

---

#### 7) 데이터 분할
- 학습/테스트 = **7 : 3 비율**  
- `stratified_split` 활용, 타깃 비율이 유지되도록 계층적 분할(Stratified Split) 적용
- 교차검증 시 **Stratified K-Fold (5-fold)** 사용

#### 8) EDA 과정 도표화(참고)
- Histogram
---

<img src="3-application/assets/img/eda/histogram/1-eda-histogram1.png" width="300"/>
<img src="3-application/assets/img/eda/histogram/1-eda-histogram2.png" width="300"/>
<img src="3-application/assets/img/eda/histogram/1-eda-histogram3.png" width="300"/>
<img src="3-application/assets/img/eda/histogram/1-eda-histogram4.png" width="300"/>
<img src="3-application/assets/img/eda/histogram/1-eda-histogram5.png" width="300"/>
<img src="3-application/assets/img/eda/histogram/1-eda-histogram6.png" width="300"/>

- Box plot
---

<img src="3-application/assets/img/eda/outlier/boxplot1.png" width="300"/>
<img src="3-application/assets/img/eda/outlier/boxplot2.png" width="300"/>
<img src="3-application/assets/img/eda/outlier/boxplot3.png" width="300"/>
<img src="3-application/assets/img/eda/outlier/boxplot4.png" width="300"/>
<img src="3-application/assets/img/eda/outlier/boxplot5.png" width="300"/>
<img src="3-application/assets/img/eda/outlier/boxplot6.png" width="300"/>
<img src="3-application/assets/img/eda/outlier/boxplot7.png" width="300"/>
<img src="3-application/assets/img/eda/outlier/boxplot8.png" width="300"/>

- Shap
---
<img src="3-application/assets/img/eda/shap/shap1.png" width="300"/>

- Confusion Matrix
---
<img src="3-application/assets/img/eda/confusion_matrix/cm1.png" width="300"/>

##  ERD
![alt text](3-application/assets/img/Customer_churn_score_ERD.png)
---

# 3. 화면 Prototype

---

## 화면 구성 (Prototype)
### 1. 메인 모델링 화면
![alt text](3-application/assets/img/Readme_prototype_page1.png)

---


### 2. 사용자 이탈율 화면 
![alt text](3-application/assets/img/Readme_prototype_page2_1.png)
![alt text](3-application/assets/img/Readme_prototype_page2_2.png)
![alt text](3-application/assets/img/Readme_prototype_page2_3.png)

---


### 3. RFM 화면
![alt text](3-application/assets/img/Readme_prototype_page3.png)

---


### 4. 데이터 도구 화면 
![alt text](3-application/assets/img/Readme_prototype_page4.png)


---
# 4. ML 학습 결과서

---

## 📊 1. 사용한 예측 모델  

| 모델 종류 | 설명 |
|-----------|------|
| 🌲 **Random Forest (RF)** | 여러 개의 결정 트리를 결합한 앙상블 모델로 안정적인 성능 제공 |
| 🚀 **XGBoost** | 빠르고 성능이 우수한 그래디언트 부스팅 모델 |
| 🐱 **CatBoost** | 범주형 데이터 처리에 강점이 있는 Gradient Boosting 기반 모델 |

---

## 📊 1-2. 모델 성능 비교  

모델 평가 지표는 **5-Fold 교차검증(OOF, Out-Of-Fold)** 기준으로 산출하였으며, 주요 평가지표는 다음과 같습니다.

| 지표 | 설명 |
|------|------|
| ✅ **Accuracy** | 전체 분류 정확도 (모든 예측 중 정답 비율) |
| 🎯 **Recall** | 실제 이탈자를 얼마나 잘 잡았는가 (FN ↓) |
| ⚠️ **Precision** | 예측된 이탈자 중 실제로 이탈한 비율 |
| 🔁 **F1-score** | Precision과 Recall의 조화 평균 (두 지표의 균형 평가) |
| 📈 **ROC_AUC** | 분류 모델의 종합적인 판별력 (AUC-ROC 곡선 면적) |

---

## 🏆 2. 최종 선정 모델: **CatBoost**

CatBoost가 다른 모델 대비 가장 높은 F1-score를 기록하여 **최종 예측 모델**로 선정되었습니다.  

### 📌 CatBoost 성능 요약 (5-Fold OOF, No SMOTE)
- **ACC** : 0.8487 ± 0.0062  
- **F1** : 0.6344 ± 0.0119  
- **Precision** : 0.6254 ± 0.0166  
- **Recall** : 0.6438 ± 0.0114  
- **ROC_AUC** : 0.8708 ± 0.0062  
- **최적 Threshold** : 0.620  

---

### 📌 SMOTE 적용 여부 비교
- 데이터 불균형 완화를 위해 **SMOTE(합성 샘플링)**을 적용한 버전도 실험  
- 그러나 CatBoost는 `auto_class_weights='Balanced'`만 적용했을 때 **Accuracy와 F1-score가 더 높게** 나타남  
- 따라서 **최종 모델에서는 SMOTE를 사용하지 않고, CatBoost + Balanced weight 조합을 선택**

---

### 📌 선정 이유
- 세 모델(RandomForest, XGBoost, CatBoost) 중 **F1-score와 ROC_AUC가 가장 우수**  
- **이탈 고객(양성 클래스, Exited=1)**에 대한 Recall 확보와 Precision 간 균형이 뛰어남  
- SMOTE를 적용하지 않은 CatBoost 모델이 **더 높은 성능**을 보여 최종 선정  
- 전체 성능 지표의 균형이 좋아 **실제 비즈니스 적용 시 안정적인 예측 성능 기대 가능**

---

# 5. RFM 분석 기반 고객 세분화

본 프로젝트에서는 고객의 거래 데이터를 바탕으로 **RFM 분석**을 수행하고, 이를 이탈 예측 결과와 결합하여 고객을 그룹화하였습니다.  
RFM 분석은 고객을 **Recency(📅 최근성), Frequency(🔁 거래 빈도), Monetary(💰 거래금액/잔액)** 기준으로 평가하여 **가치 기반 고객 세그먼트**를 정의하는 방법입니다.  

---

## 📐 RFM 항목 정의 및 스코어링 방식

- **Recency (R)** : 마지막 거래 이후 경과 일수  
  → 최근에 거래한 고객일수록 높은 점수를 부여 (최근 거래일 가까움 = 높은 점수)  

- **Frequency (F)** : 특정 기간 내 거래 횟수 (상품 수, 거래 빈도 등)  
  → 거래 빈도가 높을수록 높은 점수를 부여  

- **Monetary (M)** : 일정 기간 내 거래금액 또는 평균 잔액  
  → 거래 규모가 클수록 높은 점수를 부여  

**스코어 산정 방식**  
- 각 지표별로 고객 분포를 기반으로 **1~5점 구간화**(Quantile 기반 Scoring)  
- 예: Recency의 경우 상위 20% 최근 거래 고객 → 5점, 가장 오래된 20% 고객 → 1점  
- 동일한 방식으로 Frequency, Monetary도 각각 **분위수 기반 1~5점**으로 점수화  
- 최종적으로 고객별 `(r_score, f_score, m_score)`를 부여  

---

## 🎯 분석 목적
- 고객을 **행동 데이터(RFM) + 예측된 이탈 확률**로 세분화  
- 단순 이탈 예측을 넘어, **충성 고객 관리 / 위험 고객 사전 대응 / 저활성 고객 재활성화** 등 맞춤형 전략 수립  
- 대시보드에서 **AI 추천 전략 모달(LLM)**을 연동해 각 세그먼트별로 자동화된 대응 전략 제안  

---

## 📦 고객군 분류

고객은 RFM 스코어와 예측 이탈 확률(`churn_probability`)을 기반으로 **4개 그룹**으로 세분화되었습니다.

| 그룹 | 고객수 | 평균 R/F/M | 평균 Churn | 특성 요약 |
|------|--------|------------|------------|-----------|
| 👑 **VIP (핵심 고객)** | 530 | 4.5 / 5.0 / 4.5 | 22.0% | 최근 거래 활발, 거래빈도 및 금액 모두 높은 핵심 고객 |
| 💎 **LOYAL (충성 고객)** | 1,376 | 4.5 / 4.9 / 1.5 | 11.5% | 거래 빈도 높지만 거래금액은 낮은 충성 고객 |
| ⚠ **AT_RISK (위험 고객)** | 1,599 | 1.5 / 2.7 / 4.5 | 26.5% | 일정 금액은 있지만 거래 빈도 낮고 최근성도 낮음 → 이탈 위험 ↑ |
| 💤 **LOW (저활성 고객)** | 6,495 | 2.9 / 2.5 / 2.8 | 23.8% | 거래 빈도와 금액 모두 낮아 기여도가 낮은 그룹 |

---

# 6. Streamlit 화면 구현
### ✅ 대시보드 홈 페이지 (메인)

![alt text](image-1.png)

### ✅ ML 시각화 

![alt text](image-2.png)

### ✅ 고객 이탈율
![alt text](image-3.png)

### ✅ 고객 그룹(RFM)
![alt text](image-4.png)

### ✅ AI 고객 이탈 방지 전략 
![alt text](image-5.png)

### ✅ 데이터 도구
![alt text](image-6.png)

---
# ✔️ 은행 고객 이탈의 주요 원인
## ✅ 1. 은행 고객 이탈의 구조적 요인  
---

| 원인 | 설명 |
|------|------|
| ❗ 낮은 금융 상품 다양성(NumOfProducts) | 대부분 고객이 **1~2개 상품만 이용** → 상품 확장이 되지 않으면 장기 충성 고객으로 이어지기 어려움 |
| ❗ 낮은 고객 신용 점수(CreditScore) | 신용 점수가 낮은 고객은 대출·카드 한도가 제한되고, 불리한 조건 때문에 다른 은행으로 이동할 가능성이 높음 |
| ❗ 짧은 거래 기간(Tenure) | 거래 기간이 짧은 신규 고객(0~1년)의 이탈률이 높음 → 초기 서비스 경험 부족 시 조기 이탈 위험 |
| ❗ 낮은 활동성(IsActiveMember) | **비활성 고객 비율**이 높아 실제 거래 단절이 빈번 → 서비스 관계 유지 실패 |
| ❗ 고위험 패턴(LowActive_LowProduct) | 비활동성이면서 상품이 1개뿐인 고객은 이탈 확률이 특히 높음 |

---

## ✅ 2. 고객 개인 특성 요인  

| 요인 | 설명 |
|------|------|
| 🔍 연령대 특성(Age, Age_Group) | **젊은 고객층**은 금융 서비스 이동성이 높고, **고령 고객층(45세 이상)**은 `Senior_Flag`에 해당되어 디지털 채널 적응에 어려움을 겪는 경우가 많음 |
| 🔍 지역 차이(Geography, Germany_Flag) | 독일(Germany) 고객은 이탈 위험이 상대적으로 높게 나타남. 특히 `Balance`가 중위값 이상인 고잔액 독일 고객(`Germany_HighBalance`)은 경쟁 은행으로 이동할 가능성이 큼 |
| 🔍 성별 차이(Gender, geo_x_gender) | 성별에 따라 금융상품 이용 패턴이 다르며, 특정 성별과 지역이 결합될 경우 이탈 위험이 높아짐 |
| 🔍 계좌 잔액(Balance, Balance_per_Product) | 보유 상품 대비 잔액이 낮은 고객은 은행 활용도가 낮아 이탈 가능성이 높음 |
| 🔍 만족도(Satisfaction Score, Satisfaction_Level) | 만족도가 낮은 고객(`Low`)은 장기 충성 고객으로 전환되기 어려움. 서비스 품질 개선이 필수적임 |

---

## 📊 인사이트


1. **고객 특성별 이탈 패턴**  
   - 연령대: 젊은 고객은 이동성이 높아 쉽게 이탈, 고령 고객은 디지털 채널 적응 어려움으로 불편을 경험  
   - 활동성/상품 수: **비활동 고객 + 단일 상품 보유** 조합은 이탈 위험이 가장 높음  
   - 지역/성별: 독일 고객(`Germany_Flag`)에서 이탈률이 유의미하게 높고, 성별·지역 상호작용(`geo_x_gender`)도 이탈 확률에 영향  

2. **이탈 주요 요인**  
   - 신용 점수(CreditScore): 낮은 점수일수록 금융 제약이 커 이탈 확률 상승  
   - 계좌/상품 활용도(Balance_per_Product): 상품 대비 잔액이 낮으면 은행 관계가 약화  
   - 만족도(Satisfaction Score): Low 그룹 고객은 장기 충성 고객으로 전환되기 어려움  
   - 불만·거래 단절: 불만 제기나 거래 단절 상태 고객은 신뢰도 저하로 이탈 가속  

3. **예측 모델 성능 비교**  
   - RandomForest, XGBoost, CatBoost 세 모델을 비교한 결과 **CatBoost**가 F1-score (0.634)와 ROC-AUC (0.871)에서 가장 우수  
   - SMOTE 적용 실험 결과 성능 저하 → CatBoost의 `auto_class_weights="Balanced"` 전략이 최적  
   - Threshold 최적화로 단순 Accuracy가 아닌 **Recall·F1 중심의 성능 향상**을 달성  

4. **RFM 분석과 결합한 고객 세분화**  
   - RFM(Recency, Frequency, Monetary) + 이탈확률을 결합하여 **VIP / LOYAL / AT_RISK / LOW** 네 그룹으로 분류  
   - 각 그룹별 페르소나와 전략:  
     - 👑 **VIP**: 자산·빈도 모두 높은 핵심 고객 → 로열티 강화, 맞춤형 자산관리  
     - 💎 **LOYAL**: 빈도 높고 금액 낮은 고객 → 업셀링·교차판매  
     - ⚠ **AT_RISK**: 일정 금액은 있으나 활동 저조 → 이탈 방지 프로모션  
     - 💤 **LOW**: 활동·금액 모두 낮음 → 재활성화 캠페인  

---

✅ **결론**  
단순히 “누가 이탈할까?”를 예측하는 수준을 넘어,  
**고객 특성과 주요 이탈 요인을 데이터로 검증**하고,  
**RFM 세분화와 결합한 맞춤형 마케팅 전략**까지 도출할 수 있었습니다.  
이를 통해 고객 생애가치(LTV)를 극대화하고, 은행의 **데이터 기반 리텐션 전략** 수립에 활용 가능합니다.

##  오류 목록
- GitHub Issues를 통해 관리

[GitHub Issues](https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN18-2nd-1Team/issues?q=is%3Aissue%20state%3Aclosed)

---

## 느낀점 
- 장이건 : 스트림릿, 머신러닝, MySQL 등 지금까지 배운 요소들을 조합해서 만들다 보니 좋은 복습기회였던 것 같습니다. 다들 고생하셨습니다.
---
- 김준규 : 이번 프로젝트를 통해 단순 예측을 넘어 고객 특성별 이탈 요인을 구체적으로 파악하고, RFM 세분화를 활용해 맞춤 전략까지 도출할 수 있음을 배웠습니다. 팀원분들이 열심히 참여해주신 덕분에 프로젝트를 잘 해낼 수 있었습니다. 그동안 다들 고생많으셨습니다.
---
- 김영우 : 우리팀 짱!!! ㅋㅋㅋ 헤어지고 싶지 않은팀이었다 ㅋㅋㅋ 헤어지지 말자!!! 남은 3차4차 까지 이어지기를 ㅋㅋㅋ
---
- 박세영 : Issue 관리를 통해 프로젝트의 진행 상황을 명확히 파악할 수 있었으며, Git 충돌 상황에서는 팀원의 도움으로 문제를 해결하면서 버전 관리에 대한 이해를 넓혔습니다. 이 과정에서 Git graph 사용에 한층 익숙해졌고, 향후에는 fork 기반의 워크플로우를 적용해보고 싶다는 생각도 하게 되었으며, 동시에 침착하게 문제를 원복하는 태도 역시 조금 더 자리 잡게 되었습니다. 또한 협업 과정에서는 코드 스타일을 팀과 맞추는 중요성을 체감하며, 코드 일관성의 가치를 깊이 느낄 수 있었습니다.
---
- 황혜진 : 데이터 적재부터 시각화까지 전 과정을 직접 구현하며, 단순한 분석이 아니라 실제 시스템으로 연결하는 경험의 중요성을 깨달았습니다
---
