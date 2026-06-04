import streamlit as st

def render_kpi_card(label: str, value: str, icon: str = "📊"):
    """
    Renders a styled glassmorphic KPI card with hover transition.
    
    Parameters:
    -----------
    label : str
        The metric description (e.g. 'Total AUM').
    value : str
        The string representation of the metric value (e.g. '₹ 12.5L Cr').
    icon : str
        An emoji or icon character.
    """
    card_html = f"""
    <div class="kpi-card">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
