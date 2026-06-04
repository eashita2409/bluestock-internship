import sys
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

def calculate_sip_growth(monthly_investment: float, expected_return_annual: float, years: int):
    """
    Simulates monthly SIP growth over time using monthly compounding.
    
    Formula:
    FV = PMT * [((1 + i)^n - 1) / i] * (1 + i)
    where PMT = monthly payment, i = monthly return rate (r/12), n = total months (years * 12)
    """
    monthly_rate = (expected_return_annual / 100.0) / 12.0
    total_months = years * 12
    
    months = np.arange(1, total_months + 1)
    invested = monthly_investment * months
    
    # Calculate future value for each month
    if monthly_rate == 0:
        future_value = invested
    else:
        future_value = monthly_investment * (((1 + monthly_rate)**months - 1) / monthly_rate) * (1 + monthly_rate)
        
    df = pd.DataFrame({
        'Month': months,
        'Year': months / 12.0,
        'Invested_Amount': invested,
        'Future_Value': future_value,
        'Wealth_Gain': future_value - invested
    })
    return df

def calculate_lumpsum_growth(initial_investment: float, expected_return_annual: float, years: int):
    """
    Simulates Lumpsum growth over time using annual compounding.
    
    Formula:
    FV = PV * (1 + r)^t
    """
    months = np.arange(1, (years * 12) + 1)
    monthly_rate = (expected_return_annual / 100.0) / 12.0
    
    invested = np.full_like(months, initial_investment, dtype=float)
    future_value = initial_investment * (1 + monthly_rate)**months
    
    df = pd.DataFrame({
        'Month': months,
        'Year': months / 12.0,
        'Invested_Amount': invested,
        'Future_Value': future_value,
        'Wealth_Gain': future_value - invested
    })
    return df

def calculate_bollinger_bands(df_nav_scheme: pd.DataFrame, window: int = 20, num_std: float = 2.0):
    """
    Calculates 20-day Simple Moving Average (SMA) and Bollinger Bands.
    """
    df = df_nav_scheme.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by='date').reset_index(drop=True)
    
    df['SMA'] = df['nav'].rolling(window=window).mean()
    df['rolling_std'] = df['nav'].rolling(window=window).std()
    
    df['Upper_Band'] = df['SMA'] + (num_std * df['rolling_std'])
    df['Lower_Band'] = df['SMA'] - (num_std * df['rolling_std'])
    
    return df

def calculate_drawdowns(df_nav_scheme: pd.DataFrame):
    """
    Calculates drawdown percentage from historical peak NAV.
    
    Formula:
    Drawdown = (NAV_t - Peak_t) / Peak_t
    """
    df = df_nav_scheme.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by='date').reset_index(drop=True)
    
    df['Peak'] = df['nav'].cummax()
    df['Drawdown_Pct'] = (df['nav'] - df['Peak']) / df['Peak'] * 100.0
    
    # Calculate recovery periods
    # A recovery happens when Drawdown_Pct returns to 0
    recovery_times = []
    current_peak_date = None
    
    for idx, row in df.iterrows():
        if row['nav'] >= row['Peak']:
            current_peak_date = row['date']
            recovery_times.append(0)
        else:
            if current_peak_date:
                days = (row['date'] - current_peak_date).days
                recovery_times.append(days)
            else:
                recovery_times.append(0)
                
    df['Recovery_Days'] = recovery_times
    return df

def calculate_rolling_returns(df_nav_scheme: pd.DataFrame, window: int = 252):
    """
    Calculates rolling annualized returns.
    
    Formula:
    Rolling Return = (NAV_t / NAV_{t-window})^(252/window) - 1
    """
    df = df_nav_scheme.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by='date').reset_index(drop=True)
    
    # Simple percentage change over the window size
    df['Rolling_Return'] = df['nav'].pct_change(periods=window)
    # Annualized rolling returns
    df['Rolling_Return_Ann'] = (df['nav'] / df['nav'].shift(window)) ** (252.0 / window) - 1.0
    
    return df

def forecast_nav_trend(df_nav_scheme: pd.DataFrame, forecast_days: int = 30):
    """
    Forecasts future NAV values for the next N days using a polynomial curve fit.
    """
    df = df_nav_scheme.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by='date').reset_index(drop=True)
    
    # Represent dates as numeric indexes for fitting (days from start)
    start_date = df['date'].min()
    df['days_from_start'] = (df['date'] - start_date).dt.days
    
    x = df['days_from_start'].values
    y = df['nav'].values
    
    # Fit a degree 2 polynomial curve
    poly_coeffs = np.polyfit(x, y, 2)
    poly_fit = np.poly1d(poly_coeffs)
    
    # Forecast future days
    last_day = x[-1]
    future_x = np.arange(last_day + 1, last_day + forecast_days + 1)
    
    # Generate future dates
    future_dates = pd.date_range(start=df['date'].max() + pd.Timedelta(days=1), periods=forecast_days)
    
    # Predict future NAV values
    future_nav = poly_fit(future_x)
    
    # Ensure NAV doesn't drop below a minimum threshold
    min_nav_historical = df['nav'].min()
    future_nav = np.clip(future_nav, min_nav_historical * 0.5, None)
    
    df_forecast = pd.DataFrame({
        'date': future_dates,
        'nav_forecast': future_nav
    })
    
    return df, df_forecast

def run_test_analytics():
    db_path = project_root / "data" / "db" / "mutual_fund_analytics.db"
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
        
    conn = sqlite3.connect(str(db_path))
    print("Successfully connected to SQLite for verification.")
    
    # Verify by loading one scheme
    df_nav_sample = pd.read_sql_query(
        "SELECT date, nav FROM fact_nav WHERE amfi_code = 119551 ORDER BY date;", conn
    )
    
    if not df_nav_sample.empty:
        print(f"Loaded {len(df_nav_sample)} daily records for AMFI 119551.")
        
        # 1. Bollinger Bands
        df_bb = calculate_bollinger_bands(df_nav_sample)
        print("Bollinger Bands calculated successfully.")
        
        # 2. Drawdowns
        df_dd = calculate_drawdowns(df_nav_sample)
        max_dd = df_dd['Drawdown_Pct'].min()
        print(f"Drawdowns calculated successfully. Max Drawdown: {max_dd:.2f}%")
        
        # 3. Rolling Returns
        df_rr = calculate_rolling_returns(df_nav_sample)
        print("Rolling returns calculated successfully.")
        
        # 4. Forecast
        df_hist, df_fc = forecast_nav_trend(df_nav_sample)
        print(f"NAV Trend forecasted successfully for the next {len(df_fc)} days.")
        
    conn.close()

if __name__ == "__main__":
    run_test_analytics()
