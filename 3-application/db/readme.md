
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