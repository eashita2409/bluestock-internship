# Data Quality Report - Mutual Fund Analytics Platform

This report summarizes the data health, missing values, duplicates, and code validation across all datasets.

Report Generated automatically at: 2026-06-04 10:27:08

## 1. AMFI Code Validation Analysis

AMFI (Association of Mutual Funds in India) codes serve as the primary key linking our mutual fund datasets. Here is the checkup:

### Master Scheme Database (`01_fund_master.csv`)
- **Total Rows**: 40
- **Unique AMFI Codes**: 40
- **Missing/Null Codes**: 0
- **Non-Numeric Codes**: 0
- **Positive Integer Codes (>0)**: 40
- **Has Duplicates?**: No (Success: Keys are unique)

### Cross-Dataset Reference Integrity
Checking if AMFI codes in other datasets exist in our master list:

| Dataset | Total Rows | Unique Codes | Null Codes | Orphaned Codes (Not in Master) |
| --- | --- | --- | --- | --- |
| 02_nav_history.csv | 46000 | 40 | 0 | 0 |
| 07_scheme_performance.csv | 40 | 40 | 0 | 0 |
| 08_investor_transactions.csv | 32778 | 40 | 0 | 0 |
| 09_portfolio_holdings.csv | 322 | 34 | 0 | 0 |

> **Note**: Orphaned codes represent transaction or historic records referencing scheme codes that do not exist in our main master catalog.

----------------------------------------

## 2. Dataset Health Summaries

### 01_fund_master.csv
- **File Dimensions**: 40 rows, 15 columns
- **Duplicate Rows**: 0 (0.00%)
- **Missing Values**: None (100% complete)

Column Details:

| Column Name | Data Type | Non-Null Count | Example Value |
| --- | --- | --- | --- |
| amfi_code | int64 | 40 | `119551` |
| fund_house | str | 40 | `SBI Mutual Fund` |
| scheme_name | str | 40 | `SBI Bluechip Fund - Regular Plan - Growth` |
| category | str | 40 | `Equity` |
| sub_category | str | 40 | `Large Cap` |
| plan | str | 40 | `Regular` |
| launch_date | str | 40 | `2006-02-14` |
| benchmark | str | 40 | `NIFTY 100 TRI` |
| expense_ratio_pct | float64 | 40 | `1.54` |
| exit_load_pct | float64 | 40 | `1.0` |
| min_sip_amount | int64 | 40 | `500` |
| min_lumpsum_amount | int64 | 40 | `1000` |
| fund_manager | str | 40 | `Sohini Andani` |
| risk_category | str | 40 | `Moderate` |
| sebi_category_code | str | 40 | `EC01` |

### 02_nav_history.csv
- **File Dimensions**: 46000 rows, 3 columns
- **Duplicate Rows**: 0 (0.00%)
- **Missing Values**: None (100% complete)

Column Details:

| Column Name | Data Type | Non-Null Count | Example Value |
| --- | --- | --- | --- |
| amfi_code | int64 | 46000 | `119551` |
| date | str | 46000 | `2022-01-03` |
| nav | float64 | 46000 | `54.3856` |

### 03_aum_by_fund_house.csv
- **File Dimensions**: 90 rows, 5 columns
- **Duplicate Rows**: 0 (0.00%)
- **Missing Values**: None (100% complete)

Column Details:

| Column Name | Data Type | Non-Null Count | Example Value |
| --- | --- | --- | --- |
| date | str | 90 | `2022-03-31` |
| fund_house | str | 90 | `SBI Mutual Fund` |
| aum_lakh_crore | float64 | 90 | `6.05` |
| aum_crore | int64 | 90 | `605000` |
| num_schemes | int64 | 90 | `186` |

### 04_monthly_sip_inflows.csv
- **File Dimensions**: 48 rows, 6 columns
- **Duplicate Rows**: 0 (0.00%)
- **Missing Values per Column**:
  - `yoy_growth_pct`: 12 nulls (25.00%)

Column Details:

| Column Name | Data Type | Non-Null Count | Example Value |
| --- | --- | --- | --- |
| month | str | 48 | `2022-01` |
| sip_inflow_crore | int64 | 48 | `11517` |
| active_sip_accounts_crore | float64 | 48 | `4.91` |
| new_sip_accounts_lakh | float64 | 48 | `9.1` |
| sip_aum_lakh_crore | float64 | 48 | `4.8` |
| yoy_growth_pct | float64 | 36 | `nan` |

### 05_category_inflows.csv
- **File Dimensions**: 144 rows, 3 columns
- **Duplicate Rows**: 0 (0.00%)
- **Missing Values**: None (100% complete)

Column Details:

| Column Name | Data Type | Non-Null Count | Example Value |
| --- | --- | --- | --- |
| month | str | 144 | `2024-04` |
| category | str | 144 | `Large Cap` |
| net_inflow_crore | float64 | 144 | `2413.0` |

### 06_industry_folio_count.csv
- **File Dimensions**: 21 rows, 6 columns
- **Duplicate Rows**: 0 (0.00%)
- **Missing Values**: None (100% complete)

Column Details:

| Column Name | Data Type | Non-Null Count | Example Value |
| --- | --- | --- | --- |
| month | str | 21 | `2022-01` |
| total_folios_crore | float64 | 21 | `13.26` |
| equity_folios_crore | float64 | 21 | `9.28` |
| debt_folios_crore | float64 | 21 | `1.86` |
| hybrid_folios_crore | float64 | 21 | `0.8` |
| others_folios_crore | float64 | 21 | `1.33` |

### 07_scheme_performance.csv
- **File Dimensions**: 40 rows, 19 columns
- **Duplicate Rows**: 0 (0.00%)
- **Missing Values**: None (100% complete)

Column Details:

| Column Name | Data Type | Non-Null Count | Example Value |
| --- | --- | --- | --- |
| amfi_code | int64 | 40 | `119551` |
| scheme_name | str | 40 | `SBI Bluechip Fund - Regular Plan - Growth` |
| fund_house | str | 40 | `SBI Mutual Fund` |
| category | str | 40 | `Large Cap` |
| plan | str | 40 | `Regular` |
| return_1yr_pct | float64 | 40 | `12.42` |
| return_3yr_pct | float64 | 40 | `12.36` |
| return_5yr_pct | float64 | 40 | `14.45` |
| benchmark_3yr_pct | float64 | 40 | `11.49` |
| alpha | float64 | 40 | `0.87` |
| beta | float64 | 40 | `0.89` |
| sharpe_ratio | float64 | 40 | `0.88` |
| sortino_ratio | float64 | 40 | `1.29` |
| std_dev_ann_pct | float64 | 40 | `14.0` |
| max_drawdown_pct | float64 | 40 | `-21.7` |
| aum_crore | int64 | 40 | `14288` |
| expense_ratio_pct | float64 | 40 | `1.54` |
| morningstar_rating | int64 | 40 | `4` |
| risk_grade | str | 40 | `Moderate` |

### 08_investor_transactions.csv
- **File Dimensions**: 32778 rows, 13 columns
- **Duplicate Rows**: 0 (0.00%)
- **Missing Values**: None (100% complete)

Column Details:

| Column Name | Data Type | Non-Null Count | Example Value |
| --- | --- | --- | --- |
| investor_id | str | 32778 | `INV003054` |
| transaction_date | str | 32778 | `2024-01-01` |
| amfi_code | int64 | 32778 | `119092` |
| transaction_type | str | 32778 | `SIP` |
| amount_inr | int64 | 32778 | `1834` |
| state | str | 32778 | `Telangana` |
| city | str | 32778 | `Hyderabad` |
| city_tier | str | 32778 | `T30` |
| age_group | str | 32778 | `56+` |
| gender | str | 32778 | `Female` |
| annual_income_lakh | float64 | 32778 | `77.1` |
| payment_mode | str | 32778 | `UPI` |
| kyc_status | str | 32778 | `Verified` |

### 09_portfolio_holdings.csv
- **File Dimensions**: 322 rows, 8 columns
- **Duplicate Rows**: 0 (0.00%)
- **Missing Values**: None (100% complete)

Column Details:

| Column Name | Data Type | Non-Null Count | Example Value |
| --- | --- | --- | --- |
| amfi_code | int64 | 322 | `119551` |
| stock_symbol | str | 322 | `POWERGRID` |
| stock_name | str | 322 | `Power Grid Corporation` |
| sector | str | 322 | `Utilities` |
| weight_pct | float64 | 322 | `13.85` |
| market_value_cr | float64 | 322 | `737.09` |
| current_price_inr | float64 | 322 | `6011.08` |
| portfolio_date | str | 322 | `2025-12-31` |

### 10_benchmark_indices.csv
- **File Dimensions**: 8050 rows, 3 columns
- **Duplicate Rows**: 0 (0.00%)
- **Missing Values**: None (100% complete)

Column Details:

| Column Name | Data Type | Non-Null Count | Example Value |
| --- | --- | --- | --- |
| date | str | 8050 | `2022-01-03` |
| index_name | str | 8050 | `NIFTY50` |
| close_value | float64 | 8050 | `17492.79` |

### mock_returns.csv
- **File Dimensions**: 252 rows, 3 columns
- **Duplicate Rows**: 0 (0.00%)
- **Missing Values**: None (100% complete)

Column Details:

| Column Name | Data Type | Non-Null Count | Example Value |
| --- | --- | --- | --- |
| Date | str | 252 | `2025-01-01` |
| Fund_Returns | float64 | 252 | `0.012489879216259` |
| Market_Returns | float64 | 252 | `0.0051696980531683` |