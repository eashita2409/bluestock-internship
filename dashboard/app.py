import sys
from pathlib import Path
import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px

# Setup paths
project_root = Path(__file__).resolve().parent.parent
dashboard_dir = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(dashboard_dir) not in sys.path:
    sys.path.insert(0, str(dashboard_dir))

from components.kpi_cards import render_kpi_card
from components.charts import plot_risk_return, plot_sector_allocations

st.set_page_config(
    page_title="Bluestock Interactive Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Custom CSS if it exists
css_path = dashboard_dir / "assets" / "custom_style.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Database connection
db_path = project_root / "data" / "db" / "mutual_fund_analytics.db"

@st.cache_data
def load_data():
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    
    df_fund = pd.read_sql_query("SELECT * FROM dim_fund", conn)
    df_perf = pd.read_sql_query("SELECT * FROM fact_performance", conn)
    df_aum = pd.read_sql_query("SELECT * FROM fact_aum", conn)
    df_port = pd.read_sql_query("SELECT * FROM fact_portfolio", conn)
    
    conn.close()
    
    # Load D4 metrics
    metrics_path = project_root / "data" / "processed" / "metrics" / "performance_metrics.csv"
    df_metrics = pd.DataFrame()
    if metrics_path.exists():
        df_metrics = pd.read_csv(metrics_path)
        # Rename Unnamed: 0 to scheme_name for merging
        if 'Unnamed: 0' in df_metrics.columns:
            df_metrics = df_metrics.rename(columns={'Unnamed: 0': 'scheme_name'})
            
    return df_fund, df_perf, df_aum, df_port, df_metrics

df_fund, df_perf, df_aum, df_port, df_metrics = load_data()

# Merge performance and D4 metrics
if not df_metrics.empty and 'scheme_name' in df_metrics.columns:
    df_perf = df_perf.merge(df_metrics, on='scheme_name', how='left')

# --- SIDEBAR NAVIGATION & FILTERS ---
st.sidebar.markdown("## Bluestock Analytics")
page = st.sidebar.radio("Navigation Menu:", [
    "1. Executive Overview", 
    "2. Performance Analytics", 
    "3. Portfolio & Allocation", 
    "4. Risk Analytics"
])

st.sidebar.divider()
st.sidebar.markdown("### Global Filters")
categories = ["All"] + sorted(df_fund['category'].dropna().unique().tolist())
selected_category = st.sidebar.selectbox("Asset Category:", categories)

fund_houses = ["All"] + sorted(df_fund['fund_house'].dropna().unique().tolist())
selected_fh = st.sidebar.selectbox("Fund House / AMC:", fund_houses)

# --- FILTER DATA ---
df_fund_f = df_fund.copy()
if selected_category != "All":
    df_fund_f = df_fund_f[df_fund_f['category'] == selected_category]
if selected_fh != "All":
    df_fund_f = df_fund_f[df_fund_f['fund_house'] == selected_fh]

valid_amfis = df_fund_f['amfi_code'].unique()
df_perf_f = df_perf[df_perf['amfi_code'].isin(valid_amfis)]
df_port_f = df_port[df_port['amfi_code'].isin(valid_amfis)]

# For AUM, filter by fund house if selected
if selected_fh != "All":
    df_aum_f = df_aum[df_aum['fund_house'] == selected_fh]
else:
    df_aum_f = df_aum.copy()

# Ensure we have data
if df_perf_f.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# Helper function for chart styling
def format_chart(fig, title):
    fig.update_layout(title=title, template="plotly_white", hovermode="x unified")
    return fig

# --- PAGE 1: EXECUTIVE OVERVIEW ---
if page == "1. Executive Overview":
    st.title("Executive Overview")
    
    # Calculate KPIs
    latest_date = df_aum_f['date'].max()
    df_aum_latest = df_aum_f[df_aum_f['date'] == latest_date]
    total_aum = df_aum_latest['aum_crore'].sum() / 100000  # Lakh Crore
    
    num_schemes = len(df_perf_f)
    
    # Use return_3yr_pct as proxy for CAGR if D4 CAGR is missing for some funds
    cagr_col = 'CAGR' if 'CAGR' in df_perf_f.columns and df_perf_f['CAGR'].notnull().any() else 'return_3yr_pct'
    avg_cagr = df_perf_f[cagr_col].mean()
    if cagr_col == 'CAGR': avg_cagr *= 100 # Convert decimal to percentage
    
    avg_sharpe = df_perf_f['sharpe_ratio'].mean()
    
    top_fund = df_perf_f.sort_values(by='sharpe_ratio', ascending=False).iloc[0]
    top_fund_name = top_fund['scheme_name']
    
    # Render KPIs
    c1, c2, c3, c4 = st.columns(4)
    with c1: render_kpi_card("Total AUM (Lakh Cr)", f"₹ {total_aum:,.2f}")
    with c2: render_kpi_card("Total Schemes", f"{num_schemes}")
    with c3: render_kpi_card(f"Avg {cagr_col} (%)", f"{avg_cagr:.2f}%")
    with c4: render_kpi_card("Avg Sharpe Ratio", f"{avg_sharpe:.2f}")
    
    st.divider()
    
    st.markdown("### Top Performing Fund (by Sharpe Ratio)")
    st.info(f"**{top_fund_name}** | Category: {top_fund['category']} | Sharpe: {top_fund['sharpe_ratio']:.2f} | 3-Yr Return: {top_fund['return_3yr_pct']:.2f}%")
    
    st.markdown("### AUM Growth Over Time")
    aum_trend = df_aum_f.groupby('date')['aum_crore'].sum().reset_index()
    fig = px.area(aum_trend, x='date', y='aum_crore', color_discrete_sequence=['#1a73e8'])
    st.plotly_chart(format_chart(fig, "Total AUM Trend"), use_container_width=True)

# --- PAGE 2: PERFORMANCE ANALYTICS ---
elif page == "2. Performance Analytics":
    st.title("Performance Analytics")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### CAGR (3-Yr Return) Rankings")
        fig_cagr = px.bar(
            df_perf_f.sort_values('return_3yr_pct', ascending=False).head(10), 
            x='return_3yr_pct', y='scheme_name', orientation='h', color='return_3yr_pct', color_continuous_scale='viridis'
        )
        st.plotly_chart(format_chart(fig_cagr, "Top 10 Schemes by 3-Yr Return (%)"), use_container_width=True)
        
    with c2:
        st.markdown("### Sharpe Ratio Rankings")
        fig_sharpe = px.bar(
            df_perf_f.sort_values('sharpe_ratio', ascending=False).head(10), 
            x='sharpe_ratio', y='scheme_name', orientation='h', color='sharpe_ratio', color_continuous_scale='plasma'
        )
        st.plotly_chart(format_chart(fig_sharpe, "Top 10 Schemes by Sharpe Ratio"), use_container_width=True)
        
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("### Beta Comparison")
        fig_beta = px.bar(
            df_perf_f.sort_values('beta', ascending=False).head(10), 
            x='scheme_name', y='beta', color_discrete_sequence=['#ff7043']
        )
        fig_beta.add_hline(y=1.0, line_dash="dash", line_color="gray", annotation_text="Market Beta = 1.0")
        st.plotly_chart(format_chart(fig_beta, "Top Schemes Beta (Volatility vs Market)"), use_container_width=True)
        
    with c4:
        st.markdown("### Historical Drawdown")
        fig_dd = px.bar(
            df_perf_f.sort_values('max_drawdown_pct').head(10), 
            x='scheme_name', y='max_drawdown_pct', color_discrete_sequence=['#ea4335']
        )
        st.plotly_chart(format_chart(fig_dd, "Worst Drawdowns (%)"), use_container_width=True)
        
    st.markdown("### Risk vs Return Scatter Plot")
    st.plotly_chart(plot_risk_return(df_perf_f), use_container_width=True)

# --- PAGE 3: PORTFOLIO & ALLOCATION ---
elif page == "3. Portfolio & Allocation":
    st.title("Portfolio & Allocation Analytics")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Sector Allocation")
        st.plotly_chart(plot_sector_allocations(df_port_f), use_container_width=True)
        
    with c2:
        st.markdown("### Category Allocation (by AUM)")
        cat_grouped = df_perf_f.groupby('category')['aum_crore'].sum().reset_index()
        fig_cat = px.pie(cat_grouped, values='aum_crore', names='category', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(format_chart(fig_cat, "AUM by Asset Category"), use_container_width=True)
        
    st.markdown("### AUM Distribution")
    fig_hist = px.histogram(df_perf_f, x='aum_crore', nbins=30, color_discrete_sequence=['#34a853'])
    st.plotly_chart(format_chart(fig_hist, "Distribution of Fund Sizes (AUM in Cr)"), use_container_width=True)

# --- PAGE 4: RISK ANALYTICS ---
elif page == "4. Risk Analytics":
    st.title("Comprehensive Risk Analytics")
    
    st.markdown("### Risk Metrics Overview")
    
    # Combine standard and generated metrics
    risk_cols = ['scheme_name', 'std_dev_ann_pct', 'beta', 'sortino_ratio', 'max_drawdown_pct']
    if 'Historical_VaR_95' in df_perf_f.columns:
        risk_cols.extend(['Historical_VaR_95', 'Calmar_Ratio'])
        
    df_risk = df_perf_f[risk_cols].sort_values('max_drawdown_pct')
    st.dataframe(df_risk, use_container_width=True)
    
    if 'Historical_VaR_95' in df_perf_f.columns:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### Value at Risk (95% Confidence)")
            df_var = df_perf_f.dropna(subset=['Historical_VaR_95']).sort_values('Historical_VaR_95')
            if not df_var.empty:
                fig_var = px.bar(df_var.head(10), x='scheme_name', y='Historical_VaR_95', color_discrete_sequence=['#ea4335'])
                st.plotly_chart(format_chart(fig_var, "Historical VaR (95%) - Maximum Expected Daily Loss"), use_container_width=True)
            
        with c2:
            st.markdown("### Sortino vs Calmar Ratio")
            df_sc = df_perf_f.dropna(subset=['Sortino_Ratio', 'Calmar_Ratio'])
            if not df_sc.empty:
                fig_sc = px.scatter(df_sc, x='Sortino_Ratio', y='Calmar_Ratio', hover_name='scheme_name', size='aum_crore', color_discrete_sequence=['#ab47bc'])
                st.plotly_chart(format_chart(fig_sc, "Downside Risk-Adjusted Returns"), use_container_width=True)
    else:
        st.info("Additional VaR and Calmar metrics from Deliverable D4 not available for all selected funds. Generating standard risk view.")
        
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("### Volatility Distribution")
        fig_vol = px.box(df_perf_f, x='category', y='std_dev_ann_pct', color='category')
        st.plotly_chart(format_chart(fig_vol, "Annualized Volatility by Category"), use_container_width=True)
    with c4:
        st.markdown("### Sortino Ratio Comparison")
        fig_sort = px.bar(df_perf_f.sort_values('sortino_ratio', ascending=False).head(10), x='scheme_name', y='sortino_ratio', color_discrete_sequence=['#00acc1'])
        st.plotly_chart(format_chart(fig_sort, "Top 10 Schemes by Sortino Ratio"), use_container_width=True)
