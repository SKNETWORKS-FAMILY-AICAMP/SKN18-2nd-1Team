from __future__ import annotations
from pathlib import Path
import pandas as pd

# 학습 파이프라인에서 자주 쓰는 기본 파일명
_DEFAULT_NAME = "Customer-Churn-Records.csv"

# 현재 파일 기준 프로젝트 루트 경로 추정
# dataloader.py → process → utils → 3-application → project-root
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_DATA_DIR = _PROJECT_ROOT / "3-application" / "assets" / "data"

def _safe_read_csv(path: Path) -> pd.DataFrame:
    """CSV 인코딩/구분자 이슈에 대비한 안전 로더."""
    try:
        return pd.read_csv(path)
    except UnicodeDecodeError:
        # BOM 포함 등
        return pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        # 세미콜론 구분 CSV 대비
        return pd.read_csv(path, sep=";")

def find_csv_in_data(data_dir: Path | None = None) -> Path:
    """
    3-application/assets/data 폴더에서 학습용 CSV 한 개를 찾습니다.
    - 우선순위: 기본 파일명(_DEFAULT_NAME) → 사전순 첫 번째 .csv
    """
    d = Path(data_dir) if data_dir else _DEFAULT_DATA_DIR
    if not d.exists():
        raise FileNotFoundError(f"[ERROR] 데이터 폴더가 없습니다: {d}")

    # 1) 기본 파일명 우선
    p = d / _DEFAULT_NAME
    if p.exists():
        return p.resolve()

    # 2) 사전순 첫 번째 CSV
    csvs = sorted(d.glob("*.csv"))
    if not csvs:
        raise FileNotFoundError(f"[ERROR] {d} 폴더에 .csv 파일이 없습니다.")
    return csvs[0].resolve()

def load_csv_from_data(
    filename: str | None = None,
    data_dir: str | Path | None = None,
    require_columns: list[str] | None = None,
) -> pd.DataFrame:
    """
    CSV 로드 (기본: 프로젝트 루트/3-application/assets/data).
    - filename이 None이면 find_csv_in_data()로 자동 탐색
    - require_columns가 주어지면 필수 컬럼 존재 여부를 검증
    """
    d = Path(data_dir) if data_dir else _DEFAULT_DATA_DIR
    path = (d / filename).resolve() if filename else find_csv_in_data(d)

    if not path.exists():
        raise FileNotFoundError(f"[ERROR] CSV 파일을 찾을 수 없습니다: {path}")

    df = _safe_read_csv(path)

    if require_columns:
        missing = [c for c in require_columns if c not in df.columns]
        if missing:
            raise KeyError(f"[ERROR] CSV에 누락된 컬럼: {missing}\n- 파일: {path}\n- 보유 컬럼: {list(df.columns)}")

    print(f"[OK] CSV Loaded: {path}  shape={df.shape}")
    return df

# 편의 함수들 --------------------------------------------------------------

def list_csvs(data_dir: str | Path | None = None) -> list[Path]:
    """data_dir (기본: 3-application/assets/data) 안의 CSV 파일 리스트를 반환."""
    d = Path(data_dir) if data_dir else _DEFAULT_DATA_DIR
    return sorted(p.resolve() for p in d.glob("*.csv")) if d.exists() else []

def load_default_for_notebook() -> pd.DataFrame:
    """노트북에서 빠르게 불러오기: 기본 파일명/탐색 규칙 사용."""
    return load_csv_from_data()

# (직접 실행 테스트)
if __name__ == "__main__":
    df = load_default_for_notebook()
    print(df.head())
