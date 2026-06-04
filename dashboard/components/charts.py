import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Standard colors
COLOR_THEME = ["#1a73e8", "#34a853", "#fbbc05", "#ea4335", "#ab47bc", "#00acc1", "#ff7043"]

def plot_nav_tracker(df_nav: pd.DataFrame, selected_schemes: list):
    """Generates an interactive Plotly line chart of daily NAV over time."""
    if df_nav.empty or not selected_schemes:
        return go.Figure()
        
    df_filtered = df_nav[df_nav['scheme_name'].isin(selected_schemes)].copy()
    df_filtered['date'] = pd.to_datetime(df_filtered['date'])
    df_filtered = df_filtered.sort_values(by=['scheme_name', 'date'])
    
    fig = px.line(
        df_filtered, 
        x='date', 
        y='nav', 
        color='scheme_name',
        title="Net Asset Value (NAV) Tracker",
        labels={'date': 'Date', 'nav': 'Net Asset Value (INR)', 'scheme_name': 'Scheme'},
        color_discrete_sequence=COLOR_THEME
    )
    
    fig.update_layout(
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=80, b=40),
        hovermode="x unified"
    )
    return fig

def plot_sip_inflows(df_sip: pd.DataFrame):
    """Generates a dual-axis line and bar plot for monthly SIP inflows & active accounts."""
    if df_sip.empty:
        return go.Figure()
        
    fig = go.Figure()
    
    # Add active accounts as bars
    fig.add_trace(
        go.Bar(
            x=df_sip['month'],
            y=df_sip['active_sip_accounts_crore'],
            name="Active SIP Accounts (Cr)",
            yaxis="y2",
            marker_color="rgba(52, 168, 83, 0.4)",
            hovertemplate="%{y:.2f} Crore accounts"
        )
    )
    
    # Add inflow as a line
    fig.add_trace(
        go.Scatter(
            x=df_sip['month'],
            y=df_sip['sip_inflow_crore'],
            name="SIP Inflow (Cr)",
            yaxis="y1",
            mode="lines+markers",
            line=dict(color="#1a73e8", width=3),
            marker=dict(size=8),
            hovertemplate="₹%{y:,} Crore"
        )
    )
    
    fig.update_layout(
        title="Industry SIP Inflows & Active Accounts Trend",
        xaxis=dict(title="Month", tickangle=45),
        yaxis=dict(title="SIP Inflows (INR Crore)", titlefont=dict(color="#1a73e8"), tickfont=dict(color="#1a73e8")),
        yaxis2=dict(
            title="Active SIP Accounts (Crore)",
            titlefont=dict(color="#34a853"),
            tickfont=dict(color="#34a853"),
            overlaying="y",
            side="right"
        ),
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=80, b=40)
    )
    return fig

def plot_risk_return(df_perf: pd.DataFrame):
    """Generates an interactive risk (volatility) vs return scatter plot."""
    if df_perf.empty:
        return go.Figure()
        
    fig = px.scatter(
        df_perf,
        x='std_dev_ann_pct',
        y='return_3yr_pct',
        color='category',
        size='aum_crore',
        hover_name='scheme_name',
        hover_data=['sharpe_ratio', 'morningstar_rating', 'fund_house'],
        labels={
            'std_dev_ann_pct': 'Annual Volatility (Std Dev %)',
            'return_3yr_pct': '3-Year Annualized Return (%)',
            'category': 'Category',
            'aum_crore': 'AUM (INR Crore)'
        },
        title="Risk vs. Return Profiles (3-Year Horizon)",
        color_discrete_sequence=COLOR_THEME
    )
    
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=40, r=40, t=80, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def plot_sector_allocations(df_port: pd.DataFrame):
    """Generates a bar chart of stock sector allocations."""
    if df_port.empty:
        return go.Figure()
        
    df_grouped = df_port.groupby('sector')['weight_pct'].sum().sort_values(ascending=False).reset_index()
    
    fig = px.bar(
        df_grouped.head(10),
        x='weight_pct',
        y='sector',
        orientation='h',
        title="Dominant Sectors Allocation Across All Schemes",
        labels={'weight_pct': 'Cumulative Weight (%)', 'sector': 'Sector'},
        color='weight_pct',
        color_continuous_scale="blues"
    )
    
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=40, r=40, t=80, b=40),
        coloraxis_showscale=False
    )
    fig.update_yaxes(autorange="reversed")
    return fig

def plot_demographics(df_tx: pd.DataFrame, group_by_col: str):
    """Generates a transaction counts chart grouped by demographics."""
    if df_tx.empty:
        return go.Figure()
        
    df_grouped = df_tx.groupby(group_by_col).size().reset_index(name='count')
    
    fig = px.bar(
        df_grouped,
        x=group_by_col,
        y='count',
        title=f"Transactions Count by {group_by_col.replace('_', ' ').capitalize()}",
        labels={'count': 'Number of Transactions', group_by_col: group_by_col.replace('_', ' ').capitalize()},
        color='count',
        color_continuous_scale="purples"
    )
    
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=40, r=40, t=80, b=40),
        coloraxis_showscale=False
    )
    return fig

def plot_payment_modes(df_tx: pd.DataFrame):
    """Generates a donut chart of payment modes."""
    if df_tx.empty:
        return go.Figure()
        
    df_grouped = df_tx.groupby('payment_mode').size().reset_index(name='count')
    
    fig = px.pie(
        df_grouped,
        values='count',
        names='payment_mode',
        hole=0.4,
        title="Transaction Volumes by Payment Mode",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=40, r=40, t=80, b=40)
    )
    return fig
