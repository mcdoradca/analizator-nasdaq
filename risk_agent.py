"""
Moduł Agenta Ryzyka "Cerber".

Odpowiedzialność: Analiza ryzyka portfela (korelacja) oraz
ocena ryzyka pojedynczej spółki (Beta, korelacja z rynkiem).
"""
from typing import Dict, Optional
import pandas as pd
from itertools import combinations

def calculate_returns_correlation(data_a: pd.DataFrame, data_b: pd.DataFrame) -> Optional[float]:
    """
    Oblicza korelację Pearsona dla dziennych stóp zwrotu dwóch serii danych.
    """
    if data_a is None or data_b is None or 'close' not in data_a.columns or 'close' not in data_b.columns:
        return None

    merged_data = pd.merge(data_a['close'], data_b['close'], left_index=True, right_index=True, how='inner', suffixes=('_a', '_b'))
    if len(merged_data) < 20: # Wymagamy minimum 20 punktów danych
        return None

    returns = merged_data.pct_change().dropna()
    if len(returns) < 2:
        return None

    return returns.iloc[:, 0].corr(returns.iloc[:, 1])

def analyze_portfolio_risk_for_frontend(portfolio_data: Dict[str, pd.DataFrame]) -> Dict:
    """
    Analizuje ryzyko korelacji całego portfela.
    Wynik jest zgodny z oczekiwaniami frontendu.
    """
    tickers = list(portfolio_data.keys())
    if len(tickers) < 2:
        return {"correlation": 0.0, "level": "Brak Danych", "summary": "Portfel musi zawierać min. 2 aktywa.", "color": "text-gray-400"}

    all_correlations = [c for c in (calculate_returns_correlation(portfolio_data.get(t_a), portfolio_data.get(t_b)) for t_a, t_b in combinations(tickers, 2)) if c is not None]
    
    if not all_correlations:
        return {"correlation": 0.0, "level": "Błąd Obliczeń", "summary": "Nie można obliczyć korelacji.", "color": "text-red-500"}

    avg_corr = sum(all_correlations) / len(all_correlations)
    
    level, color, summary = "Niski", "text-green-400", "Portfel jest dobrze zdywersyfikowany."
    if avg_corr > 0.7:
        level, color, summary = "Bardzo Wysoki", "text-red-500", "Ryzyko koncentracji jest bardzo wysokie!"
    elif avg_corr > 0.5:
        level, color, summary = "Wysoki", "text-yellow-500", "Podwyższone ryzyko koncentracji."
    elif avg_corr > 0.3:
        level, color = "Umiarkowany", "text-blue-400"

    return {"correlation": avg_corr, "level": level, "summary": summary, "color": color}

def analyze_single_stock_risk(stock_df: pd.DataFrame, market_df: pd.DataFrame, overview_data: Dict) -> Optional[Dict]:
    """
    NOWA FUNKCJA: Analizuje ryzyko pojedynczej spółki.
    """
    if stock_df is None or market_df is None or overview_data is None:
        return None

    beta = overview_data.get('Beta', 'N/A')
    correlation = calculate_returns_correlation(stock_df, market_df)

    risk_level, risk_color = 'N/A', 'text-gray-400'
    if beta != 'N/A' and correlation is not None:
        beta_f = float(beta)
        risk_score = 0
        if beta_f > 1.8: risk_score += 2
        elif beta_f > 1.2: risk_score += 1
        
        if correlation > 0.8: risk_score += 1

        if risk_score >= 2:
            risk_level, risk_color = 'Wysokie', 'text-red-400'
        elif risk_score >= 1:
            risk_level, risk_color = 'Umiarkowane', 'text-yellow-400'
        else:
            risk_level, risk_color = 'Niskie', 'text-green-400'

    return {
        "beta": beta,
        "correlation": f"{correlation:.2f}" if correlation is not None else "N/A",
        "riskLevel": risk_level,
        "riskColor": risk_color
    }

