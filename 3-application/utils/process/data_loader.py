# service/utils/process/data_loader.py
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def get_mysql_engine():
    """
    .env 파일의 환경변수를 읽어 MySQL SQLAlchemy 엔진 생성
    """
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT", "3306")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASS")
    database = os.getenv("DB_NAME")
    charset = os.getenv("DB_CHARSET", "utf8mb4")

    if not all([host, port, user, password, database]):
        raise ValueError("환경 변수(DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME)를 확인하세요.")

    password_enc = quote_plus(password)
    url = f"mysql+pymysql://{user}:{password_enc}@{host}:{port}/{database}?charset={charset}"
    return create_engine(url, pool_pre_ping=True)

def load_table(
    table_name: str,
    columns: list[str] = None,
    where: str = None,
    limit: int = None
) -> pd.DataFrame:
    """
    MySQL 테이블을 DataFrame으로 로드
    """
    engine = get_mysql_engine()
    cols = ", ".join(columns) if columns else "*"
    query = f"SELECT {cols} FROM {table_name}"
    if where:
        query += f" WHERE {where}"
    if limit:
        query += f" LIMIT {limit}"

    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

    print(f"[OK] Loaded {len(df)} rows from '{table_name}'")
    return df
