# Database Validation Report

Report Generated at: 2026-06-04 11:58:08

This report validates the schema, constraint integrity, and data sanity of the loaded SQLite database.

## 1. Table Existence Check

> [!NOTE]
> All 11 expected tables exist in the database.

| Table Name | Row Count | Status |
| --- | --- | --- |
| `dim_fund` | 40 | PASSED (Non-empty) |
| `dim_date` | 1297 | PASSED (Non-empty) |
| `fact_nav` | 46000 | PASSED (Non-empty) |
| `fact_transactions` | 32778 | PASSED (Non-empty) |
| `fact_performance` | 40 | PASSED (Non-empty) |
| `fact_portfolio` | 322 | PASSED (Non-empty) |
| `fact_aum` | 90 | PASSED (Non-empty) |
| `fact_sip_industry` | 48 | PASSED (Non-empty) |
| `fact_category_inflows` | 144 | PASSED (Non-empty) |
| `fact_industry_folios` | 21 | PASSED (Non-empty) |
| `fact_benchmark_indices` | 8050 | PASSED (Non-empty) |

## 2. Foreign Key Constraint Checks

> [!NOTE]
> No foreign key violations detected in the database (`PRAGMA foreign_key_check` returned 0 violations).

## 3. Data Sanity Rules Validation

| Rule Description | Status |
| --- | --- |
| fact_nav: NAV values must be positive (> 0) | PASSED |
| fact_transactions: Transaction amounts must be positive (> 0) | PASSED |
| dim_date: Date keys must be formatted as YYYY-MM-DD | PASSED |
| fact_sip_industry: Month keys must be formatted as YYYY-MM | PASSED |
| fact_portfolio: Stock weights must be in range (0, 100] | PASSED |
| fact_nav: All codes must exist in dim_fund | PASSED |
| fact_transactions: All codes must exist in dim_fund | PASSED |

## 4. Overall Validation Summary

> [!TIP]
> **SUCCESS**: Database validation passed successfully! All integrity constraints and data validation checks hold.