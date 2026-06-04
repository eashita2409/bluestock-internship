import numpy as np
import pandas as pd
import pytest
from src.analytics import (
    calculate_cagr,
    calculate_annualized_return,
    calculate_annualized_volatility,
    calculate_sharpe_ratio,
    calculate_beta,
    calculate_alpha
)

def test_calculate_cagr():
    # An investment growing from 100 to 121 in 2 years has a CAGR of 10%
    assert pytest.approx(calculate_cagr(100.0, 121.0, 2.0)) == 0.10
    
    # Check error handling
    with pytest.raises(ValueError):
        calculate_cagr(0.0, 121.0, 2.0)
    with pytest.raises(ValueError):
        calculate_cagr(100.0, -10.0, 2.0)
    with pytest.raises(ValueError):
        calculate_cagr(100.0, 120.0, 0.0)


def test_calculate_annualized_return():
    # If returns are constantly 0, annualized return should be 0
    returns = pd.Series([0.0] * 252)
    assert pytest.approx(calculate_annualized_return(returns, 252)) == 0.0
    
    # If returns are empty
    empty_returns = pd.Series([])
    assert calculate_annualized_return(empty_returns, 252) == 0.0


def test_calculate_annualized_volatility():
    # Series with constant returns has 0 volatility
    returns = pd.Series([0.01] * 10)
    assert pytest.approx(calculate_annualized_volatility(returns, 252)) == 0.0
    
    # Volatility of a single element or empty series should return 0.0
    assert pytest.approx(calculate_annualized_volatility(pd.Series([0.01]), 252)) == 0.0


def test_calculate_sharpe_ratio():
    # If returns are constantly equal to risk free rate, Sharpe ratio should be 0
    # Note: since volatility is 0, we expect our function to return 0.0 to avoid division by zero
    returns = pd.Series([0.05 / 252] * 252)
    assert calculate_sharpe_ratio(returns, risk_free_rate=0.05, periods_per_year=252) == 0.0


def test_calculate_beta():
    # Fund returns identical to market returns should have Beta = 1.0
    market_returns = pd.Series([0.01, -0.02, 0.015, 0.005, -0.01])
    fund_returns = market_returns.copy()
    assert pytest.approx(calculate_beta(fund_returns, market_returns)) == 1.0
    
    # Fund returns double the market returns should have Beta = 2.0
    fund_double = market_returns * 2.0
    assert pytest.approx(calculate_beta(fund_double, market_returns)) == 2.0


def test_calculate_alpha():
    # If fund returns match CAPM expectations exactly, alpha should be 0
    # Expected Return = Rf + Beta * (Rm - Rf)
    # Rf = 0.05, Beta = 1.0. Let's make Market return 10%. Fund return 10%. Alpha = 10% - (5% + 1*(10% - 5%)) = 0
    market_returns = pd.Series([0.10 / 252] * 252)
    fund_returns = pd.Series([0.10 / 252] * 252)
    alpha = calculate_alpha(fund_returns, market_returns, risk_free_rate=0.05, periods_per_year=252)
    assert pytest.approx(alpha, abs=1e-5) == 0.0
