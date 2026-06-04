import sys
import shutil
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to sys.path so we can import src
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.utils import get_data_dir

def clean_nav_history():
    raw_dir = get_data_dir("raw")
    processed_dir = get_data_dir("processed")
    
    file_path = raw_dir / "02_nav_history.csv"
    if not file_path.exists():
        print(f"Error: {file_path} does not exist.")
        return
    
    print("Cleaning 02_nav_history.csv...")
    df = pd.read_csv(file_path)
    initial_shape = df.shape
    
    # Parse dates
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    # Drop rows with invalid dates
    invalid_dates = df['date'].isnull().sum()
    df = df.dropna(subset=['date'])
    
    # Sort by amfi_code and date
    df = df.sort_values(by=['amfi_code', 'date'])
    
    # Forward fill missing NAV values grouped by amfi_code
    df['nav'] = df.groupby('amfi_code')['nav'].ffill()
    
    # Remove duplicate rows
    duplicates_removed = df.duplicated(subset=['amfi_code', 'date']).sum()
    df = df.drop_duplicates(subset=['amfi_code', 'date'])
    
    # Validate NAV > 0
    invalid_navs = (df['nav'] <= 0).sum()
    df = df[df['nav'] > 0]
    
    # Format date back to string
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
    
    # Save cleaned
    output_path = processed_dir / "02_nav_history.csv"
    df.to_csv(output_path, index=False)
    
    print(f"NAV History cleaned: {initial_shape} -> {df.shape}")
    print(f" - Invalid dates dropped: {invalid_dates}")
    print(f" - Duplicate rows removed: {duplicates_removed}")
    print(f" - Non-positive NAVs removed: {invalid_navs}")

def clean_investor_transactions():
    raw_dir = get_data_dir("raw")
    processed_dir = get_data_dir("processed")
    
    file_path = raw_dir / "08_investor_transactions.csv"
    if not file_path.exists():
        print(f"Error: {file_path} does not exist.")
        return
        
    print("Cleaning 08_investor_transactions.csv...")
    df = pd.read_csv(file_path)
    initial_shape = df.shape
    
    # Standardize transaction_type
    tx_type_map = {
        'sip': 'SIP',
        'redemption': 'Redemption',
        'lumpsum': 'Lumpsum'
    }
    df['transaction_type'] = df['transaction_type'].apply(
        lambda x: tx_type_map.get(str(x).lower().strip(), str(x).strip().capitalize())
    )
    
    # Validate amount > 0
    invalid_amounts = (df['amount_inr'] <= 0).sum()
    df = df[df['amount_inr'] > 0]
    
    # Validate KYC status
    kyc_map = {
        'verified': 'Verified',
        'pending': 'Pending'
    }
    df['kyc_status'] = df['kyc_status'].apply(
        lambda x: kyc_map.get(str(x).lower().strip(), str(x).strip().capitalize())
    )
    
    # Fix date formats
    df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
    invalid_dates = df['transaction_date'].isnull().sum()
    df = df.dropna(subset=['transaction_date'])
    df['transaction_date'] = df['transaction_date'].dt.strftime('%Y-%m-%d')
    
    # Save cleaned
    output_path = processed_dir / "08_investor_transactions.csv"
    df.to_csv(output_path, index=False)
    
    print(f"Investor Transactions cleaned: {initial_shape} -> {df.shape}")
    print(f" - Non-positive amounts removed: {invalid_amounts}")
    print(f" - Invalid dates dropped: {invalid_dates}")

def clean_scheme_performance():
    raw_dir = get_data_dir("raw")
    processed_dir = get_data_dir("processed")
    
    file_path = raw_dir / "07_scheme_performance.csv"
    if not file_path.exists():
        print(f"Error: {file_path} does not exist.")
        return
        
    print("Cleaning 07_scheme_performance.csv...")
    df = pd.read_csv(file_path)
    initial_shape = df.shape
    
    # Validate return columns are numeric
    return_cols = ['return_1yr_pct', 'return_3yr_pct', 'return_5yr_pct', 'benchmark_3yr_pct']
    for col in return_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        
    # Sharpe ratio numeric
    df['sharpe_ratio'] = pd.to_numeric(df['sharpe_ratio'], errors='coerce').fillna(0.0)
    
    # Flag negative Sharpe ratios
    df['has_negative_sharpe'] = (df['sharpe_ratio'] < 0).astype(int)
    
    # Validate expense ratio range
    df['expense_ratio_pct'] = pd.to_numeric(df['expense_ratio_pct'], errors='coerce').fillna(0.0)
    # Print warning if any are out of typical range 0-5%
    out_of_range_expense = df[(df['expense_ratio_pct'] < 0) | (df['expense_ratio_pct'] > 5.0)]
    if not out_of_range_expense.empty:
        print(f"Warning: {len(out_of_range_expense)} schemes have expense ratios outside the 0-5% range.")
        
    # Save cleaned
    output_path = processed_dir / "07_scheme_performance.csv"
    df.to_csv(output_path, index=False)
    
    print(f"Scheme Performance cleaned: {initial_shape} -> {df.shape}")

def process_other_datasets():
    raw_dir = get_data_dir("raw")
    processed_dir = get_data_dir("processed")
    
    other_files = [
        "01_fund_master.csv",
        "03_aum_by_fund_house.csv",
        "04_monthly_sip_inflows.csv",
        "05_category_inflows.csv",
        "06_industry_folio_count.csv",
        "09_portfolio_holdings.csv",
        "10_benchmark_indices.csv"
    ]
    
    for filename in other_files:
        src_path = raw_dir / filename
        dest_path = processed_dir / filename
        if not src_path.exists():
            print(f"Warning: Raw file {filename} not found.")
            continue
            
        print(f"Processing and copying {filename}...")
        df = pd.read_csv(src_path)
        
        # Standardize dates to YYYY-MM-DD if date columns exist
        for col in df.columns:
            if 'date' in col:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
                
        df.to_csv(dest_path, index=False)

def run_all_cleaning():
    print("Starting Day 2 Data Cleaning Process...")
    clean_nav_history()
    clean_investor_transactions()
    clean_scheme_performance()
    process_other_datasets()
    print("Data cleaning completed successfully.")

if __name__ == "__main__":
    run_all_cleaning()
