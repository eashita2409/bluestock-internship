import sqlite3
from pathlib import Path
import pytest

project_root = Path(__file__).resolve().parent.parent
db_path = project_root / "data" / "db" / "mutual_fund_analytics.db"

@pytest.fixture
def db_conn():
    """Fixture to establish connection and close it after test completes."""
    assert db_path.exists(), f"Database file does not exist at {db_path}"
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON;")
    yield conn
    conn.close()

def test_database_connection(db_conn):
    """Test that connection can be established successfully."""
    cursor = db_conn.cursor()
    cursor.execute("SELECT 1;")
    result = cursor.fetchone()
    assert result[0] == 1

def test_tables_exist(db_conn):
    """Test that all 11 dimension and fact tables exist in the database."""
    expected_tables = {
        "dim_fund", "dim_date", "fact_nav", "fact_transactions", 
        "fact_performance", "fact_portfolio", "fact_aum", "fact_sip_industry", 
        "fact_category_inflows", "fact_industry_folios", "fact_benchmark_indices"
    }
    cursor = db_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    existing_tables = {r[0] for r in cursor.fetchall() if not r[0].startswith("sqlite_")}
    
    missing_tables = expected_tables - existing_tables
    assert len(missing_tables) == 0, f"Missing tables in database: {missing_tables}"

def test_foreign_key_violations(db_conn):
    """Test that there are no active foreign key constraint violations."""
    cursor = db_conn.cursor()
    cursor.execute("PRAGMA foreign_key_check;")
    violations = cursor.fetchall()
    assert len(violations) == 0, f"Foreign key violations found: {violations}"

def test_nav_data_integrity(db_conn):
    """Test that NAV history contains no negative or zero values."""
    cursor = db_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM fact_nav WHERE nav <= 0;")
    invalid_count = cursor.fetchone()[0]
    assert invalid_count == 0, f"Found {invalid_count} records in fact_nav with non-positive NAV values."

def test_transaction_data_integrity(db_conn):
    """Test that transaction amounts are all positive."""
    cursor = db_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM fact_transactions WHERE amount_inr <= 0;")
    invalid_count = cursor.fetchone()[0]
    assert invalid_count == 0, f"Found {invalid_count} records in fact_transactions with non-positive amounts."

def test_portfolio_weights(db_conn):
    """Test that portfolio holding weights are valid percentages (>0 and <=100)."""
    cursor = db_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM fact_portfolio WHERE weight_pct <= 0 OR weight_pct > 100;")
    invalid_count = cursor.fetchone()[0]
    assert invalid_count == 0, f"Found {invalid_count} records in fact_portfolio with invalid weights."

def test_dim_fund_unique_pk(db_conn):
    """Test that primary keys in dim_fund are unique."""
    cursor = db_conn.cursor()
    cursor.execute("SELECT COUNT(amfi_code), COUNT(DISTINCT amfi_code) FROM dim_fund;")
    total, unique = cursor.fetchone()
    assert total == unique, f"Duplicate AMFI codes found in dim_fund: total {total}, unique {unique}"

def test_dim_date_format(db_conn):
    """Test that dates in dim_date match YYYY-MM-DD format (10 characters long)."""
    cursor = db_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM dim_date WHERE length(date) != 10 OR date NOT LIKE '____-__-__';")
    invalid_count = cursor.fetchone()[0]
    assert invalid_count == 0, f"Found {invalid_count} records in dim_date with invalid date formatting."
