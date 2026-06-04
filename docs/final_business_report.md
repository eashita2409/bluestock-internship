# Executive Business Report: Mutual Fund Analytics Platform

**Prepared for:** Bluestock Fintech Executive Board  
**Report Compiled on:** 2026-06-04  

---

## Executive Summary

This report delivers a thorough business evaluation of the Bluestock Mutual Fund Analytics Platform. Leveraging a cleaned relational SQLite database of over 46,000 NAV records, 32,778 investor transactions, and active portfolio holdings, we present advanced financial analytics, volatility channels, drawdown exposures, predictive projections, and strategic business recommendations.

---

## 1. Platform Assets & Flows Scale

The platform coordinates substantial capital volumes across multiple asset classes:
- **Total Platform AUM**: ₹ 62.74 Lakh Crore (commanded majorly by SBI Mutual Fund, ICICI Prudential, and HDFC Mutual Fund).
- **Monthly Industry SIP Inflows**: ₹ 31,002 Crore.
- **Active Retail SIP Accounts**: 9.35 Crore.
- **Investor Base**: 32,778 unique active transacting accounts.

---

## 2. Advanced Risk & Volatility Analytics

### 2.1. Volatility Channels (Bollinger Bands)
We computed 20-day Simple Moving Averages (SMAs) and Volatility Bands ($\pm 2$ standard deviations) across major schemes. These bands represent the standard trading channel:
- When a fund's NAV touches the **Upper Band**, it is historically overvalued or overbought, suggesting high near-term momentum but possible mean-reversion.
- When it touches the **Lower Band**, it represents oversold conditions, identifying buy-the-dip opportunities.

### 2.2. Drawdown & Recovery Periods
Drawdown measures the peak-to-trough drop from historical maximum NAV. Evaluating drawdowns helps understand the downside risk of different schemes:
- **SBI Bluechip Fund (AMFI: 119551)**: Max Historical Drawdown is **-15.01%**, with a maximum recovery time of **296 days**.
- **HDFC Top 100 Fund (AMFI: 125497)**: Max Historical Drawdown is **-16.42%**, recovering in **310 days**.
- *Insight*: High-equity funds expose retail investors to temporary standard corrections of 15-20% during market corrections, requiring a minimum holding timeline of 3-5 years to guarantee recovery.

### 2.3. Rolling Returns
Traditional point-to-point returns (e.g., 3-year return from Jan 1 to Dec 31) are highly sensitive to start and end dates. Annualized rolling returns (calculated daily over a 1-year window) show that equity large-cap schemes averaged rolling returns of **12.4% - 14.8%**, indicating a strong probability of wealth creation.

---

## 3. Risk-Adjusted Scheme Rankings

We ranked all 40 schemes based on their Sharpe Ratio (excess return per unit of volatility, assuming a risk-free rate of 5.0%):

| Rank | Scheme Name | Category | 3-Yr Return (%) | Volatility (%) | Sharpe Ratio | Jensen's Alpha |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | HDFC Top 100 Fund - Regular - Growth | Large Cap | 14.84% | 9.28% | 1.06 | 1.82% |
| **2** | Mirae Asset Large Cap Fund - Regular | Large Cap | 14.81% | 9.25% | 1.06 | 1.79% |
| **3** | ICICI Pru Bluechip Fund - Direct | Large Cap | 14.41% | 9.14% | 1.03 | 1.45% |
| **4** | ICICI Pru Liquid Fund - Regular | Liquid | 7.68% | 0.35% | 7.68 | 0.12% |
| **5** | HDFC Short Term Debt Fund - Regular | Short Debt | 7.37% | 1.29% | 1.84 | 0.45% |

*Interpretation*: While Liquid and Short-Term Debt schemes show extremely high Sharpe Ratios due to near-zero volatility (denominator), equity large-cap funds like HDFC Top 100 and Mirae Asset Large Cap represent the most efficient equity options, generating 1.06% of excess return for every 1.0% of annualized standard deviation risk.

---

## 4. Sector Concentration & Overlaps

We analyzed stock portfolio compositions to detect diversification risk:
- **Financial Services Concentration**: Financials (Banking, Insurance, and NBFCs) and IT command the highest weight across equity portfolios, often representing **30% - 48%** of total assets.
- **Portfolio Sector Overlaps**: 
  - Comparing **SBI Bluechip Fund** vs. **ICICI Pru Bluechip Fund** shows a sector overlap of **84.52%**.
  - *Business Action*: Having both schemes in a retail portfolio provides zero diversification benefits, as both track similar large-cap index constituents.

---

## 5. Predictive Simulations

### 5.1. 30-Day NAV Forecasting
Applying degree 2 polynomial curve fitting on historical NAV price vectors predicts a short-term upward momentum for large-cap schemes, supported by steady monthly inflows.

### 5.2. Compounding Wealth simulator
Modeling the long-term compounding effects highlights the wealth multiplier:
- **SIP Simulator**: A monthly SIP of **₹5,000** at a conservative **12.0% expected return** over **15 years** results in:
  - Total Invested Principal: ₹ 9.00 Lakh
  - Estimated Maturity Value: **₹ 25.22 Lakh**
  - Net Wealth Gained: **₹ 16.22 Lakh** (180.2% growth)
- **Lumpsum Simulator**: A one-off lumpsum of **₹50,000** at **12.0% expected return** over **15 years** compounds to:
  - Estimated Maturity Value: **₹ 2.74 Lakh** (448.7% growth)

---

## 6. Strategic Business Recommendations for Bluestock Fintech

1. **Portfolio Overlap Alert Widget**: Integrate a "Portfolio Overlap Check" tool on the client dashboard. When a user holds multiple large-cap funds, alert them of high overlap (>75%) and suggest diversifying into mid-cap or international funds.
2. **Democratize SIPs for Gen Z**: The transaction logs show that the 18-25 age group represents a large share of UPI transactions but has smaller ticket sizes. Create a "Micro-SIP" promotion targeting UPI auto-mandates starting at ₹250/month.
3. **Risk-Adjusted Star Badges**: Instead of highlighting raw returns, label schemes by their risk-adjusted Sharpe rankings. Promoting funds like Mirae Asset Large Cap as "Risk-Efficient Choice" builds platform credibility.
