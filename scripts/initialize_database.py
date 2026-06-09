"""
initialize_database.py
======================
Automatically builds the SQLite database from tracked CSV files and the
schema DDL whenever the .db file is absent (e.g. on a fresh Streamlit Cloud
deployment).

Called by dashboard/app.py before any DB connection is attempted.
Safe to call multiple times — it is a no-op when the database already exists.

Usage (standalone):
    python scripts/initialize_database.py
"""

import sys
import sqlite3
import logging
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Path resolution — works on Windows (local) and Linux (Streamlit Cloud)
# ---------------------------------------------------------------------------
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

SCHEMA_PATH: Path = PROJECT_ROOT / "sql" / "schema.sql"
PROCESSED_DIR: Path = PROJECT_ROOT / "data" / "processed"
DB_DIR: Path = PROJECT_ROOT / "data" / "db"
DB_PATH: Path = DB_DIR / "mutual_fund_analytics.db"

# Tables to load in FK-safe order: (csv_filename, sqlite_table_name)
TABLE_LOAD_ORDER = [
    ("01_fund_master.csv",          "dim_fund"),
    ("02_nav_history.csv",          "fact_nav"),
    ("08_investor_transactions.csv","fact_transactions"),
    ("07_scheme_performance.csv",   "fact_performance"),
    ("09_portfolio_holdings.csv",   "fact_portfolio"),
    ("03_aum_by_fund_house.csv",    "fact_aum"),
    ("04_monthly_sip_inflows.csv",  "fact_sip_industry"),
    ("05_category_inflows.csv",     "fact_category_inflows"),
    ("06_industry_folio_count.csv", "fact_industry_folios"),
    ("10_benchmark_indices.csv",    "fact_benchmark_indices"),
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_date_dimension(conn: sqlite3.Connection) -> None:
    """Aggregate all dates from date-bearing fact CSVs into dim_date."""
    date_sources = [
        ("02_nav_history.csv",          "date"),
        ("08_investor_transactions.csv","transaction_date"),
        ("09_portfolio_holdings.csv",   "portfolio_date"),
        ("03_aum_by_fund_house.csv",    "date"),
        ("10_benchmark_indices.csv",    "date"),
    ]

    all_dates: set = set()
    for csv_file, col in date_sources:
        path = PROCESSED_DIR / csv_file
        if path.exists():
            df = pd.read_csv(path, usecols=[col])
            all_dates.update(df[col].dropna().unique())

    if not all_dates:
        log.warning("No dates found — dim_date will be empty.")
        return

    date_series = pd.to_datetime(sorted(all_dates))
    dim_date = pd.DataFrame({
        "date":        date_series.strftime("%Y-%m-%d"),
        "year":        date_series.year,
        "month":       date_series.month,
        "day":         date_series.day,
        "quarter":     date_series.quarter,
        "day_of_week": date_series.dayofweek,
        "is_weekend":  date_series.dayofweek.isin([5, 6]).astype(int),
    })
    dim_date.to_sql("dim_date", conn, if_exists="append", index=False)
    log.info("dim_date  — loaded %d unique dates.", len(dim_date))


def _apply_schema(conn: sqlite3.Connection) -> None:
    """Execute schema.sql DDL against the given connection."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"schema.sql not found at {SCHEMA_PATH}. "
            "Cannot initialise database."
        )
    with open(SCHEMA_PATH, "r", encoding="utf-8") as fh:
        schema_sql = fh.read()
    conn.executescript(schema_sql)
    log.info("Schema DDL applied successfully.")


def _load_tables(conn: sqlite3.Connection) -> None:
    """Load every fact/dim CSV into its corresponding SQLite table."""
    for csv_file, table_name in TABLE_LOAD_ORDER:
        csv_path = PROCESSED_DIR / csv_file
        if not csv_path.exists():
            log.warning("%-40s not found — skipping table %s.", csv_file, table_name)
            continue
        df = pd.read_csv(csv_path)
        df.to_sql(table_name, conn, if_exists="append", index=False)
        log.info("%-30s → %-30s  (%d rows)", csv_file, table_name, len(df))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def initialize_database(force_rebuild: bool = False) -> Path:
    """
    Ensure the SQLite database exists and is populated.

    Parameters
    ----------
    force_rebuild : bool
        If True, deletes any existing .db file and rebuilds from scratch.
        Default is False (no-op when the file already exists).

    Returns
    -------
    Path
        Absolute path to the (now-existing) database file.

    Raises
    ------
    FileNotFoundError
        If schema.sql or the processed CSV directory is missing.
    RuntimeError
        If the database is built but core tables are still empty after loading.
    """
    # --- 1. Short-circuit if DB already exists and rebuild not requested ------
    if DB_PATH.exists() and not force_rebuild:
        log.info("Database already exists at %s — skipping init.", DB_PATH)
        return DB_PATH

    log.info("=" * 60)
    if force_rebuild and DB_PATH.exists():
        DB_PATH.unlink()
        log.info("Existing database removed for forced rebuild.")
    else:
        log.info("Database not found — auto-initialising from CSV sources.")
    log.info("Target path : %s", DB_PATH)
    log.info("=" * 60)

    # --- 2. Validate prerequisites -------------------------------------------
    if not PROCESSED_DIR.exists():
        raise FileNotFoundError(
            f"Processed data directory not found at {PROCESSED_DIR}. "
            "Run scripts/data_cleaning.py first."
        )
    fund_master = PROCESSED_DIR / "01_fund_master.csv"
    if not fund_master.exists():
        raise FileNotFoundError(
            f"01_fund_master.csv not found in {PROCESSED_DIR}. "
            "Cannot populate dim_fund (required by all FK constraints)."
        )

    # --- 3. Create DB directory & connection ---------------------------------
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = OFF;")   # OFF during bulk load

    try:
        # --- 4. Apply schema -------------------------------------------------
        _apply_schema(conn)

        # --- 5. Build date dimension first (no FK deps) ----------------------
        log.info("Building dim_date ...")
        _build_date_dimension(conn)

        # --- 6. Load all other tables ----------------------------------------
        log.info("Loading fact/dim tables ...")
        _load_tables(conn)

        # --- 7. Re-enable foreign keys & commit ------------------------------
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.commit()

        # --- 8. Quick integrity check ----------------------------------------
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM dim_fund;"
        )
        fund_count = cursor.fetchone()[0]
        if fund_count == 0:
            raise RuntimeError(
                "dim_fund is empty after loading — initialization failed."
            )

        log.info("=" * 60)
        log.info("DATABASE INITIALISATION COMPLETE")
        log.info("dim_fund rows : %d", fund_count)
        log.info("Database path : %s", DB_PATH)
        log.info("=" * 60)

    except Exception:
        conn.close()
        # Remove partially-built DB so the next startup retries cleanly
        if DB_PATH.exists():
            DB_PATH.unlink()
        raise
    finally:
        conn.close()

    return DB_PATH


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Initialize the Bluestock Mutual Fund Analytics SQLite database."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force a complete rebuild even if the .db already exists.",
    )
    args = parser.parse_args()

    try:
        db = initialize_database(force_rebuild=args.force)
        print(f"\n[OK] Database ready at: {db}\n")
        sys.exit(0)
    except Exception as exc:
        print(f"\n[ERROR] Initialization failed: {exc}\n")
        sys.exit(1)
