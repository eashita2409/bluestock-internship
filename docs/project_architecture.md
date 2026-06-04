# Technical Project Architecture Document: Mutual Fund Analytics Platform

This document describes the folder structure, data models, processing pipelines, and system dependencies of the Bluestock Mutual Fund Analytics Platform.

---

## 1. System Folder Architecture

```
bluestock-internship/
├── .gitignore
├── requirements.txt            # System library dependencies
├── data/
│   ├── raw/                    # Original Bluestock CSV files & live JSON API dumps
│   ├── processed/              # Cleaned, standardized CSV files ready for database load
│   └── db/
│       └── mutual_fund_analytics.db # SQLite relational database
├── src/
│   ├── __init__.py
│   ├── utils.py                # Core dynamic path resolving & CSV loading utilities
│   └── analytics.py            # Financial formulas (CAGR, Sharpe, Beta, Alpha)
├── scripts/
│   ├── data_ingestion.py       # Ingests, checks reference integrity, generates data quality report
│   ├── data_cleaning.py        # Cleans, forward-fills, and standardizes CSV data
│   ├── database_loading.py     # Executes Schema DDL and loads CSV tables into SQLite
│   ├── database_validation.py  # Checks row counts, schemas, and foreign keys
│   ├── run_queries.py          # Executes analytical SQL queries and generates CSV exports
│   ├── eda_analysis.py         # Performs advanced statistics and outputs static charts
│   └── predictive_analysis.py  # Drawdowns, Bollinger bands, and polynomial price forecasting
├── sql/
│   ├── schema.sql              # Relational SQLite database schema DDL script
│   └── queries.sql             # Day 2 core analytical queries
├── notebooks/
│   ├── 01_data_ingestion.ipynb # Interactive ingestion & API fetching
│   ├── 01_exploratory_analysis.ipynb # Getting started exploratory sandbox
│   ├── 02_database_operations.ipynb  # Rebuilding database & querying
│   ├── 03_eda_and_visualization.ipynb # Advanced plotting and analysis
│   └── 04_advanced_analytics.ipynb   # Drawdowns, forecasting, and simulations
├── dashboard/
│   ├── app.py                  # Streamlit dashboard main application file
│   ├── assets/
│   │   └── custom_style.css    # Custom CSS for glassmorphic cards and theme overrides
│   └── components/
│       ├── kpi_cards.py        # Reusable HTML metric card generator
│       └── charts.py           # Interactive Plotly chart builders
├── tests/
│   ├── test_analytics.py       # Unit tests for financial formulas (pytest)
│   └── test_database.py        # Relational database integrity & constraint tests
└── docs/
    ├── data_quality_report.md  # Day 1 data quality details
    ├── database_validation_report.md # SQLite integrity check logs
    ├── database_analysis_report.md  # Day 2 SQL query outputs and insights
    ├── eda_report.md           # Day 3 advanced stats & findings
    ├── final_business_report.md # Day 4 executive summary & recommendations
    ├── project_architecture.md  # System architecture & data dictionary
    └── final_summary.md        # High-level summary of capstone milestones
```

---

## 2. Relational Database Design (Star Schema)

The SQLite database `mutual_fund_analytics.db` is built as a star schema consisting of 2 dimension tables and 9 fact/helper tables:

```mermaid
erDiagram
    dim_fund {
        int amfi_code PK
        text fund_house
        text scheme_name
        text category
        text sub_category
        text plan
        text launch_date
        text benchmark
        real expense_ratio_pct
        real exit_load_pct
        real min_sip_amount
        real min_lumpsum_amount
        text fund_manager
        text risk_category
        text sebi_category_code
    }
    dim_date {
        text date PK
        int year
        int month
        int day
        int quarter
        int day_of_week
        int is_weekend
    }
    fact_nav {
        int amfi_code FK
        text date FK
        real nav
    }
    fact_transactions {
        int transaction_id PK
        text investor_id
        text transaction_date FK
        int amfi_code FK
        text transaction_type
        real amount_inr
        text state
        text city
        text city_tier
        text age_group
        text gender
        real annual_income_lakh
        text payment_mode
        text kyc_status
    }
    fact_performance {
        int amfi_code PK, FK
        text scheme_name
        text fund_house
        text category
        text plan
        real return_1yr_pct
        real return_3yr_pct
        real return_5yr_pct
        real benchmark_3yr_pct
        real alpha
        real beta
        real sharpe_ratio
        real sortino_ratio
        real std_dev_ann_pct
        real max_drawdown_pct
        real aum_crore
        real expense_ratio_pct
        int morningstar_rating
        text risk_grade
        int has_negative_sharpe
    }
    fact_portfolio {
        int portfolio_id PK
        int amfi_code FK
        text stock_symbol
        text stock_name
        text sector
        real weight_pct
        real market_value_cr
        real current_price_inr
        text portfolio_date FK
    }
    fact_aum {
        int aum_id PK
        text date FK
        text fund_house
        real aum_lakh_crore
        real aum_crore
        int num_schemes
    }
    fact_benchmark_indices {
        int benchmark_id PK
        text date FK
        text index_name
        real close_value
    }
    
    dim_fund ||--o{ fact_nav : "identifies"
    dim_date ||--o{ fact_nav : "dates"
    dim_fund ||--o{ fact_transactions : "purchases"
    dim_date ||--o{ fact_transactions : "settles"
    dim_fund ||--|| fact_performance : "evaluates"
    dim_fund ||--o{ fact_portfolio : "holds"
    dim_date ||--o{ fact_portfolio : "allocates"
    dim_date ||--o{ fact_aum : "measures"
    dim_date ||--o{ fact_benchmark_indices : "references"
```

---

## 3. Data Processing Pipelines

```mermaid
flowchart TD
    RawCSV["Raw Bluestock CSVs (data/raw/)"] --> CleanScript["Cleaning Pipeline (scripts/data_cleaning.py)"]
    CleanScript --> ProcessedCSV["Cleaned CSVs (data/processed/)"]
    ProcessedCSV --> LoadScript["DB Loader (scripts/database_loading.py)"]
    SchemaDDL["Schema DDL (sql/schema.sql)"] --> LoadScript
    LoadScript --> SQLiteDB["SQLite Database (data/db/)"]
    SQLiteDB --> ValScript["Validator (scripts/database_validation.py)"]
    SQLiteDB --> QueryScript["Query Runner (scripts/run_queries.py)"]
    SQLiteDB --> EDAScript["EDA script (scripts/eda_analysis.py)"]
    SQLiteDB --> PredScript["Predictive models (scripts/predictive_analysis.py)"]
    SQLiteDB --> Dashboard["Streamlit Dashboard (dashboard/app.py)"]
    
    ValScript --> ValRep["Validation Report (docs/)"]
    QueryScript --> QueryRep["Day 2 Report & CSVs (docs/ & data/)"]
    EDAScript --> EDARep["EDA Report & Charts (docs/)"]
    PredScript --> ForecastPlots["Forecast metrics"]
    Dashboard --> InteractiveViews["Browser Dashboard UI"]
```

---

## 4. Primary Data Dictionary

### Table: `dim_fund`
Primary dimension catalog of all mutual fund schemes.
- `amfi_code` (INTEGER, PK): Association of Mutual Funds in India code, primary identifier.
- `fund_house` (TEXT): Asset Management Company name (e.g. "SBI Mutual Fund").
- `scheme_name` (TEXT): Official fund scheme title.
- `category` (TEXT): Broad asset class (e.g. "Equity", "Debt", "Liquid").
- `expense_ratio_pct` (REAL): Annual fund operating costs expressed as a percentage of assets.
- `min_sip_amount` (REAL): Minimum SIP installment value.

### Table: `fact_nav`
Tracks daily Net Asset Value prices.
- `amfi_code` (INTEGER, FK): Links to `dim_fund`.
- `date` (TEXT, FK): YYYY-MM-DD date key, links to `dim_date`.
- `nav` (REAL): Day's closing NAV price.

### Table: `fact_transactions`
Captures individual investor transactions.
- `transaction_id` (INTEGER, PK): Primary key auto-incremented.
- `investor_id` (TEXT): Unique investor account identifier.
- `transaction_date` (TEXT, FK): Links to `dim_date`.
- `amfi_code` (INTEGER, FK): Links to `dim_fund`.
- `transaction_type` (TEXT): "SIP", "Lumpsum", or "Redemption".
- `amount_inr` (REAL): Value of the transaction.
- `annual_income_lakh` (REAL): Annual income in Lakhs.
- `payment_mode` (TEXT): "UPI", "Net Banking", "Cheque", or "Mandate".
- `kyc_status` (TEXT): "Verified" or "Pending".
