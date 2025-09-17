# -*- coding: utf-8 -*-
"""
Moduł Agentów Selekcyjnych ("Rewolucja AI").

Odpowiedzialność: Skanowanie rynku i selekcja spółek do "Dream Teamu"
na podstawie zdefiniowanych kryteriów (Płynność, Impuls, Zmienność),
zgodnie z dokumentacją projektową.
"""
import pandas as pd
import os
from typing import List, Dict, Optional
from data_fetcher import DataFetcher, transform_to_dataframe

# --- Logika Agenta Płynności ---
def check_liquidity(df: pd.DataFrame, period: int = 30, multiplier: float = 5.0) -> bool:
    """
    Sprawdza, czy w danym okresie wystąpił skok wolumenu.
    Logika "Łowcy Tłumu".
    """
    if df is None or 'volume' not in df.columns or len(df) < period:
        return False
    
    recent_data = df.tail(period)
    average_volume = recent_data['volume'].mean()
    
    # Sprawdź, czy jakikolwiek dzień miał wolumen X razy większy niż średnia
    if (recent_data['volume'] > average_volume * multiplier).any():
        return True
    return False

# --- Logika Agenta Impulsu ---
def check_momentum(ticker: str, fetcher: DataFetcher, latest_close_price: float) -> bool:
    """
    Sprawdza, czy cena jest powyżej 50-dniowej średniej kroczącej.
    Logika "Strażnika Trendu".
    """
    sma_data = fetcher.get_data({
        "function": "SMA",
        "symbol": ticker,
        "interval": "daily",
        "time_period": 50,
        "series_type": "close"
    })
    
    if sma_data and "Technical Analysis: SMA" in sma_data:
        try:
            latest_sma_value = float(next(iter(sma_data["Technical Analysis: SMA"].values()))["SMA"])
            return latest_close_price > latest_sma_value
        except (StopIteration, KeyError, ValueError):
            return False
    return False

# --- Logika Agenta Zmienności ---
def check_volatility(ticker: str, fetcher: DataFetcher, latest_close_price: float, min_volatility_pct: float = 4.0) -> bool:
    """
    Sprawdza, czy wskaźnik ATR wynosi co najmniej X% ceny.
    Logika "Poszukiwacza Energii".
    """
    atr_data = fetcher.get_data({
        "function": "ATR",
        "symbol": ticker,
        "interval": "daily",
        "time_period": 14 # Standardowy okres dla ATR
    })

    if atr_data and "Technical Analysis: ATR" in atr_data:
        try:
            latest_atr_value = float(next(iter(atr_data["Technical Analysis: ATR"].values()))["ATR"])
            volatility_pct = (latest_atr_value / latest_close_price) * 100
            return volatility_pct >= min_volatility_pct
        except (StopIteration, KeyError, ValueError):
            return False
    return False

# --- Główna funkcja orkiestrująca ---
def run_market_scan(tickers: List[str], fetcher: DataFetcher) -> Dict:
    """
    Uruchamia pełny proces skanowania rynku przez agentów selekcyjnych.
    """
    print(f"INFO: Agenci Selekcyjni rozpoczynają skanowanie {len(tickers)} spółek...")
    candidates = []
    
    for ticker in tickers:
        print(f"\n--- Analiza: {ticker} ---")
        
        # Krok 1: Pobierz podstawowe dane historyczne (wystarczy ~60 dni)
        historical_data_json = fetcher.get_data({
            "function": "TIME_SERIES_DAILY",
            "symbol": ticker,
            "outputsize": "compact" # "compact" zwraca ~100 punktów danych
        })
        
        df = transform_to_dataframe(historical_data_json)
        
        if df is None or df.empty:
            print(f"OSTRZEŻENIE: Nie udało się pobrać danych historycznych dla {ticker}. Pomijam.")
            continue
            
        latest_close_price = df['close'].iloc[-1]
        
        # Krok 2: Głosowanie agentów
        approvals = 0
        votes = {}
        
        # Głos Agenta Płynności
        votes['liquidity'] = check_liquidity(df)
        if votes['liquidity']:
            approvals += 1
        print(f"Agent Płynności: {'TAK' if votes['liquidity'] else 'NIE'}")

        # Głos Agenta Impulsu
        votes['momentum'] = check_momentum(ticker, fetcher, latest_close_price)
        if votes['momentum']:
            approvals += 1
        print(f"Agent Impulsu: {'TAK' if votes['momentum'] else 'NIE'}")

        # Głos Agenta Zmienności
        votes['volatility'] = check_volatility(ticker, fetcher, latest_close_price)
        if votes['volatility']:
            approvals += 1
        print(f"Agent Zmienności: {'TAK' if votes['volatility'] else 'NIE'}")

        # Krok 3: Werdykt
        if approvals >= 2:
            candidates.append(ticker)
            print(f"WERDYKT: {ticker} zostaje KANDYDATEM ({approvals}/3 głosy).")
        else:
            print(f"WERDYKT: {ticker} odrzucony ({approvals}/3 głosy).")
            
    print(f"\nINFO: Skanowanie zakończone. Wyłoniono {len(candidates)} kandydatów: {candidates}")
    return {
        "initial_count": len(tickers),
        "candidates_count": len(candidates),
        "candidates": candidates
    }

# Blok do testowania modułu
if __name__ == "__main__":
    API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not API_KEY:
        print("OSTRZEŻENIE: Brak klucza ALPHA_VANTAGE_API_KEY.")
        API_KEY = "TWOJ_KLUCZ_API"

    data_fetcher = DataFetcher(api_key=API_KEY)
    
    # Zróżnicowana lista spółek do testu
    test_tickers = ["TSLA", "JNJ", "AMD", "PLTR", "XOM", "BA"] 
    
    scan_results = run_market_scan(test_tickers, data_fetcher)
    
    import json
    print("\n--- Ostateczny wynik Rewolucji AI ---")
    print(json.dumps(scan_results, indent=2))
