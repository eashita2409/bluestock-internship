import sys
import sqlite3
from pathlib import Path
import pandas as pd

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.utils import get_data_dir

def load_date_dimension(conn, processed_dir):
    print("Generating Date Dimension (dim_date)...")
    date_files_and_cols = [
        ("02_nav_history.csv", "date"),
        ("08_investor_transactions.csv", "transaction_date"),
        ("09_portfolio_holdings.csv", "portfolio_date"),
        ("03_aum_by_fund_house.csv", "date"),
        ("10_benchmark_indices.csv", "date")
    ]
    
    all_dates = set()
    for filename, colname in date_files_and_cols:
        file_path = processed_dir / filename
        if file_path.exists():
            df = pd.read_csv(file_path)
            if colname in df.columns:
                dates = df[colname].dropna().unique()
                all_dates.update(dates)
                
    date_list = sorted(list(all_dates))
    date_df = pd.DataFrame({'date': date_list})
    dt_series = pd.to_datetime(date_df['date'])
    
    date_df['year'] = dt_series.dt.year
    date_df['month'] = dt_series.dt.month
    date_df['day'] = dt_series.dt.day
    date_df['quarter'] = dt_series.dt.quarter
    date_df['day_of_week'] = dt_series.dt.dayofweek
    date_df['is_weekend'] = dt_series.dt.dayofweek.isin([5, 6]).astype(int)
    
    # Save to SQL table
    date_df.to_sql('dim_date', conn, if_exists='append', index=False)
    print(f"Loaded {len(date_df)} unique dates into dim_date.")

def run_database_loading():
    processed_dir = get_data_dir("processed")
    db_dir = project_root / "data" / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / "mutual_fund_analytics.db"
    
    print(f"Initializing SQLite database at: {db_path}")
    
    # If DB exists, delete it to ensure a clean rebuild and avoid duplicates
    if db_path.exists():
        db_path.unlink()
        
    conn = sqlite3.connect(str(db_path))
    
    # Execute schema.sql DDL
    schema_path = project_root / "sql" / "schema.sql"
    if not schema_path.exists():
        print(f"Error: Schema script not found at {schema_path}")
        return
        
    print("Executing database schema DDL...")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    
    # 1. Load dim_fund (no dependencies)
    print("Loading dim_fund...")
    df_fund = pd.read_csv(processed_dir / "01_fund_master.csv")
    df_fund.to_sql('dim_fund', conn, if_exists='append', index=False)
    
    # 2. Load dim_date (no dependencies, pre-populated)
    load_date_dimension(conn, processed_dir)
    
    # 3. Load other tables (order respects FK constraints)
    tables_to_load = [
        ("02_nav_history.csv", "fact_nav"),
        ("08_investor_transactions.csv", "fact_transactions"),
        ("07_scheme_performance.csv", "fact_performance"),
        ("09_portfolio_holdings.csv", "fact_portfolio"),
        ("03_aum_by_fund_house.csv", "fact_aum"),
        ("04_monthly_sip_inflows.csv", "fact_sip_industry"),
        ("05_category_inflows.csv", "fact_category_inflows"),
        ("06_industry_folio_count.csv", "fact_industry_folios"),
        ("10_benchmark_indices.csv", "fact_benchmark_indices")
    ]
    
    for csv_file, table_name in tables_to_load:
        csv_path = processed_dir / csv_file
        if not csv_path.exists():
            print(f"Warning: processed file {csv_file} not found. Skipping table {table_name}.")
            continue
            
        print(f"Loading {table_name} from {csv_file}...")
        df = pd.read_csv(csv_path)
        df.to_sql(table_name, conn, if_exists='append', index=False)
        
    # Verify loaded records count
    print("\n" + "="*50)
    print("DATABASE LOADING COMPLETE. ROW COUNTS:")
    print("="*50)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cursor.fetchall() if not r[0].startswith("sqlite_")]
    
    for table in sorted(tables):
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        count = cursor.fetchone()[0]
        print(f"Table '{table}': {count} rows")
    print("="*50 + "\n")
    
    conn.close()

if __name__ == "__main__":
    run_database_loading()
