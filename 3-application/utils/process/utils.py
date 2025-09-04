# utils/process/utils.py
import os
import pandas as pd
from sqlalchemy import create_engine

def get_engine() -> "Engine":
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASS = os.getenv("DB_PASS", "root1234")
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "sknproject2")
    url = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url, pool_pre_ping=True)

def write_churn_scores(engine, df_scores: pd.DataFrame, table: str = "stg_churn_score"):
    """
    df_scores: columns = ['customer_id','churn_probability']
    """
    # 컬럼 표준화
    out = df_scores.rename(columns={
        "CustomerId":"customer_id",
        "churn_probability":"churn_probability"
    })[["customer_id","churn_probability"]].copy()

    # DB 적재(교체)
    out.to_sql(table, con=engine, if_exists="replace", index=False)

def create_view_join(engine):
    """
    rfm_result_once(이미 존재) + stg_churn_score 조인 뷰를 생성.
    """
    sql = """
    CREATE OR REPLACE VIEW vw_rfm_for_app AS
    SELECT r.*,
           s.churn_probability
    FROM rfm_result_once r
    LEFT JOIN stg_churn_score s
      ON s.customer_id = r.customer_id;
    """
    with engine.begin() as conn:
        conn.exec_driver_sql(sql)
