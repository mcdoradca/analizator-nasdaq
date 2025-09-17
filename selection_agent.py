# src/analysis/selection_agent.py
"""
Moduł Agentów Selekcyjnych ("Rewolucja AI").
Odpowiedzialność: Skanowanie rynku i selekcja spółek do "Dream Teamu".
"""
import numpy as np
from typing import List, Dict, Any
from src.data_fetcher import data_fetcher

def _calculate_sma(data: Dict[str, Any], period: int) -> float:
    """Oblicza prostą średnią kroczącą z danych."""
    if not data or "Time Series (Daily)" not in data:
        return 0.0
    
    time_series = data["Time Series (Daily)"]
    closes = [float(day["4. close"]) for day in time_series.values()]
    if len(closes) < period:
        return 0.0
    return sum(closes[:period]) / period

def _calculate_atr(data: Dict[str, Any], period: int = 14) -> float:
    """Oblicza Average True Range (ATR) - wskaźnik zmienności."""
    if not data or "Time Series (Daily)" not in data:
        return 0.0
    
    time_series = data["Time Series (Daily)"]
    daily_data = list(time_series.values())[:period]
    
    true_ranges = []
    for i in range(len(daily_data)):
        current = daily_data[i]
        high, low, close = float(current["2. high"]), float(current["3. low"]), float(current["4. close"])
        
        if i == 0:
            tr = high - low
        else:
            prev_close = float(daily_data[i-1]["4. close"])
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        
        true_ranges.append(tr)
    
    return sum(true_ranges) / len(true_ranges) if true_ranges else 0.0

def run_market_scan(tickers: List[str]) -> Dict[str, Any]:
    """
    Przeprowadza prawdziwe skanowanie rynku przez Agentów Selekcyjnych.
    """
    print(f"INFO: Agenci Selekcyjni rozpoczynają skanowanie {len(tickers)} spółek...")
    candidates = []

    for ticker in tickers:
        print(f"INFO: Analizowanie {ticker}...")
        
        # 1. Pobierz dane niezbędne do analizy
        daily_data = data_fetcher.get_data({"function": "TIME_SERIES_DAILY", "symbol": ticker, "outputsize": "compact"}) if data_fetcher else None
        
        if not daily_data or "Time Series (Daily)" not in daily_data:
            print(f"WARNING: Pominięto {ticker} - brak danych")
            continue

        # 2. Kryterium 1: Agent Płynności (Wolumen > 5x średnia)
        time_series = daily_data["Time Series (Daily)"]
        volumes = [float(day["5. volume"]) for day in time_series.values()]
        
        if len(volumes) < 30:
            print(f"WARNING: Pominięto {ticker} - za mało danych historycznych")
            continue

        avg_volume = sum(volumes[1:30]) / 29  # Średnia z ostatnich 29 dni
        latest_volume = volumes[0]

        if latest_volume < 5 * avg_volume:
            print(f"INFO: Odrzucono {ticker} - wolumen zbyt niski ({latest_volume:.0f} < 5*{avg_volume:.0f})")
            continue

        # 3. Kryterium 2: Agent Impulsu (Cena > SMA50)
        sma50 = _calculate_sma(daily_data, 50)
        latest_close = float(list(time_series.values())[0]["4. close"])
        
        if latest_close <= sma50 or sma50 == 0:
            print(f"INFO: Odrzucono {ticker} - cena ({latest_close:.2f}) <= SMA50 ({sma50:.2f})")
            continue

        # 4. Kryterium 3: Agent Zmienności (ATR > 4% ceny)
        atr_value = _calculate_atr(daily_data)
        atr_percentage = (atr_value / latest_close) * 100 if latest_close > 0 else 0
        
        if atr_percentage < 4.0:
            print(f"INFO: Odrzucono {ticker} - zmienność zbyt niska ({atr_percentage:.2f}% < 4%)")
            continue

        # 5. Wszystkie kryteria spełnione - dodaj do kandydatów
        print(f"SUCCESS: Dodano {ticker} do kandydatów (Wolumen: {latest_volume:.0f}, Cena: {latest_close:.2f}, Zmienność: {atr_percentage:.2f}%)")
        candidates.append(ticker)

    print(f"INFO: Skanowanie zakończone. Wyłoniono {len(candidates)} kandydatów: {candidates}")
    return {
        "initial_count": len(tickers),
        "candidates_count": len(candidates),
        "candidates": candidates
    }
