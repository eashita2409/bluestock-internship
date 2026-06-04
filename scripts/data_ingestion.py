import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to sys.path so we can import src
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.utils import get_data_dir

def run_data_ingestion():
    raw_dir = get_data_dir("raw")
    csv_files = sorted(raw_dir.glob("*.csv"))
    
    # We will exclude mock_returns.csv if we want to focus on the 10 official files,
    # but the prompt says 'all CSV datasets automatically', so we'll process all of them
    # while highlighting the official ones.
    
    print(f"Detected {len(csv_files)} CSV files in data/raw:")
    for f in csv_files:
        print(f" - {f.name} ({f.stat().st_size / 1024:.2f} KB)")
    print("\n" + "="*80 + "\n")
    
    loaded_datasets = {}
    
    # 1 & 2. Load all datasets
    for f in csv_files:
        print(f"Loading {f.name}...")
        try:
            df = pd.read_csv(f)
            loaded_datasets[f.name] = df
        except Exception as e:
            print(f"Error loading {f.name}: {e}")
            
    print("\n" + "="*80 + "\n")
    
    # 3. Print shape, dtypes, head, and summary for each dataset
    for name, df in loaded_datasets.items():
        print(f"DATASET: {name}")
        print(f"Shape (Rows, Columns): {df.shape}")
        print("-" * 40)
        print("Data Types:")
        print(df.dtypes)
        print("-" * 40)
        print("First 5 Rows:")
        print(df.head())
        print("-" * 40)
        print("Statistical Summary:")
        print(df.describe(include='all'))
        print("\n" + "="*80 + "\n")
        
    # 4. Validate AMFI codes
    print("VALIDATING AMFI CODES...")
    amfi_validation_results = {}
    
    # Check if fund master is loaded
    fund_master_file = "01_fund_master.csv"
    if fund_master_file in loaded_datasets:
        master_df = loaded_datasets[fund_master_file]
        if "amfi_code" in master_df.columns:
            master_codes = master_df["amfi_code"].dropna()
            
            # Master validations
            total_master_codes = len(master_df)
            unique_master_codes = master_df["amfi_code"].nunique()
            null_master_codes = master_df["amfi_code"].isnull().sum()
            numeric_check = pd.to_numeric(master_df["amfi_code"], errors='coerce')
            non_numeric_count = numeric_check.isnull().sum() - null_master_codes
            positive_check = (numeric_check > 0).sum()
            
            amfi_validation_results[fund_master_file] = {
                "total_rows": total_master_codes,
                "unique_codes": unique_master_codes,
                "null_codes": null_master_codes,
                "non_numeric": non_numeric_count,
                "positive_codes": positive_check,
                "has_duplicates": unique_master_codes != (total_master_codes - null_master_codes)
            }
            
            # Cross-validate other datasets that contain an "amfi_code" column
            master_set = set(master_codes.astype(int))
            
            for name, df in loaded_datasets.items():
                if name == fund_master_file:
                    continue
                if "amfi_code" in df.columns:
                    codes = df["amfi_code"].dropna()
                    try:
                        codes_int = codes.astype(int)
                        missing_in_master = [c for c in codes_int if c not in master_set]
                        missing_in_master_unique = sorted(list(set(missing_in_master)))
                    except Exception:
                        missing_in_master_unique = ["Error: Non-integer AMFI codes found in dataset"]
                        
                    amfi_validation_results[name] = {
                        "total_rows": len(df),
                        "has_amfi_column": True,
                        "unique_codes": df["amfi_code"].nunique(),
                        "null_codes": df["amfi_code"].isnull().sum(),
                        "missing_in_master_count": len(missing_in_master_unique) if isinstance(missing_in_master_unique, list) else 1,
                        "missing_codes": missing_in_master_unique
                    }
        else:
            print("Error: 'amfi_code' column missing in 01_fund_master.csv")
    else:
        print("Error: 01_fund_master.csv not found in loaded datasets.")
        
    print("\n" + "="*80 + "\n")
    
    # 5. Create Data Quality Report
    print("GENERATING DATA QUALITY REPORT...")
    report_lines = []
    report_lines.append("# Data Quality Report - Mutual Fund Analytics Platform")
    report_lines.append("\nThis report summarizes the data health, missing values, duplicates, and code validation across all datasets.")
    report_lines.append(f"\nReport Generated automatically at: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # AMFI Validation Section
    report_lines.append("## 1. AMFI Code Validation Analysis")
    report_lines.append("\nAMFI (Association of Mutual Funds in India) codes serve as the primary key linking our mutual fund datasets. Here is the checkup:\n")
    
    if fund_master_file in amfi_validation_results:
        master_results = amfi_validation_results[fund_master_file]
        report_lines.append("### Master Scheme Database (`01_fund_master.csv`)")
        report_lines.append(f"- **Total Rows**: {master_results['total_rows']}")
        report_lines.append(f"- **Unique AMFI Codes**: {master_results['unique_codes']}")
        report_lines.append(f"- **Missing/Null Codes**: {master_results['null_codes']}")
        report_lines.append(f"- **Non-Numeric Codes**: {master_results['non_numeric']}")
        report_lines.append(f"- **Positive Integer Codes (>0)**: {master_results['positive_codes']}")
        report_lines.append(f"- **Has Duplicates?**: {'Yes (Warning: Master keys must be unique!)' if master_results['has_duplicates'] else 'No (Success: Keys are unique)'}")
        report_lines.append("\n### Cross-Dataset Reference Integrity")
        report_lines.append("Checking if AMFI codes in other datasets exist in our master list:\n")
        
        headers = ["Dataset", "Total Rows", "Unique Codes", "Null Codes", "Orphaned Codes (Not in Master)"]
        report_lines.append("| " + " | ".join(headers) + " |")
        report_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        
        for name, res in amfi_validation_results.items():
            if name == fund_master_file:
                continue
            row = [
                name,
                str(res["total_rows"]),
                str(res["unique_codes"]),
                str(res["null_codes"]),
                str(res["missing_in_master_count"])
            ]
            report_lines.append("| " + " | ".join(row) + " |")
            
        report_lines.append("\n> **Note**: Orphaned codes represent transaction or historic records referencing scheme codes that do not exist in our main master catalog.")
    else:
        report_lines.append("\n**Error**: Could not perform AMFI validation because `01_fund_master.csv` was missing or invalid.")
        
    report_lines.append("\n" + "-"*40 + "\n")
    
    # Dataset Ingestion Summaries
    report_lines.append("## 2. Dataset Health Summaries")
    
    for name, df in loaded_datasets.items():
        report_lines.append(f"\n### {name}")
        report_lines.append(f"- **File Dimensions**: {df.shape[0]} rows, {df.shape[1]} columns")
        
        # Duplicate Rows check
        dups = df.duplicated().sum()
        dup_pct = (dups / len(df)) * 100 if len(df) > 0 else 0
        report_lines.append(f"- **Duplicate Rows**: {dups} ({dup_pct:.2f}%)")
        
        # Missing values analysis
        missing_count = df.isnull().sum()
        cols_with_missing = missing_count[missing_count > 0]
        
        if len(cols_with_missing) > 0:
            report_lines.append("- **Missing Values per Column**:")
            for col, count in cols_with_missing.items():
                pct = (count / len(df)) * 100
                report_lines.append(f"  - `{col}`: {count} nulls ({pct:.2f}%)")
        else:
            report_lines.append("- **Missing Values**: None (100% complete)")
            
        # Data columns type table
        report_lines.append("\nColumn Details:\n")
        col_headers = ["Column Name", "Data Type", "Non-Null Count", "Example Value"]
        report_lines.append("| " + " | ".join(col_headers) + " |")
        report_lines.append("| " + " | ".join(["---"] * len(col_headers)) + " |")
        
        for col in df.columns:
            non_null = df[col].notnull().sum()
            dtype = str(df[col].dtype)
            example = str(df[col].iloc[0]) if len(df) > 0 else "N/A"
            # Truncate long example strings
            if len(example) > 50:
                example = example[:47] + "..."
            # Clean string for Markdown table safety
            example = example.replace("\n", " ").replace("|", "\\|")
            
            col_row = [col, dtype, str(non_null), f"`{example}`"]
            report_lines.append("| " + " | ".join(col_row) + " |")
            
    # Write report to docs folder
    docs_dir = project_root / "docs"
    docs_dir.mkdir(exist_ok=True)
    report_file = docs_dir / "data_quality_report.md"
    
    with open(report_file, "w", encoding="utf-8") as rf:
        rf.write("\n".join(report_lines))
        
    print(f"Data Quality Report successfully written to: {report_file}")

if __name__ == "__main__":
    run_data_ingestion()
