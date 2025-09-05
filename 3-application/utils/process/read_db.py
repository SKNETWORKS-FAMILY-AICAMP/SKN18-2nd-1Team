# 3-application/utils/read_db.py
from __future__ import annotations
import os
import pandas as pd
import pymysql
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # .env 로드

def get_conn():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASS", ""),
        database=os.getenv("DB_NAME", ""),
        charset="utf8mb4",
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
        client_flag=pymysql.constants.CLIENT.LOCAL_FILES,
    )

def read_df(sql: str, params: tuple | None = None) -> pd.DataFrame:
    conn = get_conn()
    try:
        return pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()
