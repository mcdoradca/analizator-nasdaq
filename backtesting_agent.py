
"""
Moduł Silnika Backtestingu "Wehikuł Czasu".
Odpowiedzialność: Przeprowadzanie symulacji historycznych.
"""
import pandas as pd
from typing import Dict, Any
from src.data_fetcher import data_fetcher

def run_backtest_simulation(ticker: str) -> Dict[str, Any]:
    """
    Przeprowadza backtest na rzeczywistych danych historycznych.
    Prosta strategia: Kup i trzymaj (Buy and Hold).
    """
    print(f"INFO: Silnik 'Wehikuł Czasu' rozpoczyna symulację dla {ticker}...")

    # Pobierz dane historyczne
    params = {
        "function": "TIME_SERIES_DAILY", 
        "symbol": ticker,
        "outputsize": "compact"  # Ostatnie 100 dni
    }
    
    data = data_fetcher.get_data(params) if data_fetcher else None
    
    if not data or "Time Series (Daily)" not in data:
        print(f"ERROR: Nie udało się pobrać danych historycznych dla {ticker}")
        return {
            "ticker": ticker,
            "trade_count": 0,
            "total_pnl": 0.0,
            "error": "Brak danych historycznych"
        }

    # Przygotuj dane
    time_series = data["Time Series (Daily)"]
    df = pd.DataFrame.from_dict(time_series, orient='index', dtype=float)
    df.columns = ['1. open', '2. high', '3. low', '4. close', '5. volume']
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    
    if len(df) < 2:
        print(f"ERROR: Za mało danych dla backtestu {ticker}")
        return {
            "ticker": ticker,
            "trade_count": 0,
            "total_pnl": 0.0,
            "error": "Niewystarczająca ilość danych"
        }

    # Prosta strategia: Kup na początku okresu, sprzedaj na końcu
    initial_price = df['4. close'].iloc[0]
    final_price = df['4. close'].iloc[-1]
    total_pnl = final_price - initial_price
    pnl_percentage = (total_pnl / initial_price) * 100 if initial_price > 0 else 0

    print(f"INFO: Symulacja zakończona. Wynik: {total_pnl:.2f} USD ({pnl_percentage:.2f}%)")
    
    return {
        "ticker": ticker,
        "trade_count": 1,  # Tylko jedna transakcja w tej strategii
        "total_pnl": total_pnl,
        "pnl_percentage": pnl_percentage,
        "initial_price": initial_price,
        "final_price": final_price,
        "period_days": len(df)
    }
