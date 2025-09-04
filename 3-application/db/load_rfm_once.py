# load_rfm_once.py
# ------------------------------------------------------------
# 목적: 고객 CSV를 DB에 적재하고 RFM 테이블(rfm_result_once) 생성
# 입력: assets/data/Customer-Churn-Records.csv
# 출력: MySQL 테이블
#   - stg_bank_churn (원본 고객 데이터)
#   - rfm_result_once (R/F/M 점수 + 세그먼트)
#   - stg_churn_score (빈껍데기, 이후 full_scoring.py가 채움)
# ------------------------------------------------------------
import os
import csv
import pymysql
from pathlib import Path

# =========================
# Config (환경변수 오버라이드 가능)
# =========================
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "root1234")
DB_NAME = os.getenv("DB_NAME", "sknproject2")

BANK_CSV = os.getenv("BANK_CSV", str(Path(__file__).resolve().parents[1] / "assets" / "data" / "Customer-Churn-Records.csv"))

# =========================
# DB Connection
# =========================
def connect(db=None):
    return pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS,
        database=db, charset="utf8mb4", autocommit=True
    )

# =========================
# 테이블 DDL
# =========================
DDL_STG = """
DROP TABLE IF EXISTS stg_bank_churn;
CREATE TABLE stg_bank_churn (
  RowNumber        INT,
  CustomerId       BIGINT,
  Surname          VARCHAR(100),
  CreditScore      INT,
  Geography        VARCHAR(32),
  Gender           VARCHAR(16),
  Age              INT,
  Tenure           INT,
  Balance          DECIMAL(18,2),
  NumOfProducts    INT,
  HasCrCard        TINYINT,
  IsActiveMember   TINYINT,
  EstimatedSalary  DECIMAL(18,2),
  Exited           TINYINT,
  _loaded_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_stg_customer (CustomerId),
  INDEX ix_stg_exited (Exited)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

DDL_RFM = """
DROP TABLE IF EXISTS rfm_result_once;
CREATE TABLE rfm_result_once (
  customer_id     BIGINT PRIMARY KEY,
  surname         VARCHAR(100) NULL,
  recency_days    INT NOT NULL,
  frequency_90d   INT NOT NULL,
  monetary_90d    DECIMAL(18,2) NOT NULL,
  r_score         TINYINT NOT NULL,
  f_score         TINYINT NOT NULL,
  m_score         TINYINT NOT NULL,
  rfm_code        CHAR(3) NOT NULL,
  segment_code    VARCHAR(32) NOT NULL,
  _built_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

DDL_SCORE = """
DROP TABLE IF EXISTS stg_churn_score;
CREATE TABLE stg_churn_score (
  customer_id        BIGINT NOT NULL,
  churn_probability  DECIMAL(9,6),
  _scored_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# =========================
# CSV 적재 함수
# =========================
def load_stg_from_csv(cur, csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        batch = []
        insert_sql = """
        INSERT INTO stg_bank_churn
        (RowNumber, CustomerId, Surname, CreditScore, Geography, Gender, Age, Tenure,
         Balance, NumOfProducts, HasCrCard, IsActiveMember, EstimatedSalary, Exited)
        VALUES
        (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        for r in reader:
            vals = [
                r.get("RowNumber"), r.get("CustomerId"), r.get("Surname"),
                r.get("CreditScore"), r.get("Geography"), r.get("Gender"),
                r.get("Age"), r.get("Tenure"), r.get("Balance"),
                r.get("NumOfProducts"), r.get("HasCrCard"), r.get("IsActiveMember"),
                r.get("EstimatedSalary"), r.get("Exited"),
            ]
            batch.append(vals)
            if len(batch) >= 1000:
                cur.executemany(insert_sql, batch)
                batch.clear()
        if batch:
            cur.executemany(insert_sql, batch)

# =========================
# RFM 계산 (간단 버전)
# =========================
SQL_RFM_INSERT = """
INSERT INTO rfm_result_once
(customer_id, surname, recency_days, frequency_90d, monetary_90d,
 r_score, f_score, m_score, rfm_code, segment_code)
SELECT
  CustomerId,
  Surname,
  GREATEST(0, (3650 - Tenure*365)) AS recency_days,
  NumOfProducts AS frequency_90d,
  Balance       AS monetary_90d,
  -- 점수 구간화(단순 5분위)
  NTILE(5) OVER (ORDER BY (3650 - Tenure*365) DESC) AS r_score,
  NTILE(5) OVER (ORDER BY NumOfProducts ASC)        AS f_score,
  NTILE(5) OVER (ORDER BY Balance ASC)              AS m_score,
  CONCAT(
    NTILE(5) OVER (ORDER BY (3650 - Tenure*365) DESC),
    NTILE(5) OVER (ORDER BY NumOfProducts ASC),
    NTILE(5) OVER (ORDER BY Balance ASC)
  ) AS rfm_code,
  CASE
    WHEN NumOfProducts >= 3 AND Balance > 100000 THEN 'VIP'
    WHEN NumOfProducts >= 2 THEN 'LOYAL'
    WHEN Balance > 50000 THEN 'AT_RISK'
    ELSE 'LOW'
  END AS segment_code
FROM stg_bank_churn;
"""

# =========================
# 메인
# =========================
def main():
    print(f"[INFO] Using CSV: {BANK_CSV}")
    if not Path(BANK_CSV).exists():
        raise FileNotFoundError(f"CSV not found: {BANK_CSV}")

    # DB 생성 보장
    conn = connect()
    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} DEFAULT CHARACTER SET utf8mb4;")
    conn.close()

    conn = connect(DB_NAME)
    try:
        with conn.cursor() as cur:
            print(">> Create tables...")
            cur.execute(DDL_STG)
            cur.execute(DDL_RFM)
            cur.execute(DDL_SCORE)

            print(">> Load stg_bank_churn...")
            load_stg_from_csv(cur, BANK_CSV)

            print(">> Build RFM...")
            cur.execute("SET sql_mode=(SELECT REPLACE(@@sql_mode,'ONLY_FULL_GROUP_BY',''));")
            cur.execute("DROP TEMPORARY TABLE IF EXISTS tmp;")
            cur.execute("TRUNCATE rfm_result_once;")
            cur.execute(SQL_RFM_INSERT)

        print("✅ Done. Tables created:")
        print(" - stg_bank_churn")
        print(" - rfm_result_once")
        print(" - stg_churn_score (empty, to be filled by full_scoring.py)")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
