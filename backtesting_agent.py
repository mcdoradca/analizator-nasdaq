# -*- coding: utf-8 -*-
"""
Moduł Silnika Backtestingu "Wehikuł Czasu".

Odpowiedzialność: Przeprowadzanie symulacji historycznych dla danej strategii
i spółki na podstawie rzeczywistych danych.
"""
import os
import pandas as pd
from data_fetcher import DataFetcher, transform_to_dataframe

def run_backtest_simulation(ticker: str, fetcher: DataFetcher, short_window: int = 10, long_window: int = 50):
    """
    Przeprowadza symulację strategii przecięcia średnich kroczących na danych historycznych.
    """
    print(f"INFO: Silnik 'Wehikuł Czasu' rozpoczyna symulację dla {ticker}...")

    # Krok 1: Pobierz pełne dane historyczne
    historical_data_json = fetcher.get_data({
        "function": "TIME_SERIES_DAILY",
        "symbol": ticker,
        "outputsize": "full"
    })
    
    df = transform_to_dataframe(historical_data_json)
    
    if df is None or len(df) < long_window:
        print(f"BŁĄD: Niewystarczająca ilość danych historycznych dla {ticker} do przeprowadzenia testu.")
        return {"ticker": ticker, "trade_count": 0, "total_pnl": 0.0, "error": "Insufficient data."}

    # Krok 2: Oblicz średnie kroczące
    df[f'SMA_{short_window}'] = df['close'].rolling(window=short_window, min_periods=1).mean()
    df[f'SMA_{long_window}'] = df['close'].rolling(window=long_window, min_periods=1).mean()
    
    # Usuń okres, w którym długoterminowa średnia nie jest jeszcze stabilna
    df_strategy = df.iloc[long_window:].copy()

    # Krok 3: Symulacja transakcji
    in_position = False
    buy_price = 0.0
    total_pnl = 0.0
    trade_count = 0

    for i in range(1, len(df_strategy)):
        # Sprawdź sygnał kupna: krótka średnia przecina długą od dołu
        if df_strategy[f'SMA_{short_window}'].iloc[i] > df_strategy[f'SMA_{long_window}'].iloc[i] and \
           df_strategy[f'SMA_{short_window}'].iloc[i-1] <= df_strategy[f'SMA_{long_window}'].iloc[i-1] and \
           not in_position:
            
            in_position = True
            buy_price = df_strategy['close'].iloc[i]
            # print(f"{df_strategy.index[i].date()}: KUPOWANIE po cenie {buy_price:.2f}")

        # Sprawdź sygnał sprzedaży: krótka średnia przecina długą od góry
        elif df_strategy[f'SMA_{short_window}'].iloc[i] < df_strategy[f'SMA_{long_window}'].iloc[i] and \
             df_strategy[f'SMA_{short_window}'].iloc[i-1] >= df_strategy[f'SMA_{long_window}'].iloc[i-1] and \
             in_position:

            in_position = False
            sell_price = df_strategy['close'].iloc[i]
            pnl = sell_price - buy_price
            total_pnl += pnl
            trade_count += 1
            # print(f"{df_strategy.index[i].date()}: SPRZEDAŻ po cenie {sell_price:.2f}, P/L: {pnl:.2f}")

    print(f"INFO: Symulacja zakończona. Wynik P/L: {total_pnl:.2f}, Liczba transakcji: {trade_count}")
    return {
        "ticker": ticker,
        "trade_count": trade_count,
        "total_pnl": total_pnl
    }

# Blok do testowania modułu
if __name__ == "__main__":
    API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not API_KEY:
        print("OSTRZEŻENIE: Brak klucza ALPHA_VANTAGE_API_KEY.")
        API_KEY = "TWOJ_KLUCZ_API"
        
    data_fetcher = DataFetcher(api_key=API_KEY)
    
    # Przykładowy test dla spółki o wyraźnych trendach
    test_ticker = "TSLA" 
    
    backtest_results = run_backtest_simulation(test_ticker, data_fetcher)
    
    import json
    print(f"\n--- Ostateczny wynik symulacji dla {test_ticker} ---")
    print(json.dumps(backtest_results, indent=2))
