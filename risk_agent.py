# -*- coding: utf-8 -*-
"""
Moduł Agenta Ryzyka "Cerber".

Odpowiedzialność: Analiza ryzyka portfela, w szczególności korelacji
między aktywami, aby zapobiegać nadmiernej koncentracji.
"""

from typing import Dict, Optional
import pandas as pd
from itertools import combinations
import os

# Importy do testowania modułu w izolacji
from data_fetcher import DataFetcher, transform_to_dataframe

def calculate_returns_correlation(data_a: pd.DataFrame, data_b: pd.DataFrame) -> Optional[float]:
    """
    Oblicza korelację Pearsona dla dziennych stóp zwrotu dwóch serii danych.
    Funkcja została dostosowana do nowej struktury DataFrame z data_fetcher.

    Args:
        data_a (pd.DataFrame): DataFrame z danymi historycznymi dla pierwszej spółki.
        data_b (pd.DataFrame): DataFrame z danymi historycznymi dla drugiej spółki.

    Returns:
        Optional[float]: Współczynnik korelacji lub None w przypadku błędu.
    """
    if data_a is None or data_b is None or 'close' not in data_a.columns or 'close' not in data_b.columns:
        return None

    # Używamy indeksu (daty) do połączenia danych
    merged_data = pd.merge(data_a['close'], data_b['close'], left_index=True, right_index=True, how='inner', suffixes=('_a', '_b'))

    if len(merged_data) < 2:
        # Potrzebujemy co najmniej dwóch punktów danych do obliczenia korelacji
        return None

    # Oblicz dzienne stopy zwrotu
    returns = merged_data.pct_change().dropna()

    if returns.empty:
        return None

    # Oblicz korelację
    correlation = returns.iloc[:, 0].corr(returns.iloc[:, 1])
    return correlation

def analyze_portfolio_risk(portfolio_data: Dict[str, pd.DataFrame]) -> Dict:
    """
    Analizuje ryzyko portfela pod kątem korelacji między aktywami.
    Implementacja logiki Agenta "Cerber". Wynik jest zgodny z oczekiwaniami frontendu.

    Args:
        portfolio_data (Dict[str, pd.DataFrame]): Słownik, gdzie klucze to tickery,
                                                  a wartości to DataFrame'y z ich danymi.

    Returns:
        Dict: Słownik zawierający analizę ryzyka w formacie dla UI.
    """
    print("INFO: Agent 'Cerber' analizuje ryzyko korelacji portfela...")
    tickers = list(portfolio_data.keys())
    warnings = []

    if len(tickers) < 2:
        return {
            "correlation": 0.0,
            "level": "Brak Danych",
            "summary": "Portfel musi zawierać co najmniej 2 aktywa do analizy korelacji.",
            "color": "text-gray-400"
        }

    all_correlations = []
    ticker_pairs = combinations(tickers, 2)

    for ticker_a, ticker_b in ticker_pairs:
        data_a = portfolio_data.get(ticker_a)
        data_b = portfolio_data.get(ticker_b)

        correlation = calculate_returns_correlation(data_a, data_b)
        if correlation is not None:
            all_correlations.append(correlation)
            if correlation > 0.8:
                warnings.append(f"Wysoka korelacja ({correlation:.2f}) między {ticker_a} a {ticker_b}.")

    if not all_correlations:
         return {
            "correlation": 0.0,
            "level": "Błąd Obliczeń",
            "summary": "Nie można było obliczyć korelacji dla żadnej pary aktywów.",
            "color": "text-red-500"
        }

    average_correlation = sum(all_correlations) / len(all_correlations)
    summary = " ".join(warnings) if warnings else "Poziom korelacji w normie. Portfel jest dobrze zdywersyfikowany."

    level = "Niski"
    color = "text-green-400"
    if average_correlation > 0.7:
        level = "Bardzo Wysoki"
        color = "text-red-500"
        summary = "Ryzyko koncentracji jest bardzo wysokie! Spółki w portfelu poruszają się niemal identycznie. " + summary
    elif average_correlation > 0.5:
        level = "Wysoki"
        color = "text-yellow-500"
        summary = "Podwyższone ryzyko koncentracji. Rozważ dywersyfikację. " + summary
    elif average_correlation > 0.3:
        level = "Umiarkowany"
        color = "text-blue-400"

    return {
        "correlation": average_correlation,
        "level": level,
        "summary": summary,
        "color": color
    }

# Testowanie modułu po naprawie
if __name__ == "__main__":
    API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not API_KEY:
        print("OSTRZEŻENIE: Brak klucza ALPHA_VANTAGE_API_KEY. Testy mogą się nie powść.")
        API_KEY = "TWOJ_KLUCZ_API"

    fetcher = DataFetcher(api_key=API_KEY)

    # Przykładowy portfel do testów
    test_portfolio_tickers = ["AAPL", "GOOGL", "MSFT"] # Technologiczne, spodziewana wysoka korelacja
    # test_portfolio_tickers = ["AAPL", "JNJ", "XOM"] # Różne sektory, spodziewana niska korelacja
    
    portfolio_dfs = {}
    print(f"\n--- Test Agenta 'Cerber' dla portfela: {test_portfolio_tickers} ---")
    for ticker in test_portfolio_tickers:
        print(f"Pobieranie danych dla {ticker}...")
        json_data = fetcher.get_data({"function": "TIME_SERIES_DAILY", "symbol": ticker, "outputsize": "compact"})
        if json_data:
            df = transform_to_dataframe(json_data)
            if df is not None:
                portfolio_dfs[ticker] = df

    if len(portfolio_dfs) == len(test_portfolio_tickers):
        print("\nPobrano wszystkie dane. Uruchamianie analizy ryzyka...")
        risk_analysis = analyze_portfolio_risk(portfolio_dfs)
        import json
        print("\nWynik analizy 'Cerbera':")
        print(json.dumps(risk_analysis, indent=2, ensure_ascii=False))
    else:
        print("\nNie udało się pobrać danych dla wszystkich spółek. Analiza przerwana.")
