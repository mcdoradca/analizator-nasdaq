
"""
Nowy Agent Ryzyka "Cerber"
Analizuje ryzyko portfela pod kątem korelacji między aktywami.
"""
from typing import Dict, List, Tuple
import pandas as pd
from itertools import combinations
from src.data_fetcher import data_fetcher

def fetch_historical_data(ticker: str, days: int = 100) -> pd.DataFrame:
    """Pobiera dane historyczne dla pojedynczego tickera."""
    if not data_fetcher:
        return pd.DataFrame()
    
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": ticker,
        "outputsize": "compact"
    }
    
    data = data_fetcher.get_data(params)
    if not data or "Time Series (Daily)" not in data:
        print(f"WARNING: Nie udało się pobrać danych dla {ticker}")
        return pd.DataFrame()
    
    time_series = data["Time Series (Daily)"]
    df = pd.DataFrame.from_dict(time_series, orient='index', dtype=float)
    df.columns = ['open', 'high', 'low', 'close', 'volume']
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    
    return df.tail(days)

def calculate_returns_correlation(data_a: pd.DataFrame, data_b: pd.DataFrame) -> float:
    """
    Oblicza korelację Pearsona dla dziennych stóp zwrotu dwóch serii danych.
    """
    if data_a.empty or data_b.empty:
        return 0.0
    
    # Dopasuj daty
    merged_data = pd.merge(data_a['close'], data_b['close'], 
                          left_index=True, right_index=True, 
                          how='inner', suffixes=('_a', '_b'))
    
    if len(merged_data) < 5:  # Minimum 5 punktów danych
        return 0.0
    
    # Oblicz dzienne stopy zwrotu
    returns = merged_data.pct_change().dropna()
    
    # Oblicz korelację
    correlation = returns.iloc[:, 0].corr(returns.iloc[:, 1])
    return correlation if not pd.isna(correlation) else 0.0

def analyze_portfolio_risk(tickers: List[str]) -> Dict[str, Any]:
    """
    Analizuje ryzyko portfela pod kątem korelacji między aktywami.
    """
    print(f"INFO: Agent 'Cerber' analizuje ryzyko portfela: {tickers}")
    
    if len(tickers) < 2:
        return {
            "average_correlation": 0.0,
            "correlation_level": "Brak Danych",
            "color": "text-gray-400",
            "summary": "Portfel musi zawierać co najmniej 2 aktywa do analizy korelacji.",
            "warnings": []
        }

    # Pobierz dane historyczne dla wszystkich tickerów
    portfolio_data = {}
    for ticker in tickers:
        df = fetch_historical_data(ticker)
        if not df.empty:
            portfolio_data[ticker] = df
        else:
            print(f"WARNING: Pominięto {ticker} w analizie ryzyka - brak danych")

    if len(portfolio_data) < 2:
        return {
            "average_correlation": 0.0,
            "correlation_level": "Brak Danych",
            "color": "text-gray-400",
            "summary": "Niewystarczająca ilość danych do analizy korelacji.",
            "warnings": []
        }

    all_correlations = []
    warnings = []

    # Analizuj wszystkie pary
    for (ticker_a, data_a), (ticker_b, data_b) in combinations(portfolio_data.items(), 2):
        correlation = calculate_returns_correlation(data_a, data_b)
        all_correlations.append(correlation)

        if correlation > 0.8:
            warnings.append(f"Wysoka korelacja ({correlation:.2f}) między {ticker_a} a {ticker_b}. Ryzyko koncentracji.")
        elif correlation < -0.6:
            warnings.append(f"Silna korelacja ujemna ({correlation:.2f}) między {ticker_a} a {ticker_b}. Może zapewniać dywersyfikację.")

    average_correlation = sum(all_correlations) / len(all_correlations) if all_correlations else 0.0

    # Określ poziom ryzyka
    if average_correlation > 0.7:
        level, color = "Bardzo Wysoki", "text-red-400"
    elif average_correlation > 0.5:
        level, color = "Wysoki", "text-orange-400"
    elif average_correlation > 0.3:
        level, color = "Umiarkowany", "text-yellow-400"
    elif average_correlation > -0.3:
        level, color = "Niski", "text-green-400"
    else:
        level, color = "Ujemny (Dywersyfikacja)", "text-blue-400"

    summary = f"Średnia korelacja portfela: {average_correlation:.2f}. {level} poziom korelacji."
    
    if average_correlation > 0.6:
        summary += " Zalecana dywersyfikacja portfela."
    elif average_correlation < -0.4:
        summary += " Portfel dobrze zdywersyfikowany."

    print(f"INFO: Analiza ryzyka zakończona. Średnia korelacja: {average_correlation:.2f}")
    
    return {
        "average_correlation": round(average_correlation, 2),
        "correlation_level": level,
        "color": color,
        "summary": summary,
        "warnings": warnings
    }
