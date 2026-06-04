import sys
import sqlite3
from pathlib import Path
import pandas as pd

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.utils import get_project_root

def run_database_validation():
    db_path = project_root / "data" / "db" / "mutual_fund_analytics.db"
    docs_dir = project_root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    report_path = docs_dir / "database_validation_report.md"
    
    print(f"Connecting to database at {db_path} for validation...")
    if not db_path.exists():
        print(f"Error: Database file does not exist at {db_path}")
        return False
        
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    
    report_lines = []
    report_lines.append("# Database Validation Report")
    report_lines.append(f"\nReport Generated at: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("\nThis report validates the schema, constraint integrity, and data sanity of the loaded SQLite database.")
    
    # 1. Verify existence of tables
    report_lines.append("\n## 1. Table Existence Check")
    expected_tables = [
        "dim_fund", "dim_date", "fact_nav", "fact_transactions", 
        "fact_performance", "fact_portfolio", "fact_aum", "fact_sip_industry", 
        "fact_category_inflows", "fact_industry_folios", "fact_benchmark_indices"
    ]
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    existing_tables = [r[0] for r in cursor.fetchall() if not r[0].startswith("sqlite_")]
    
    missing_tables = [t for t in expected_tables if t not in existing_tables]
    
    if not missing_tables:
        report_lines.append("\n> [!NOTE]\n> All 11 expected tables exist in the database.")
    else:
        report_lines.append(f"\n> [!CAUTION]\n> Missing tables: {', '.join(missing_tables)}")
        
    # Table counts and row checks
    headers = ["Table Name", "Row Count", "Status"]
    report_lines.append("\n| " + " | ".join(headers) + " |")
    report_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    
    row_counts = {}
    validation_passed = True
    
    for table in expected_tables:
        if table in existing_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            row_counts[table] = count
            status = "PASSED (Non-empty)" if count > 0 else "WARNING (Empty table)"
            if count == 0:
                validation_passed = False
            report_lines.append(f"| `{table}` | {count} | {status} |")
        else:
            row_counts[table] = 0
            report_lines.append(f"| `{table}` | 0 | MISSING |")
            validation_passed = False
            
    # 2. Foreign Key Constraint Checks
    report_lines.append("\n## 2. Foreign Key Constraint Checks")
    cursor.execute("PRAGMA foreign_key_check;")
    fk_violations = cursor.fetchall()
    
    if not fk_violations:
        report_lines.append("\n> [!NOTE]\n> No foreign key violations detected in the database (`PRAGMA foreign_key_check` returned 0 violations).")
    else:
        report_lines.append(f"\n> [!WARNING]\n> Found {len(fk_violations)} Foreign Key violations:")
        fk_headers = ["Table", "RowID", "Referenced Table", "FKey Index"]
        report_lines.append("\n| " + " | ".join(fk_headers) + " |")
        report_lines.append("| " + " | ".join(["---"] * len(fk_headers)) + " |")
        for v in fk_violations:
            report_lines.append(f"| `{v[0]}` | {v[1]} | `{v[2]}` | {v[3]} |")
        validation_passed = False

    # 3. Data Sanity Rules Validation
    report_lines.append("\n## 3. Data Sanity Rules Validation")
    sanity_checks = []
    
    # Check 3.1: NAV Values should be positive
    if "fact_nav" in existing_tables:
        cursor.execute("SELECT COUNT(*) FROM fact_nav WHERE nav <= 0;")
        non_positive_navs = cursor.fetchone()[0]
        status = "PASSED" if non_positive_navs == 0 else f"FAILED ({non_positive_navs} rows <= 0)"
        if non_positive_navs > 0:
            validation_passed = False
        sanity_checks.append(("fact_nav: NAV values must be positive (> 0)", status))

    # Check 3.2: Transaction amounts should be positive
    if "fact_transactions" in existing_tables:
        cursor.execute("SELECT COUNT(*) FROM fact_transactions WHERE amount_inr <= 0;")
        non_positive_tx = cursor.fetchone()[0]
        status = "PASSED" if non_positive_tx == 0 else f"FAILED ({non_positive_tx} rows <= 0)"
        if non_positive_tx > 0:
            validation_passed = False
        sanity_checks.append(("fact_transactions: Transaction amounts must be positive (> 0)", status))

    # Check 3.3: Dates format check in dim_date (should match YYYY-MM-DD)
    if "dim_date" in existing_tables:
        cursor.execute("SELECT COUNT(*) FROM dim_date WHERE length(date) != 10 OR date NOT LIKE '____-__-__';")
        invalid_dates = cursor.fetchone()[0]
        status = "PASSED" if invalid_dates == 0 else f"FAILED ({invalid_dates} invalid date formats)"
        if invalid_dates > 0:
            validation_passed = False
        sanity_checks.append(("dim_date: Date keys must be formatted as YYYY-MM-DD", status))

    # Check 3.4: Monthly dates in fact_sip_industry (should match YYYY-MM)
    if "fact_sip_industry" in existing_tables:
        cursor.execute("SELECT COUNT(*) FROM fact_sip_industry WHERE length(month) != 7 OR month NOT LIKE '____-__';")
        invalid_months = cursor.fetchone()[0]
        status = "PASSED" if invalid_months == 0 else f"FAILED ({invalid_months} invalid month formats)"
        if invalid_months > 0:
            validation_passed = False
        sanity_checks.append(("fact_sip_industry: Month keys must be formatted as YYYY-MM", status))

    # Check 3.5: Portfolio holdings weight sanity (weights should be between 0 and 100)
    if "fact_portfolio" in existing_tables:
        cursor.execute("SELECT COUNT(*) FROM fact_portfolio WHERE weight_pct <= 0 OR weight_pct > 100;")
        invalid_weights = cursor.fetchone()[0]
        status = "PASSED" if invalid_weights == 0 else f"FAILED ({invalid_weights} weights out of bounds 0-100)"
        if invalid_weights > 0:
            validation_passed = False
        sanity_checks.append(("fact_portfolio: Stock weights must be in range (0, 100]", status))

    # Check 3.6: DIM vs FACT fund reference integrity (orphaned funds check)
    if "fact_nav" in existing_tables and "dim_fund" in existing_tables:
        cursor.execute("SELECT COUNT(DISTINCT amfi_code) FROM fact_nav WHERE amfi_code NOT IN (SELECT amfi_code FROM dim_fund);")
        orphaned_nav_codes = cursor.fetchone()[0]
        status = "PASSED" if orphaned_nav_codes == 0 else f"FAILED ({orphaned_nav_codes} orphaned codes)"
        if orphaned_nav_codes > 0:
            validation_passed = False
        sanity_checks.append(("fact_nav: All codes must exist in dim_fund", status))

    # Check 3.7: DIM vs FACT transaction reference integrity
    if "fact_transactions" in existing_tables and "dim_fund" in existing_tables:
        cursor.execute("SELECT COUNT(DISTINCT amfi_code) FROM fact_transactions WHERE amfi_code NOT IN (SELECT amfi_code FROM dim_fund);")
        orphaned_tx_codes = cursor.fetchone()[0]
        status = "PASSED" if orphaned_tx_codes == 0 else f"FAILED ({orphaned_tx_codes} orphaned codes)"
        if orphaned_tx_codes > 0:
            validation_passed = False
        sanity_checks.append(("fact_transactions: All codes must exist in dim_fund", status))

    # Render Sanity Checks Table
    sanity_headers = ["Rule Description", "Status"]
    report_lines.append("\n| " + " | ".join(sanity_headers) + " |")
    report_lines.append("| " + " | ".join(["---"] * len(sanity_headers)) + " |")
    for desc, stat in sanity_checks:
        report_lines.append(f"| {desc} | {stat} |")

    # 4. Overall Status
    report_lines.append("\n## 4. Overall Validation Summary")
    if validation_passed:
        report_lines.append("\n> [!TIP]\n> **SUCCESS**: Database validation passed successfully! All integrity constraints and data validation checks hold.")
    else:
        report_lines.append("\n> [!CAUTION]\n> **FAILED**: Database validation failed. Please check the warnings/failed sections above.")

    # Write report
    with open(report_path, "w", encoding="utf-8") as rf:
        rf.write("\n".join(report_lines))
        
    print(f"Validation completed. Report written to {report_path}")
    conn.close()
    return validation_passed

if __name__ == "__main__":
    success = run_database_validation()
    sys.exit(0 if success else 1)
