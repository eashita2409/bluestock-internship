import pandas as pd
import numpy as np
from scipy import stats

def calculate_cagr(start_value: float, end_value: float, years: float) -> float:
    """
    Calculates the Compound Annual Growth Rate (CAGR).
    
    Formula:
    CAGR = (End Value / Start Value) ^ (1 / Years) - 1
    
    Parameters:
    -----------
    start_value : float
        The initial value of the investment.
    end_value : float
        The final value of the investment.
    years : float
        The duration of the investment in years.
    """
    if start_value <= 0 or end_value <= 0:
        raise ValueError("Start and end values must be positive numbers greater than 0.")
    if years <= 0:
        raise ValueError("Years must be a positive number greater than 0.")
        
    return (end_value / start_value) ** (1.0 / years) - 1.0


def calculate_annualized_return(returns: pd.Series, periods_per_year: int = 252) -> float:
    """
    Calculates the annualized return from a series of periodic returns.
    
    Formula (Geometric Mean):
    Annualized Return = (Product of (1 + Return_i)) ^ (periods_per_year / n) - 1
    
    Parameters:
    -----------
    returns : pd.Series
        A series of returns (e.g. daily return percentages in decimal form: 0.01 for 1%).
    periods_per_year : int
        Number of trading periods in a year. Defaults to 252 (standard stock market trading days).
        Use 12 for monthly returns, 52 for weekly returns.
    """
    clean_returns = returns.dropna()
    if clean_returns.empty:
        return 0.0
        
    n = len(clean_returns)
    # Compound returns: multiply all (1 + r) elements together
    compound_growth = np.prod(1.0 + clean_returns)
    
    return compound_growth ** (periods_per_year / n) - 1.0


def calculate_annualized_volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
    """
    Calculates the annualized volatility (standard deviation of returns).
    Volatility represents the risk or fluctuations of the fund's price.
    
    Formula:
    Volatility = Standard Deviation of Returns * Square Root of (periods_per_year)
    
    Parameters:
    -----------
    returns : pd.Series
        A series of periodic returns.
    periods_per_year : int
        Number of trading periods in a year. Defaults to 252.
    """
    clean_returns = returns.dropna()
    if len(clean_returns) < 2:
        return 0.0
        
    # Calculate standard deviation and multiply by sqrt of trading days to annualize
    return clean_returns.std() * np.sqrt(periods_per_year)


def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.05, periods_per_year: int = 252) -> float:
    """
    Calculates the annualized Sharpe Ratio.
    The Sharpe Ratio measures risk-adjusted return; higher values mean better return per unit of risk.
    
    Formula:
    Sharpe Ratio = (Annualized Return - Risk-Free Rate) / Annualized Volatility
    
    Parameters:
    -----------
    returns : pd.Series
        A series of periodic returns.
    risk_free_rate : float
        The annual risk-free rate of return (e.g. Govt bond yields). Defaults to 5% (0.05).
    periods_per_year : int
        Number of trading periods in a year. Defaults to 252.
    """
    ann_return = calculate_annualized_return(returns, periods_per_year)
    ann_vol = calculate_annualized_volatility(returns, periods_per_year)
    
    # Avoid division by zero if volatility is 0
    if ann_vol == 0.0:
        return 0.0
        
    return (ann_return - risk_free_rate) / ann_vol


def calculate_beta(fund_returns: pd.Series, market_returns: pd.Series) -> float:
    """
    Calculates the Beta coefficient of the fund relative to the market index.
    Beta measures how sensitive the fund is to market movements.
    - Beta = 1: Fund moves exactly with the market.
    - Beta > 1: Fund is more volatile than the market (higher risk/reward).
    - Beta < 1: Fund is less volatile than the market (defensive).
    
    Formula:
    Beta = Covariance(Fund Returns, Market Returns) / Variance(Market Returns)
    
    Parameters:
    -----------
    fund_returns : pd.Series
        Series of periodic returns for the mutual fund.
    market_returns : pd.Series
        Series of periodic returns for the market index (e.g., Nifty 50 or S&P 500).
    """
    # Align the returns to ensure we compare the same dates/indices
    df = pd.concat([fund_returns, market_returns], axis=1).dropna()
    if df.shape[0] < 2:
        return 1.0 # Default fallback
        
    fund_clean = df.iloc[:, 0]
    market_clean = df.iloc[:, 1]
    
    covariance = np.cov(fund_clean, market_clean)[0][1]
    market_variance = np.var(market_clean, ddof=1)
    
    if market_variance == 0.0:
        return 1.0
        
    return covariance / market_variance


def calculate_alpha(fund_returns: pd.Series, market_returns: pd.Series, risk_free_rate: float = 0.05, periods_per_year: int = 252) -> float:
    """
    Calculates the Jensen's Alpha.
    Alpha measures the fund's excess return relative to its expected return under the CAPM model.
    A positive alpha means the fund manager outperformed the market benchmark on a risk-adjusted basis.
    
    Formula:
    Expected Return (CAPM) = Risk-Free Rate + Beta * (Market Return - Risk-Free Rate)
    Alpha = Annualized Fund Return - Expected Return
    
    Parameters:
    -----------
    fund_returns : pd.Series
        Series of periodic returns for the mutual fund.
    market_returns : pd.Series
        Series of periodic returns for the market index.
    risk_free_rate : float
        The annual risk-free rate of return. Defaults to 5% (0.05).
    periods_per_year : int
        Number of trading periods in a year. Defaults to 252.
    """
    ann_fund_return = calculate_annualized_return(fund_returns, periods_per_year)
    ann_market_return = calculate_annualized_return(market_returns, periods_per_year)
    beta = calculate_beta(fund_returns, market_returns)
    
    # Jensen's Alpha Formula
    expected_return = risk_free_rate + beta * (ann_market_return - risk_free_rate)
    return ann_fund_return - expected_return
