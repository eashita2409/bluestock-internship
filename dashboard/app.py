import streamlit as st
import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np

# Set Streamlit page config
st.set_page_config(
    page_title="Bluestock Mutual Fund Analytics Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Custom CSS
css_path = Path(__file__).resolve().parent / "assets" / "custom_style.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Import components
from components.kpi_cards import render_kpi_card
from components.charts import (
    plot_nav_tracker,
    plot_sip_inflows,
    plot_risk_return,
    plot_sector_allocations,
    plot_demographics,
    plot_payment_modes
)

# Resolve DB path
db_path = Path(__file__).resolve().parent.parent / "data" / "db" / "mutual_fund_analytics.db"

@st.cache_resource
def get_db_connection():
    """Establishes connection to the database."""
    if not db_path.exists():
        st.error(f"Database not found at {db_path}. Please run database loading first.")
        return None
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

conn = get_db_connection()

if conn:
    # --- LOAD CACHED DATA ---
    @st.cache_data
    def load_data(query):
        return pd.read_sql_query(query, conn)

    df_fund = load_data("SELECT * FROM dim_fund;")
    df_perf = load_data("SELECT * FROM fact_performance;")
    df_sip = load_data("SELECT * FROM fact_sip_industry ORDER BY month;")
    df_tx = load_data("SELECT * FROM fact_transactions;")
    df_aum = load_data("SELECT * FROM fact_aum ORDER BY date;")
    df_nav = load_data("SELECT n.amfi_code, f.scheme_name, n.date, n.nav, f.category, f.fund_house FROM fact_nav n JOIN dim_fund f ON n.amfi_code = f.amfi_code ORDER BY n.amfi_code, n.date;")
    df_port = load_data("SELECT p.*, f.scheme_name, f.category FROM fact_portfolio p JOIN dim_fund f ON p.amfi_code = f.amfi_code;")

    # --- SIDEBAR NAVIGATION & GLOBAL FILTERS ---
    st.sidebar.markdown(
        "<h2 style='text-align: center; color: #1a73e8;'>Bluestock Fintech</h2>", 
        unsafe_allow_html=True
    )
    st.sidebar.markdown(
        "<p style='text-align: center; font-size: 0.9rem; color: #5f6368;'>Mutual Fund Analytics Dashboard</p>", 
        unsafe_allow_html=True
    )
    st.sidebar.divider()

    # Page Select
    page = st.sidebar.radio(
        "Navigate Pages:",
        ["Overview & KPIs", "NAV Tracker", "SIP Trends", "Scheme Comparison", "Portfolio & Sectors", "Investor Demographics"]
    )
    
    st.sidebar.divider()
    st.sidebar.markdown("### Global Filters")
    
    # Global Filters (Category & Fund House)
    categories = ["All"] + sorted(list(df_fund['category'].dropna().unique()))
    selected_category = st.sidebar.selectbox("Asset Class / Category:", categories)
    
    fund_houses = ["All"] + sorted(list(df_fund['fund_house'].dropna().unique()))
    selected_fh = st.sidebar.selectbox("Fund House / AMC:", fund_houses)

    # Filter dataframes based on global filters
    def apply_global_filters(df, category_col='category', fh_col='fund_house'):
        filtered_df = df.copy()
        if category_col in filtered_df.columns and selected_category != "All":
            filtered_df = filtered_df[filtered_df[category_col] == selected_category]
        if fh_col in filtered_df.columns and selected_fh != "All":
            filtered_df = filtered_df[filtered_df[fh_col] == selected_fh]
        return filtered_df

    df_fund_f = apply_global_filters(df_fund)
    df_perf_f = apply_global_filters(df_perf)
    df_nav_f = apply_global_filters(df_nav)
    df_port_f = apply_global_filters(df_port)
    
    # Map global filter to transactions
    df_tx_f = df_tx.copy()
    if selected_category != "All" or selected_fh != "All":
        filtered_codes = df_fund_f['amfi_code'].unique()
        df_tx_f = df_tx_f[df_tx_f['amfi_code'].isin(filtered_codes)]

    # --- PAGE 1: OVERVIEW & KPIS ---
    if page == "Overview & KPIs":
        st.markdown("# Executive Platform Overview")
        st.markdown("Key platform performance metrics, assets scale, and recent activity overview.")
        
        # Calculate KPIs
        # Total AUM (Latest date sum)
        latest_aum_date = df_aum['date'].max()
        df_aum_latest = df_aum[df_aum['date'] == latest_aum_date]
        total_aum_cr = df_aum_latest['aum_crore'].sum()
        total_aum_lakh_cr = total_aum_cr / 100000
        
        # Latest Month SIP Inflow
        latest_sip_row = df_sip.iloc[-1]
        latest_sip_inflow = latest_sip_row['sip_inflow_crore']
        active_sip_accounts = latest_sip_row['active_sip_accounts_crore']
        
        # Total Unique Investors in transaction database
        total_investors = df_tx['investor_id'].nunique()
        
        # Display KPI cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            render_kpi_card("Total AUM (Latest)", f"₹ {total_aum_lakh_cr:.2f}L Cr", "🏦")
        with col2:
            render_kpi_card("Monthly SIP Inflow", f"₹ {latest_sip_inflow:,} Cr", "📈")
        with col3:
            render_kpi_card("Active SIP Accounts", f"{active_sip_accounts:.2f} Cr", "👥")
        with col4:
            render_kpi_card("Unique Investors", f"{total_investors:,}", "💳")
            
        st.divider()
        
        # Charts section
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown("### Assets Under Management (AUM) Share by AMC")
            # Group latest AUM by fund house
            df_aum_grouped = df_aum_latest.groupby('fund_house')['aum_crore'].sum().reset_index()
            df_aum_grouped = df_aum_grouped.sort_values(by='aum_crore', ascending=False)
            
            fig_aum = px.bar(
                df_aum_grouped,
                x='aum_crore',
                y='fund_house',
                orientation='h',
                labels={'aum_crore': 'AUM (INR Crore)', 'fund_house': 'Fund House'},
                color='aum_crore',
                color_continuous_scale="blues"
            )
            fig_aum.update_layout(template="plotly_white", coloraxis_showscale=False)
            fig_aum.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_aum, use_container_width=True)
            
        with c2:
            st.markdown("### Asset Allocation Breakdown")
            df_cat_grouped = df_perf_f.groupby('category')['aum_crore'].sum().reset_index()
            fig_pie = px.pie(
                df_cat_grouped,
                values='aum_crore',
                names='category',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_pie.update_layout(template="plotly_white")
            st.plotly_chart(fig_pie, use_container_width=True)

    # --- PAGE 2: NAV TRACKER ---
    elif page == "NAV Tracker":
        st.markdown("# Net Asset Value (NAV) Tracker")
        st.markdown("Visualize daily NAV historical prices. Use filters on the left to restrict categories or fund houses.")
        
        # Dropdown selection for schemes
        schemes = sorted(list(df_nav_f['scheme_name'].unique()))
        
        if not schemes:
            st.warning("No schemes found matching the selected global filters.")
        else:
            default_schemes = schemes[:3]
            selected_schemes = st.multiselect("Select Schemes to Plot:", schemes, default=default_schemes)
            
            if selected_schemes:
                fig_nav = plot_nav_tracker(df_nav_f, selected_schemes)
                st.plotly_chart(fig_nav, use_container_width=True)
                
                # Show data table for selected schemes
                df_nav_show = df_nav_f[df_nav_f['scheme_name'].isin(selected_schemes)].copy()
                df_nav_show = df_nav_show.pivot(index='date', columns='scheme_name', values='nav')
                st.markdown("### Historical NAV Data Table")
                st.dataframe(df_nav_show.tail(30), use_container_width=True)
            else:
                st.info("Please select at least one scheme to visualize.")

    # --- PAGE 3: SIP TRENDS ---
    elif page == "SIP Trends":
        st.markdown("# Industry-wide SIP Inflow Analysis")
        st.markdown("Monthly tracking of industry-wide SIP inflows, active investor accounts, and net category inflows.")
        
        fig_sip = plot_sip_inflows(df_sip)
        st.plotly_chart(fig_sip, use_container_width=True)
        
        st.divider()
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### Net Monthly Inflows by Fund Category")
            query_cat = "SELECT month, category, net_inflow_crore FROM fact_category_inflows ORDER BY month;"
            df_cat = load_data(query_cat)
            
            # Pivot category inflows
            df_cat_pivot = df_cat.pivot(index='month', columns='category', values='net_inflow_crore').fillna(0)
            
            fig_cat = px.line(
                df_cat,
                x='month',
                y='net_inflow_crore',
                color='category',
                labels={'net_inflow_crore': 'Net Inflow (INR Crore)', 'month': 'Month'},
                title="Category Net Monthly Inflows Over Time"
            )
            fig_cat.update_layout(template="plotly_white")
            st.plotly_chart(fig_cat, use_container_width=True)
            
        with c2:
            st.markdown("### Cumulative Sector / Assets Folio Count (Crores)")
            query_folios = "SELECT month, equity_folios_crore, debt_folios_crore, hybrid_folios_crore FROM fact_industry_folios ORDER BY month;"
            df_fol = load_data(query_folios)
            
            fig_fol = go.Figure()
            fig_fol.add_trace(go.Scatter(x=df_fol['month'], y=df_fol['equity_folios_crore'], name="Equity Folios (Cr)", mode="lines+markers"))
            fig_fol.add_trace(go.Scatter(x=df_fol['month'], y=df_fol['debt_folios_crore'], name="Debt Folios (Cr)", mode="lines"))
            fig_fol.add_trace(go.Scatter(x=df_fol['month'], y=df_fol['hybrid_folios_crore'], name="Hybrid Folios (Cr)", mode="lines"))
            
            fig_fol.update_layout(
                title="Folio Count Expansion by Asset Class",
                xaxis_title="Month",
                yaxis_title="Folios (Crores)",
                template="plotly_white"
            )
            st.plotly_chart(fig_fol, use_container_width=True)

    # --- PAGE 4: SCHEME COMPARISON ---
    elif page == "Scheme Comparison":
        st.markdown("# Mutual Fund Scheme Comparison")
        st.markdown("Compare key metrics, Sharpe Ratios, volatility, and historical annualized returns across multiple schemes.")
        
        schemes = sorted(list(df_perf_f['scheme_name'].dropna().unique()))
        
        if not schemes:
            st.warning("No schemes found matching the selected global filters.")
        else:
            selected_comp = st.multiselect("Select Schemes to Compare (Max 5):", schemes, default=schemes[:3])
            
            if selected_comp:
                df_comp = df_perf_f[df_perf_f['scheme_name'].isin(selected_comp)]
                
                # Render Comparison Table
                comp_cols = [
                    'scheme_name', 'category', 'return_3yr_pct', 'std_dev_ann_pct', 
                    'sharpe_ratio', 'aum_crore', 'expense_ratio_pct', 'morningstar_rating'
                ]
                df_comp_table = df_comp[comp_cols].rename(columns={
                    'scheme_name': 'Scheme Name',
                    'category': 'Category',
                    'return_3yr_pct': '3-Yr Return (%)',
                    'std_dev_ann_pct': 'Volatility (%)',
                    'sharpe_ratio': 'Sharpe Ratio',
                    'aum_crore': 'AUM (Cr)',
                    'expense_ratio_pct': 'Expense Ratio (%)',
                    'morningstar_rating': 'Rating'
                })
                
                st.dataframe(df_comp_table.reset_index(drop=True), use_container_width=True)
                
                # Render Bar Charts comparing returns and Sharpe ratios
                c1, c2 = st.columns(2)
                with c1:
                    fig_ret = px.bar(
                        df_comp,
                        x='return_3yr_pct',
                        y='scheme_name',
                        orientation='h',
                        title="3-Year Annualized Return (%) Comparison",
                        labels={'return_3yr_pct': 'Return (%)', 'scheme_name': 'Scheme'},
                        color='return_3yr_pct',
                        color_continuous_scale="viridis"
                    )
                    fig_ret.update_layout(template="plotly_white", coloraxis_showscale=False)
                    st.plotly_chart(fig_ret, use_container_width=True)
                    
                with c2:
                    fig_sr = px.bar(
                        df_comp,
                        x='sharpe_ratio',
                        y='scheme_name',
                        orientation='h',
                        title="Sharpe Ratio Comparison (Higher means better risk-adjusted return)",
                        labels={'sharpe_ratio': 'Sharpe Ratio', 'scheme_name': 'Scheme'},
                        color='sharpe_ratio',
                        color_continuous_scale="magenta"
                    )
                    fig_sr.update_layout(template="plotly_white", coloraxis_showscale=False)
                    st.plotly_chart(fig_sr, use_container_width=True)
                    
                # Risk vs Return scatter plot showing where selected compare to all
                st.divider()
                st.markdown("### Risk vs. Return Positioning (Full Universe vs Selected)")
                fig_scat = plot_risk_return(df_perf_f)
                
                # Add highlighting trace for selected schemes
                fig_scat.add_trace(
                    go.Scatter(
                        x=df_comp['std_dev_ann_pct'],
                        y=df_comp['return_3yr_pct'],
                        mode='markers+text',
                        marker=dict(size=14, color='red', symbol='x', line=dict(width=2, color='white')),
                        text=df_comp['scheme_name'].apply(lambda x: x[:20] + "..."),
                        textposition="top center",
                        name="Compared Schemes"
                    )
                )
                st.plotly_chart(fig_scat, use_container_width=True)
            else:
                st.info("Please select schemes to compare.")

    # --- PAGE 5: PORTFOLIO & SECTORS ---
    elif page == "Portfolio & Sectors":
        st.markdown("# Portfolio Holdings & Sector Allocations")
        st.markdown("Analyze stock holdings and sector diversifications of selected mutual fund schemes.")
        
        # Scheme Dropdown Select
        schemes = sorted(list(df_port_f['scheme_name'].dropna().unique()))
        
        if not schemes:
            st.warning("No portfolio data found matching the selected global filters.")
        else:
            selected_scheme = st.selectbox("Select Scheme to Inspect Portfolio:", schemes)
            
            df_port_scheme = df_port_f[df_port_f['scheme_name'] == selected_scheme]
            
            c1, c2 = st.columns([1, 1])
            with c1:
                st.markdown(f"### Top Stock Holdings in {selected_scheme}")
                df_port_table = df_port_scheme[['stock_name', 'stock_symbol', 'weight_pct', 'market_value_cr', 'current_price_inr']]
                df_port_table = df_port_table.sort_values(by='weight_pct', ascending=False)
                df_port_table = df_port_table.rename(columns={
                    'stock_name': 'Stock Name',
                    'stock_symbol': 'Ticker',
                    'weight_pct': 'Weight (%)',
                    'market_value_cr': 'Market Value (Cr)',
                    'current_price_inr': 'Current Price (INR)'
                })
                st.dataframe(df_port_table.reset_index(drop=True), use_container_width=True)
                
            with c2:
                st.markdown("### Sector Allocation Weights")
                df_sect_grouped = df_port_scheme.groupby('sector')['weight_pct'].sum().reset_index()
                df_sect_grouped = df_sect_grouped.sort_values(by='weight_pct', ascending=False)
                
                fig_sect = px.bar(
                    df_sect_grouped,
                    x='weight_pct',
                    y='sector',
                    orientation='h',
                    labels={'weight_pct': 'Sector Weight (%)', 'sector': 'Sector'},
                    color='weight_pct',
                    color_continuous_scale="gnbu"
                )
                fig_sect.update_layout(template="plotly_white", coloraxis_showscale=False)
                fig_sect.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_sect, use_container_width=True)
                
            st.divider()
            # General sector allocation across ALL filtered schemes
            st.markdown("### General Sector Allocation Across ALL Filtered Schemes")
            fig_all_sect = plot_sector_allocations(df_port_f)
            st.plotly_chart(fig_all_sect, use_container_width=True)

    # --- PAGE 6: INVESTOR DEMOGRAPHICS ---
    elif page == "Investor Demographics":
        st.markdown("# Investor Demographics & Behavior")
        st.markdown("Detailed profiles of investors, transaction behavior, payment methods, and correlation heatmap.")
        
        c1, c2 = st.columns(2)
        with c1:
            demo_opt = st.selectbox("Group Transaction Counts by:", ["age_group", "city_tier", "gender", "kyc_status"])
            fig_demo = plot_demographics(df_tx_f, demo_opt)
            st.plotly_chart(fig_demo, use_container_width=True)
            
        with c2:
            fig_pay = plot_payment_modes(df_tx_f)
            st.plotly_chart(fig_pay, use_container_width=True)
            
        st.divider()
        
        c3, c4 = st.columns([1, 1])
        with c3:
            st.markdown("### Transaction Type Volume Distribution")
            df_tx_type = df_tx_f.groupby('transaction_type').size().reset_index(name='count')
            fig_type = px.bar(
                df_tx_type,
                x='transaction_type',
                y='count',
                labels={'count': 'Number of Transactions', 'transaction_type': 'Transaction Type'},
                color='transaction_type',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_type.update_layout(template="plotly_white", showlegend=False)
            st.plotly_chart(fig_type, use_container_width=True)
            
        with c4:
            st.markdown("### Investor Profile Correlation Heatmap")
            # Map age group to numeric midpoints
            age_map = {
                "18-25": 21.5,
                "26-35": 30.5,
                "36-45": 40.5,
                "46-55": 50.5,
                "56+": 60.0
            }
            df_tx_corr = df_tx_f.copy()
            df_tx_corr['age_midpoint'] = df_tx_corr['age_group'].map(age_map).fillna(35.0)
            
            numeric_df = df_tx_corr[['amount_inr', 'annual_income_lakh', 'age_midpoint']].dropna()
            
            corr = numeric_df.corr()
            
            fig_heat = px.imshow(
                corr,
                text_auto=True,
                color_continuous_scale="RdBu_r",
                zmin=-1.0,
                zmax=1.0,
                title="Correlation Heatmap (Age vs Income vs Amount)"
            )
            fig_heat.update_layout(template="plotly_white")
            st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.error("Could not connect to the database. Make sure the database exists.")
