#csv_to db.py
import os
import sys
import csv
import pymysql
from pathlib import Path

# =========================
# Config (env overridable)
# =========================
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "root1234")
DB_NAME = os.getenv("DB_NAME", "sknproject2")

# 필수: Churn 원본 CSV 경로(자동 탐색 지원: resolve_bank_csv())
BANK_CSV_ENV = os.getenv("BANK_CSV", "")
# 선택: 모델 점수 CSV (컬럼: customer_id,churn_probability) — RowNumber일 경우 자동 보정함
SCORE_CSV = os.getenv("SCORE_CSV") or str(
    Path(__file__).resolve().parents[1] / "assets" / "data" / "churn_scores.csv"
)

# =========================
# Helpers
# =========================
def resolve_bank_csv():
    """BANK_CSV 우선순위:
    1) 환경변수 BANK_CSV
    2) 스크립트 기준 추정 경로들
    3) 상위 트리에서 파일명 검색
    """
    if BANK_CSV_ENV:
        p = Path(BANK_CSV_ENV).expanduser().resolve()
        if p.exists():
            return str(p)

    here = Path(__file__).resolve()
    root = here.parent  # .../ (스크립트 상위)
    candidates = [
        root / "assets" / "data" / "Customer-Churn-Records.csv",
        root.parent / "2-application" / "assets" / "data" / "Customer-Churn-Records.csv",
        root.parent / "3-application" / "assets" / "data" / "Customer-Churn-Records.csv",
    ]
    for c in candidates:
        if c.exists():
            return str(c.resolve())

    # filename search up to 3 parents
    for parent in [here.parent, here.parent.parent, here.parent.parent.parent]:
        for path in parent.rglob("Customer-Churn-Records.csv"):
            return str(path.resolve())

    raise FileNotFoundError(
        "[ERROR] BANK_CSV not found.\n"
        f"- current working dir: {Path.cwd()}\n"
        f"- tried env BANK_CSV={BANK_CSV_ENV}\n"
        "👉 Set BANK_CSV env to absolute path or place file under assets/data/"
    )

def connect():
    # local_infile client flag enables LOAD DATA LOCAL INFILE when server allows it
    return pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS,
        database=DB_NAME, charset="utf8mb4", autocommit=True,
        client_flag=pymysql.constants.CLIENT.LOCAL_FILES
    )

def exec_multi(cur, sql):
    for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
        cur.execute(stmt + ";")

# def load_csv_via_local_infile(cur, table, csv_path, columns):
#     q = f"""
#     LOAD DATA LOCAL INFILE %s
#     INTO TABLE {table}
#     FIELDS TERMINATED BY ',' ENCLOSED BY '"'
#     LINES TERMINATED BY '\\n'
#     IGNORE 1 LINES
#     ({columns});
#     """
#     # 세션에서 local_infile 켜보되, 서버가 GLOBAL만 허용해도 예외처리로 폴백함
#     try:
#         cur.execute("SET SESSION local_infile=1;")
#     except Exception:
#         pass
#     cur.execute(q, (csv_path,))
def load_csv_via_local_infile(cur, table, csv_path, columns):
    q = f"""
    LOAD DATA LOCAL INFILE %s
    REPLACE
    INTO TABLE {table}
    FIELDS TERMINATED BY ',' ENCLOSED BY '"'
    LINES TERMINATED BY '\\n'
    IGNORE 1 LINES
    ({columns});
    """
    try:
        cur.execute("SET SESSION local_infile=1;")
    except Exception:
        pass
    cur.execute(q, (csv_path,))


def load_csv_row_by_row(cur, table, csv_path, insert_sql, expected_cols):
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        batch = []
        for r in reader:
            vals = [r.get(col, None) for col in expected_cols]
            batch.append(vals)
            if len(batch) >= 1000:
                cur.executemany(insert_sql, batch)
                batch.clear()
        if batch:
            cur.executemany(insert_sql, batch)

# =========================
# SQL blocks
# =========================
# DDL_STG = """
# DROP TABLE IF EXISTS stg_bank_churn;
# CREATE TABLE stg_bank_churn (
#   RowNumber        INT,
#   CustomerId       BIGINT,
#   Surname          VARCHAR(100),
#   CreditScore      INT,
#   Geography        VARCHAR(32),
#   Gender           VARCHAR(16),
#   Age              INT,
#   Tenure           INT,
#   Balance          DECIMAL(18,2),
#   NumOfProducts    INT,
#   HasCrCard        TINYINT,
#   IsActiveMember   TINYINT,
#   EstimatedSalary  DECIMAL(18,2),
#   Exited           TINYINT,
#   _loaded_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
#   INDEX ix_stg_customer (CustomerId),
#   INDEX ix_stg_exited (Exited)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
# """
DDL_CUSTOMER = """
DROP TABLE IF EXISTS bank_customer;
CREATE TABLE bank_customer (
  RowNumber        INT NOT NULL,
  CustomerId       BIGINT NOT NULL,
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
  PRIMARY KEY (CustomerId),
  UNIQUE KEY uk_rownum (RowNumber),
  KEY ix_geo (Geography),
  KEY ix_exited (Exited),
  KEY ix_surname (Surname)
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
  _built_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_rfm_segment (segment_code),
  INDEX ix_rfm_scores (m_score, r_score, f_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

DDL_SCORE = """
DROP TABLE IF EXISTS stg_churn_score;
CREATE TABLE stg_churn_score (
  customer_id        BIGINT NOT NULL,
  churn_probability  DECIMAL(9,6) NOT NULL,
  _scored_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (customer_id),
  INDEX ix_score_prob (churn_probability)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

SQL_TMP_RFM = """
DROP TEMPORARY TABLE IF EXISTS tmp_rfm;
CREATE TEMPORARY TABLE tmp_rfm AS
SELECT
  s.CustomerId                                   AS customer_id,
  s.Surname                                      AS surname,
  GREATEST(0, (3650 - COALESCE(s.Tenure,0)*365)) AS recency_days,
  COALESCE(s.NumOfProducts, 0)                   AS frequency_90d,
  COALESCE(s.Balance, 0.0)                       AS monetary_90d
FROM bank_customer s;   -- ✅ 변경
"""

SQL_TMP_SCORED = """
DROP TEMPORARY TABLE IF EXISTS tmp_scored;
CREATE TEMPORARY TABLE tmp_scored AS
SELECT
  customer_id,
  surname,
  recency_days, frequency_90d, monetary_90d,
  (6 - NTILE(5) OVER (ORDER BY recency_days DESC)) AS r_score,
  NTILE(5) OVER (ORDER BY frequency_90d ASC)       AS f_score,
  NTILE(5) OVER (ORDER BY monetary_90d ASC)        AS m_score
FROM tmp_rfm;
"""

SQL_INSERT_RFM = """
INSERT INTO rfm_result_once (
  customer_id, surname, recency_days, frequency_90d, monetary_90d,
  r_score, f_score, m_score, rfm_code, segment_code
)
SELECT
  customer_id, surname, recency_days, frequency_90d, monetary_90d,
  r_score, f_score, m_score,
  CONCAT(r_score, f_score, m_score) AS rfm_code,
  CASE
    WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'VIP'
    WHEN r_score >= 4 AND f_score >= 4                     THEN 'LOYAL'
    WHEN r_score <= 2 AND m_score >= 4                     THEN 'AT_RISK'
    ELSE 'LOW'
  END AS segment_code
FROM tmp_scored
ON DUPLICATE KEY UPDATE
  recency_days  = VALUES(recency_days),
  frequency_90d = VALUES(frequency_90d),
  monetary_90d  = VALUES(monetary_90d),
  r_score       = VALUES(r_score),
  f_score       = VALUES(f_score),
  m_score       = VALUES(m_score),
  rfm_code      = VALUES(rfm_code),
  segment_code  = VALUES(segment_code),
  _built_at     = CURRENT_TIMESTAMP;
"""

# RowNumber로 들어온 점수 CSV를 CustomerId 기준으로 정규화
SQL_FIX_SCORE_IDS = """
ALTER TABLE stg_churn_score
  ADD COLUMN src_id BIGINT NULL AFTER customer_id;

UPDATE stg_churn_score SET src_id = customer_id;

UPDATE stg_churn_score s
JOIN bank_customer b           -- ✅ 변경
  ON b.RowNumber = s.src_id
SET s.customer_id = b.CustomerId;
"""

# 조인 샘플 출력 (NULL 뒤로 보내기)
SQL_JOIN_SAMPLE = """
SELECT r.*, s.churn_probability
FROM rfm_result_once r
LEFT JOIN stg_churn_score s ON s.customer_id = r.customer_id
ORDER BY IF(s.churn_probability IS NULL, 1, 0) ASC,
         s.churn_probability DESC,
         r.m_score DESC
LIMIT 20;
"""

# =========================
# Main
# =========================
def ensure_database_exists():
    """DB가 없으면 생성 (utf8mb4/utf8mb4_unicode_ci)"""
    # database 지정없이 접속
    conn = pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS,
        charset="utf8mb4", autocommit=True
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                "DEFAULT CHARACTER SET utf8mb4 "
                "COLLATE utf8mb4_unicode_ci;"
            )
    finally:
        conn.close()
        
def main():
    # resolve csv paths
    bank_csv = resolve_bank_csv()
    print(f"[INFO] Using BANK_CSV: {bank_csv}")
    if SCORE_CSV:
        print(f"[INFO] SCORE_CSV: {SCORE_CSV} ({'exists' if Path(SCORE_CSV).exists() else 'missing'})")

    ensure_database_exists()   # ✅ DB 없으면 생성
    conn = connect()
    try:
        with conn.cursor() as cur:
            # Create tables
            print(">> Create tables...")
            exec_multi(cur, DDL_CUSTOMER)   # ✅ bank_customer 생성
            exec_multi(cur, DDL_RFM)
            exec_multi(cur, DDL_SCORE)

            # Load bank_customer (from CSV)
            print(">> Load bank_customer from CSV via LOCAL INFILE...")
            try:
                load_csv_via_local_infile(
                    cur, "bank_customer", bank_csv,
                    "RowNumber, CustomerId, Surname, CreditScore, Geography, Gender, Age, Tenure, "
                    "Balance, NumOfProducts, HasCrCard, IsActiveMember, EstimatedSalary, Exited"
                )
                print("   - LOCAL INFILE succeeded.")
            except Exception as e:
                print(f"   - LOCAL INFILE failed ({e}); fallback to row-by-row insert.")
                insert_sql = """
                INSERT INTO bank_customer
                (RowNumber, CustomerId, Surname, CreditScore, Geography, Gender, Age, Tenure,
                Balance, NumOfProducts, HasCrCard, IsActiveMember, EstimatedSalary, Exited)
                VALUES
                (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                RowNumber=VALUES(RowNumber),
                Surname=VALUES(Surname),
                CreditScore=VALUES(CreditScore),
                Geography=VALUES(Geography),
                Gender=VALUES(Gender),
                Age=VALUES(Age),
                Tenure=VALUES(Tenure),
                Balance=VALUES(Balance),
                NumOfProducts=VALUES(NumOfProducts),
                HasCrCard=VALUES(HasCrCard),
                IsActiveMember=VALUES(IsActiveMember),
                EstimatedSalary=VALUES(EstimatedSalary),
                Exited=VALUES(Exited),
                _loaded_at=CURRENT_TIMESTAMP
                """
                expected_cols = ["RowNumber","CustomerId","Surname","CreditScore","Geography","Gender",
                                "Age","Tenure","Balance","NumOfProducts","HasCrCard",
                                "IsActiveMember","EstimatedSalary","Exited"]
                load_csv_row_by_row(cur, "bank_customer", bank_csv, insert_sql, expected_cols)


            # Optionally load stg_churn_score
            if SCORE_CSV and Path(SCORE_CSV).exists():
                print(">> Load stg_churn_score from CSV...")
                try:
                    load_csv_via_local_infile(
                        cur, "stg_churn_score", SCORE_CSV,
                        "customer_id, churn_probability"
                    )
                    print("   - stg_churn_score LOCAL INFILE succeeded.")
                except Exception as e:
                    print(f"   - stg_churn_score LOCAL INFILE failed ({e}); fallback to row-by-row.")
                    insert_sql = """
                    INSERT INTO stg_churn_score (customer_id, churn_probability)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE churn_probability=VALUES(churn_probability),
                                            _scored_at=CURRENT_TIMESTAMP
                    """
                    expected_cols = ["customer_id", "churn_probability"]
                    load_csv_row_by_row(cur, "stg_churn_score", SCORE_CSV, insert_sql, expected_cols)

                # 점수 ID 정규화(RowNumber → CustomerId)
                print(">> Normalize stg_churn_score IDs (RowNumber -> CustomerId if applicable)...")
                exec_multi(cur, SQL_FIX_SCORE_IDS)

            # Build RFM
            print(">> Build RFM proxy (tmp_rfm -> tmp_scored -> rfm_result_once)...")
            exec_multi(cur, SQL_TMP_RFM)
            exec_multi(cur, SQL_TMP_SCORED)
            exec_multi(cur, SQL_INSERT_RFM)

            # Sample joined view
            print(">> Sample joined result (top 20):")
            cur.execute(SQL_JOIN_SAMPLE)
            for row in cur.fetchall():
                print(row)

        print("✅ Done. Tables created and data loaded:")
        print(" - stg_bank_churn")
        print(" - rfm_result_once")
        if SCORE_CSV and Path(SCORE_CSV).exists():
            print(" - stg_churn_score (ID normalized if needed)")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
