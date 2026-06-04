-- 1. AUM Analysis: Rank fund houses by their latest Assets Under Management (AUM)
-- We find the latest date in fact_aum, then select and rank AUM for that date.
WITH latest_date AS (
    SELECT MAX(date) AS max_date FROM fact_aum
)
SELECT 
    fund_house,
    date,
    aum_crore,
    aum_lakh_crore,
    num_schemes,
    RANK() OVER (ORDER BY aum_crore DESC) as aum_rank
FROM fact_aum
WHERE date = (SELECT max_date FROM latest_date)
ORDER BY aum_crore DESC;


-- 2a. Transaction Summary: Total transaction volume and amounts by Transaction Type
SELECT 
    transaction_type,
    COUNT(*) as transaction_count,
    SUM(amount_inr) as total_amount_inr,
    ROUND(AVG(amount_inr), 2) as average_amount_inr
FROM fact_transactions
GROUP BY transaction_type
ORDER BY total_amount_inr DESC;


-- 2b. Payment Mode Breakdown
SELECT 
    payment_mode,
    COUNT(*) as transaction_count,
    SUM(amount_inr) as total_amount_inr,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM fact_transactions), 2) as transaction_pct
FROM fact_transactions
GROUP BY payment_mode
ORDER BY transaction_count DESC;


-- 3. Performance Metrics: Identify top-performing funds (highest 3yr return and Sharpe ratio > 1.0)
SELECT 
    amfi_code,
    scheme_name,
    fund_house,
    category,
    return_3yr_pct,
    return_5yr_pct,
    sharpe_ratio,
    morningstar_rating
FROM fact_performance
WHERE sharpe_ratio > 1.0
ORDER BY return_3yr_pct DESC;


-- 4. SIP Trends: Calculate month-over-month growth in SIP inflows
SELECT 
    month,
    sip_inflow_crore,
    sip_inflow_crore - LAG(sip_inflow_crore) OVER (ORDER BY month) as mom_change_crore,
    ROUND((sip_inflow_crore - LAG(sip_inflow_crore) OVER (ORDER BY month)) * 100.0 / LAG(sip_inflow_crore) OVER (ORDER BY month), 2) as mom_growth_pct,
    active_sip_accounts_crore,
    new_sip_accounts_lakh
FROM fact_sip_industry
ORDER BY month;


-- 5. Portfolio Diversity: Find the top sector allocation for each fund scheme
WITH ranked_sectors AS (
    SELECT 
        p.amfi_code,
        f.scheme_name,
        p.sector,
        SUM(p.weight_pct) as total_weight_pct,
        ROW_NUMBER() OVER (PARTITION BY p.amfi_code ORDER BY SUM(p.weight_pct) DESC) as sector_rank
    FROM fact_portfolio p
    JOIN dim_fund f ON p.amfi_code = f.amfi_code
    GROUP BY p.amfi_code, p.sector
)
SELECT 
    amfi_code,
    scheme_name,
    sector as dominant_sector,
    ROUND(total_weight_pct, 2) as dominant_sector_weight_pct
FROM ranked_sectors
WHERE sector_rank = 1
ORDER BY dominant_sector_weight_pct DESC;
