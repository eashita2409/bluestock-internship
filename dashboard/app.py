import streamlit as st
import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# Set Streamlit page config
st.set_page_config(
    page_title="Bluestock Mutual Fund Analytics Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Custom CSS
css_path = Path(__file__).resolve().parent / "assets" / "custom_style.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Import components & analytics
from components.kpi_cards import render_kpi_card
from components.charts import (
    plot_nav_tracker,
    plot_sip_inflows,
    plot_risk_return,
    plot_sector_allocations,
    plot_demographics,
    plot_payment_modes
)
from scripts.predictive_analysis import (
    calculate_sip_growth,
    calculate_lumpsum_growth,
    calculate_bollinger_bands,
    calculate_drawdowns,
    calculate_rolling_returns,
    forecast_nav_trend
)

# Resolve DB path
db_path = Path(__file__).resolve().parent.parent / "data" / "db" / "mutual_fund_analytics.db"

@st.cache_resource
def get_db_connection():
    """Establishes connection to the database."""
    if not db_path.exists():
        st.error(f"Database not found at {db_path}. Please check configuration.")
        return None
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

conn = get_db_connection()

# PDF Generator using ReportLab
def generate_pdf_report(df_perf_table, total_aum_lakh_cr, latest_sip_inflow):
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        story = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=20,
            textColor=colors.HexColor('#1a73e8'),
            spaceAfter=15
        )
        story.append(Paragraph("Bluestock Mutual Fund Analytics Report", title_style))
        story.append(Spacer(1, 10))
        
        body_style = styles['Normal']
        story.append(Paragraph(f"<b>Total Assets Under Management (AUM):</b> INR {total_aum_lakh_cr:.2f} Lakh Crore", body_style))
        story.append(Paragraph(f"<b>Latest Month SIP Inflow:</b> INR {latest_sip_inflow:,} Crore", body_style))
        story.append(Spacer(1, 15))
        
        story.append(Paragraph("<b>Top Scheme Performance Rankings (3-Year Annualized):</b>", styles['Heading2']))
        story.append(Spacer(1, 8))
        
        # Format table data
        table_data = [['Scheme Name', 'Category', '3-Yr Return (%)', 'Sharpe Ratio', 'AUM (Cr)']]
        for idx, row in df_perf_table.head(10).iterrows():
            table_data.append([
                str(row['Scheme Name'])[:30] + '...',
                str(row['Category']),
                f"{row['3-Yr Return (%)']:.2f}%",
                f"{row['Sharpe Ratio']:.2f}",
                f"{row['AUM (Cr)']:,}"
            ])
            
        t = Table(table_data, colWidths=[180, 100, 80, 70, 70])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a73e8')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f1f3f4')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTSIZE', (0,0), (-1,-1), 8),
        ]))
        story.append(t)
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"Error generating PDF: {e}")
        return None

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
    df_port = load_data("SELECT p.*, f.scheme_name, f.category, f.fund_house FROM fact_portfolio p JOIN dim_fund f ON p.amfi_code = f.amfi_code;")

    # --- SIDEBAR NAVIGATION & THEME SELECTOR ---
    st.sidebar.markdown(
        "<h2 style='text-align: center; color: #1a73e8;'>Bluestock Fintech</h2>", 
        unsafe_allow_html=True
    )
    st.sidebar.markdown(
        "<p style='text-align: center; font-size: 0.9rem; color: #5f6368;'>Mutual Fund Analytics Dashboard</p>", 
        unsafe_allow_html=True
    )
    st.sidebar.divider()

    # Theme selection & Custom theme injector
    theme_choice = st.sidebar.selectbox("Dashboard Theme Style:", ["Light Theme", "Dark Neon Theme"])
    
    def inject_theme(choice):
        if choice == "Dark Neon Theme":
            st.markdown("""
                <style>
                .stApp {
                    background-color: #0b0f19 !important;
                    color: #e2e8f0 !important;
                }
                [data-testid="stSidebar"] {
                    background-color: #070a13 !important;
                    border-right: 1px solid #1e293b !important;
                }
                [data-testid="stSidebar"] * {
                    color: #e2e8f0 !important;
                }
                .kpi-card {
                    background: linear-gradient(135deg, #0f172a 0%, #020617 100%) !important;
                    border: 1px solid rgba(56, 189, 248, 0.3) !important;
                    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4) !important;
                }
                .kpi-value {
                    color: #38bdf8 !important;
                }
                .kpi-label {
                    color: #94a3b8 !important;
                }
                .stTabs [data-baseweb="tab"] {
                    background-color: #0f172a !important;
                    color: #94a3b8 !important;
                    border: 1px solid #1e293b !important;
                }
                .stTabs [aria-selected="true"] {
                    background-color: #0284c7 !important;
                    color: white !important;
                    box-shadow: 0 4px 12px rgba(2, 132, 199, 0.4) !important;
                }
                h1, h2, h3, h4, h5, h6 {
                    color: #f8fafc !important;
                }
                </style>
            """, unsafe_allow_html=True)
            
    inject_theme(theme_choice)

    # Page Select
    page = st.sidebar.radio(
        "Dashboard Navigation Modules:",
        [
            "Overview & KPIs", 
            "NAV Tracker & Bollinger Bands", 
            "Advanced Analytics (Drawdowns & Returns)", 
            "SIP Trends & Flows", 
            "Scheme Rankings & Comparison", 
            "Portfolio Overlaps & Sectors", 
            "Wealth Growth Simulator",
            "Investor Demographics"
        ]
    )
    
    st.sidebar.divider()
    st.sidebar.markdown("### Advanced Search Filters")
    
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
        latest_aum_date = df_aum['date'].max()
        df_aum_latest = df_aum[df_aum['date'] == latest_aum_date]
        total_aum_cr = df_aum_latest['aum_crore'].sum()
        total_aum_lakh_cr = total_aum_cr / 100000
        
        latest_sip_row = df_sip.iloc[-1]
        latest_sip_inflow = latest_sip_row['sip_inflow_crore']
        active_sip_accounts = latest_sip_row['active_sip_accounts_crore']
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
        
        # PDF Generation & Download Functionality
        st.markdown("### Programmatic Report Export")
        c_exp1, c_exp2 = st.columns([1, 4])
        with c_exp1:
            # Build clean Performance table for PDF
            df_perf_table = df_perf_f[['scheme_name', 'category', 'return_3yr_pct', 'sharpe_ratio', 'aum_crore']].rename(columns={
                'scheme_name': 'Scheme Name',
                'category': 'Category',
                'return_3yr_pct': '3-Yr Return (%)',
                'sharpe_ratio': 'Sharpe Ratio',
                'aum_crore': 'AUM (Cr)'
            }).sort_values(by='Sharpe Ratio', ascending=False)
            
            pdf_bytes = generate_pdf_report(df_perf_table, total_aum_lakh_cr, latest_sip_inflow)
            
            if pdf_bytes:
                st.download_button(
                    label="📄 Export Executive Summary PDF",
                    data=pdf_bytes,
                    file_name="Bluestock_Executive_Analytics_Report.pdf",
                    mime="application/pdf"
                )
        st.divider()
        
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown("### Assets Under Management (AUM) Share by AMC")
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

    # --- PAGE 2: NAV TRACKER & BOLLINGER BANDS ---
    elif page == "NAV Tracker & Bollinger Bands":
        st.markdown("# NAV Price Tracker & Volatility Channel")
        st.markdown("Analyze daily NAV price trends, overlay Bollinger Bands (20-Day volatility channel), and project next 30 days price trend.")
        
        # Schemes Dropdown
        schemes = sorted(list(df_nav_f['scheme_name'].unique()))
        
        if not schemes:
            st.warning("No schemes found matching the selected global filters.")
        else:
            c_select, c_opts = st.columns([3, 1])
            with c_select:
                selected_scheme = st.selectbox("Select Scheme to Inspect:", schemes)
            with c_opts:
                enable_bb = st.checkbox("Overlay Bollinger Bands (20-Day)", value=True)
                enable_forecast = st.checkbox("Show 30-Day Predictive Trend", value=True)
                
            df_nav_scheme = df_nav_f[df_nav_f['scheme_name'] == selected_scheme].copy()
            df_nav_scheme['date'] = pd.to_datetime(df_nav_scheme['date'])
            df_nav_scheme = df_nav_scheme.sort_values(by='date').reset_index(drop=True)
            
            # Sub-filters: Date Slider
            min_date = df_nav_scheme['date'].min().date()
            max_date = df_nav_scheme['date'].max().date()
            selected_date_range = st.slider("Select Timeline Range:", min_value=min_date, max_value=max_date, value=(min_date, max_date))
            
            df_nav_filtered = df_nav_scheme[
                (df_nav_scheme['date'].dt.date >= selected_date_range[0]) & 
                (df_nav_scheme['date'].dt.date <= selected_date_range[1])
            ].copy()
            
            # Apply analytics
            df_bb = calculate_bollinger_bands(df_nav_filtered)
            df_hist, df_fc = forecast_nav_trend(df_nav_filtered)
            
            fig = go.Figure()
            
            # 1. Historical NAV Line
            fig.add_trace(
                go.Scatter(
                    x=df_bb['date'], y=df_bb['nav'],
                    name="Daily NAV",
                    line=dict(color="#1a73e8", width=2.5)
                )
            )
            
            # 2. Bollinger Bands
            if enable_bb:
                fig.add_trace(
                    go.Scatter(
                        x=df_bb['date'], y=df_bb['SMA'],
                        name="20-Day SMA",
                        line=dict(color="#e0a800", width=1.5, dash="dash")
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=df_bb['date'], y=df_bb['Upper_Band'],
                        name="Upper Volatility Band",
                        line=dict(color="rgba(26,115,232,0.2)", width=0),
                        showlegend=False
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=df_bb['date'], y=df_bb['Lower_Band'],
                        name="Bollinger Band (Volatility Channel)",
                        line=dict(color="rgba(26,115,232,0.2)", width=0),
                        fill='tonexty',
                        fillcolor='rgba(26,115,232,0.06)'
                    )
                )
                
            # 3. Forecast Line
            if enable_forecast:
                fig.add_trace(
                    go.Scatter(
                        x=df_fc['date'], y=df_fc['nav_forecast'],
                        name="Predictive NAV Forecast (30 Days)",
                        line=dict(color="#ea4335", width=2.5, dash="dot")
                    )
                )
                
            fig.update_layout(
                title=f"NAV Trend & Analytics for {selected_scheme}",
                xaxis_title="Date",
                yaxis_title="Net Asset Value (INR)",
                template="plotly_white",
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Downloadable CSV Data Table
            st.markdown("### Export Daily NAV Data")
            csv_df = df_bb[['date', 'nav', 'SMA', 'Upper_Band', 'Lower_Band']].rename(columns={
                'date': 'Date', 'nav': 'NAV Value', 'SMA': '20-Day SMA', 
                'Upper_Band': 'Upper Bollinger', 'Lower_Band': 'Lower Bollinger'
            })
            csv_data = csv_df.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                label="📥 Download NAV Analysis Table (CSV)",
                data=csv_data,
                file_name=f"{selected_scheme.replace(' ', '_')}_nav_data.csv",
                mime="text/csv"
            )

    # --- PAGE 3: ADVANCED ANALYTICS (DRAWDOWNS & RETURNS) ---
    elif page == "Advanced Analytics (Drawdowns & Returns)":
        st.markdown("# Advanced Financial Risk & Returns Analytics")
        st.markdown("Analyze rolling returns over multiple horizons and evaluate maximum historical peak-to-trough drawdowns.")
        
        schemes = sorted(list(df_nav_f['scheme_name'].unique()))
        
        if not schemes:
            st.warning("No schemes found matching the selected global filters.")
        else:
            selected_scheme = st.selectbox("Select Scheme for Drawdown & Returns Analysis:", schemes)
            
            df_nav_scheme = df_nav_f[df_nav_f['scheme_name'] == selected_scheme].copy()
            df_nav_scheme['date'] = pd.to_datetime(df_nav_scheme['date'])
            df_nav_scheme = df_nav_scheme.sort_values(by='date').reset_index(drop=True)
            
            # Apply Drawdowns and Rolling Returns
            df_dd = calculate_drawdowns(df_nav_scheme)
            df_rr = calculate_rolling_returns(df_nav_scheme, window=252)
            
            st.divider()
            
            c_dd, c_rr = st.columns(2)
            with c_dd:
                st.markdown("### Historical Drawdown Curve (%)")
                fig_dd = px.area(
                    df_dd,
                    x='date',
                    y='Drawdown_Pct',
                    labels={'Drawdown_Pct': 'Drawdown %', 'date': 'Date'},
                    color_discrete_sequence=['#ea4335']
                )
                fig_dd.update_layout(template="plotly_white", yaxis_title="Drawdown % (Drop from Peak)")
                st.plotly_chart(fig_dd, use_container_width=True)
                
                # Drawdown stats
                max_dd = df_dd['Drawdown_Pct'].min()
                max_rec = df_dd['Recovery_Days'].max()
                st.metric("Maximum Historical Drawdown", f"{max_dd:.2f}%", delta_color="inverse")
                st.metric("Worst Recovery Period", f"{max_rec} Days")
                
            with c_rr:
                st.markdown("### 1-Year Rolling Annualized Return (%)")
                fig_rr = px.line(
                    df_rr,
                    x='date',
                    y='Rolling_Return_Ann',
                    labels={'Rolling_Return_Ann': 'Return %', 'date': 'Date'},
                    color_discrete_sequence=['#34a853']
                )
                fig_rr.update_layout(template="plotly_white", yaxis_title="1-Year Rolling Return (Ann.)")
                st.plotly_chart(fig_rr, use_container_width=True)
                
                # Returns stats
                avg_rr = df_rr['Rolling_Return_Ann'].mean() * 100.0
                max_rr = df_rr['Rolling_Return_Ann'].max() * 100.0
                min_rr = df_rr['Rolling_Return_Ann'].min() * 100.0
                st.metric("Average Rolling Return", f"{avg_rr:.2f}%")
                st.metric("Max / Min Rolling Returns", f"{max_rr:.2f}% / {min_rr:.2f}%")
                
            # Download analysis data
            st.divider()
            df_export = df_dd.merge(df_rr[['date', 'Rolling_Return_Ann']], on='date', how='left')
            csv_data = df_export.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Risk/Returns Dataset (CSV)",
                data=csv_data,
                file_name=f"{selected_scheme.replace(' ', '_')}_risk_returns.csv",
                mime="text/csv"
            )

    # --- PAGE 4: SIP TRENDS & FLOWS ---
    elif page == "SIP Trends & Flows":
        st.markdown("# Industry-wide SIP Inflows & Category Flows")
        st.markdown("Track industry-wide monthly SIP inflows alongside portfolio folios growth.")
        
        fig_sip = plot_sip_inflows(df_sip)
        st.plotly_chart(fig_sip, use_container_width=True)

    # --- PAGE 5: SCHEME RANKINGS & COMPARISON ---
    elif page == "Scheme Rankings & Comparison":
        st.markdown("# Risk-Adjusted Scheme Rankings & Performance Comparison")
        st.markdown("Evaluate risk-adjusted performance across Sharpe, Sortino, Alpha, Beta, Volatility, and AUM scale.")
        
        # Display Rankings Table
        st.markdown("### Risk-Adjusted Scheme Rankings")
        df_rank = df_perf_f.copy()
        df_rank = df_rank.sort_values(by='sharpe_ratio', ascending=False).reset_index(drop=True)
        df_rank['sharpe_rank'] = df_rank.index + 1
        
        df_rank_table = df_rank[[
            'sharpe_rank', 'scheme_name', 'category', 'return_3yr_pct', 'std_dev_ann_pct', 
            'sharpe_ratio', 'alpha', 'beta', 'aum_crore'
        ]].rename(columns={
            'sharpe_rank': 'Rank',
            'scheme_name': 'Scheme Name',
            'category': 'Category',
            'return_3yr_pct': '3-Yr Return (%)',
            'std_dev_ann_pct': 'Volatility (%)',
            'sharpe_ratio': 'Sharpe Ratio',
            'alpha': 'Jensen Alpha',
            'beta': 'Market Beta',
            'aum_crore': 'AUM (Cr)'
        })
        st.dataframe(df_rank_table, use_container_width=True)
        
        csv_data = df_rank_table.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Rankings (CSV)",
            data=csv_data,
            file_name="bluestock_scheme_rankings.csv",
            mime="text/csv"
        )
        
        # Scheme Comparison Page
        st.divider()
        st.markdown("### Detailed Scheme Comparison")
        
        schemes = sorted(list(df_perf_f['scheme_name'].dropna().unique()))
        selected_comp = st.multiselect("Select Schemes to Compare (Max 5):", schemes, default=schemes[:3])
        
        if selected_comp:
            df_comp = df_perf_f[df_perf_f['scheme_name'].isin(selected_comp)]
            
            c_comp_tab, c_comp_ch = st.columns([1, 1])
            with c_comp_tab:
                comp_cols = ['scheme_name', 'category', 'return_3yr_pct', 'std_dev_ann_pct', 'sharpe_ratio', 'aum_crore']
                df_comp_show = df_comp[comp_cols].rename(columns={
                    'scheme_name': 'Scheme', 'category': 'Category', 
                    'return_3yr_pct': '3-Yr Return %', 'std_dev_ann_pct': 'Volatility %', 
                    'sharpe_ratio': 'Sharpe', 'aum_crore': 'AUM (Cr)'
                })
                st.dataframe(df_comp_show.reset_index(drop=True), use_container_width=True)
                
            with c_comp_ch:
                fig_comp = px.bar(
                    df_comp,
                    x='return_3yr_pct',
                    y='scheme_name',
                    color='sharpe_ratio',
                    title="3-Year Annualized Return vs Sharpe Ratio",
                    labels={'return_3yr_pct': 'Return %', 'scheme_name': 'Scheme', 'sharpe_ratio': 'Sharpe Ratio'},
                    color_continuous_scale="teal"
                )
                st.plotly_chart(fig_comp, use_container_width=True)

    # --- PAGE 6: PORTFOLIO OVERLAPS & SECTORS ---
    elif page == "Portfolio Overlaps & Sectors":
        st.markdown("# Portfolio Holdings Comparison & Sector Overlap Analysis")
        st.markdown("Compare the stock holdings and sector concentration of two mutual funds side-by-side to compute portfolio sector overlap.")
        
        schemes = sorted(list(df_port_f['scheme_name'].dropna().unique()))
        
        if len(schemes) < 2:
            st.warning("Please reset your global filters to allow at least 2 schemes for comparison.")
        else:
            col_a, col_b = st.columns(2)
            with col_a:
                scheme_a = st.selectbox("Select Scheme A:", schemes, index=0)
            with col_b:
                scheme_b = st.selectbox("Select Scheme B:", schemes, index=min(1, len(schemes)-1))
                
            df_port_a = df_port_f[df_port_f['scheme_name'] == scheme_a]
            df_port_b = df_port_f[df_port_f['scheme_name'] == scheme_b]
            
            # Calculate sector overlap percentage
            sect_a = df_port_a.groupby('sector')['weight_pct'].sum().reset_index(name='weight_A')
            sect_b = df_port_b.groupby('sector')['weight_pct'].sum().reset_index(name='weight_B')
            
            sect_merge = pd.merge(sect_a, sect_b, on='sector', how='outer').fillna(0)
            sect_merge['overlap'] = sect_merge[['weight_A', 'weight_B']].min(axis=1)
            total_overlap = sect_merge['overlap'].sum()
            
            st.markdown(f"<h3 style='text-align: center; color: #1a73e8;'>Portfolio Sector Overlap: {total_overlap:.2f}%</h3>", unsafe_allow_html=True)
            st.markdown("Overlap measures how correlated their sector exposures are. Higher overlap implies lesser diversification between the two funds.")
            
            st.divider()
            
            # Side by side bar charts for sector weightings
            c_sect_a, c_sect_b = st.columns(2)
            with c_sect_a:
                st.markdown(f"### {scheme_a} Sector Allocation")
                fig_sa = px.bar(sect_a, x='weight_pct', y='sector', orientation='h', color='weight_pct', color_continuous_scale="blues")
                fig_sa.update_layout(template="plotly_white", coloraxis_showscale=False)
                fig_sa.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_sa, use_container_width=True)
                
            with c_sect_b:
                st.markdown(f"### {scheme_b} Sector Allocation")
                fig_sb = px.bar(sect_b, x='weight_pct', y='sector', orientation='h', color='weight_pct', color_continuous_scale="purples")
                fig_sb.update_layout(template="plotly_white", coloraxis_showscale=False)
                fig_sb.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_sb, use_container_width=True)

    # --- PAGE 7: WEALTH GROWTH SIMULATOR ---
    elif page == "Wealth Growth Simulator":
        st.markdown("# Compounding Investment Wealth Simulator")
        st.markdown("Model the long-term compounding effects of regular Systematic Investment Plans (SIP) vs a one-off Lumpsum deposit.")
        
        sim_type = st.radio("Choose Simulator Type:", ["SIP (Monthly Investment)", "Lumpsum (One-off Investment)"])
        
        c_inputs, c_outputs = st.columns([1, 2])
        
        with c_inputs:
            st.markdown("### Input Investment Parameters")
            if sim_type == "SIP (Monthly Investment)":
                monthly_amt = st.number_input("Monthly Contribution (INR):", min_value=500, max_value=1000000, value=5000, step=500)
                expected_return = st.slider("Expected Annualized Yield (%):", min_value=1.0, max_value=30.0, value=12.0, step=0.5)
                horizon = st.slider("Investment Horizon (Years):", min_value=1, max_value=40, value=10)
                
                # Apply SIP simulator
                df_sim = calculate_sip_growth(monthly_amt, expected_return, horizon)
                
                total_invested = monthly_amt * horizon * 12
                maturity_val = df_sim['Future_Value'].iloc[-1]
                wealth_gain = maturity_val - total_invested
            else:
                lumpsum_amt = st.number_input("Initial Lumpsum Investment (INR):", min_value=5000, max_value=100000000, value=50000, step=5000)
                expected_return = st.slider("Expected Annualized Yield (%):", min_value=1.0, max_value=30.0, value=12.0, step=0.5)
                horizon = st.slider("Investment Horizon (Years):", min_value=1, max_value=40, value=10)
                
                # Apply Lumpsum simulator
                df_sim = calculate_lumpsum_growth(lumpsum_amt, expected_return, horizon)
                
                total_invested = lumpsum_amt
                maturity_val = df_sim['Future_Value'].iloc[-1]
                wealth_gain = maturity_val - total_invested
                
            # Display results metrics
            st.metric("Total Amount Invested", f"₹ {total_invested:,.2f}")
            st.metric("Estimated Maturity Value", f"₹ {maturity_val:,.2f}")
            st.metric("Estimated Wealth Gain", f"₹ {wealth_gain:,.2f}", delta=f"{wealth_gain/total_invested * 100:.1f}% Growth")
            
        with c_outputs:
            st.markdown("### Maturity Wealth Compounding Projection")
            fig_sim = go.Figure()
            fig_sim.add_trace(
                go.Scatter(
                    x=df_sim['Year'], y=df_sim['Future_Value'],
                    name="Estimated Maturity Value",
                    line=dict(color="#1a73e8", width=3)
                )
            )
            fig_sim.add_trace(
                go.Scatter(
                    x=df_sim['Year'], y=df_sim['Invested_Amount'],
                    name="Cumulative Principal Invested",
                    line=dict(color="#5f6368", width=1.5, dash="dash")
                )
            )
            fig_sim.update_layout(
                xaxis_title="Timeline (Years)",
                yaxis_title="Total Value (INR)",
                template="plotly_white",
                hovermode="x unified"
            )
            st.plotly_chart(fig_sim, use_container_width=True)
            
            # Download simulated dataset
            csv_data = df_sim.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Compounding Table (CSV)",
                data=csv_data,
                file_name="compounding_projection.csv",
                mime="text/csv"
            )

    # --- PAGE 8: INVESTOR DEMOGRAPHICS ---
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
        
        c3, c4 = st.columns(2)
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
