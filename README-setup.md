# Project Setup

## 주의
- python 3.12
  - PyTorch는 공식적으로 Python 3.12까지 안정 지원
  - 단위 범위 : 데이터 분석 / 머신러닝 / 딥러닝 / 모델 검증 및 평가

## SETUP
- 터미널 python version 3.12.6 사용
- 가상 환경 생성
```bash
cd SKN18-2nd-1Team/
uv venv .venv --python=3.12.6
```
- activate venv
```bash
cd SKN18-2nd-1Team/
source .venv/bin/activate   # Mac/Linux
# or
.venv\Scripts\activate      # Windows
```
- requirements 설치
```bash
cd SKN18-2nd-1Team/
uv pip install -r requirements.txt
```
