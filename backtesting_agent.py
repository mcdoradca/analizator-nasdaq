"""
Moduł Silnika Backtestingu "Wehikuł Czasu".

Odpowiedzialność: Przeprowadzanie zaawansowanych symulacji historycznych
dla strategii "Szybkiej Ligi" na podstawie zdefiniowanych przez użytkownika
parametrów.
"""
from datetime import datetime, timedelta
import numpy as np
from typing import List, Dict, Any

# Import logiki agentów Szybkiej Ligi, aby na niej bazować
from szybka_liga_agent import agent_korekty_fibonacciego, agent_potwierdzenia, agent_historyczny
from utils import safe_float

# --- Funkcje Pomocnicze do Obliczania Wskaźników ---
# Te funkcje muszą być tutaj, aby symulować wskaźniki na danych historycznych

def calculate_sma(series: List[float], period: int) -> float | None:
    if len(series) < period: return None
    return sum(series[-period:]) / period

def calculate_bbands(series: List[float], period: int = 20, nbdev: int = 2) -> Dict[str, float] | None:
    if len(series) < period: return None
    sma = calculate_sma(series, period)
    if sma is None: return None
    std_dev = np.std(series[-period:])
    return {
        'Real Lower Band': sma - (nbdev * std_dev),
        'Real Upper Band': sma + (nbdev * std_dev)
    }

def calculate_rsi(series: List[float], period: int = 14) -> float | None:
    if len(series) < period + 1: return None
    deltas = np.diff(series)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum()/period
    down = -seed[seed < 0].sum()/period
    if down == 0: return 100.0
    rs = up / down
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi

def calculate_stoch(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float | None:
    if len(closes) < period: return None
    
    l14 = min(lows[-period:])
    h14 = max(highs[-period:])
    
    if (h14 - l14) == 0: return 0
    
    slow_k = ((closes[-1] - l14) / (h14 - l14)) * 100
    return slow_k

# --- Główny Silnik Backtestingu ---

def run_backtest_for_ticker(ticker: str, period_days: int, data_fetcher: Any) -> List[Dict[str, Any]]:
    """
    Uruchamia pełny backtest dla strategii "Szybkiej Ligi" dla JEDNEGO tickera.
    """
    print(f"[Wehikuł Czasu] Rozpoczynam backtest dla {ticker}, okres: {period_days} dni.")
    all_trades = []
    
    end_date = datetime.now()
    start_date_limit = end_date - timedelta(days=period_days)

    try:
        # Pobieramy dane z odpowiednim wyprzedzeniem
        full_daily_data = data_fetcher.get_data({
            "function": "TIME_SERIES_DAILY", "symbol": ticker, "outputsize": "full"
        })
        if not full_daily_data or 'Time Series (Daily)' not in full_daily_data:
            print(f"[Wehikuł Czasu] Brak danych historycznych dla {ticker}.")
            return []

        # Sortujemy dane od najstarszych do najnowszych
        series = sorted(
            full_daily_data['Time Series (Daily)'].items(),
            key=lambda item: datetime.strptime(item[0], '%Y-%m-%d')
        )
        
        # Iterujemy przez dane dzień po dniu, symulując upływ czasu
        for i in range(90, len(series)): # Potrzebujemy min. 90 dni historii do analizy
            current_date_str, current_day_values = series[i]
            current_date = datetime.strptime(current_date_str, '%Y-%m-%d')

            # Pomiń dni spoza okresu testowego
            if current_date < start_date_limit:
                continue

            # Przygotowujemy "udawane" dane, jakie agenci widzieliby danego dnia
            historical_slice_dict = dict(series[:i+1])
            mock_daily_data = {'Time Series (Daily)': historical_slice_dict}
            
            # Uruchomienie agenta sygnału
            signal_result = agent_korekty_fibonacciego(mock_daily_data)
            
            if signal_result.get('signal'):
                # Jeśli jest sygnał, symulujemy transakcję
                entry_price = signal_result['entry']
                stop_loss = signal_result['plan']['stopLoss']
                target_price = signal_result['plan']['target']

                # Sprawdzamy przyszłe dni, aby zobaczyć, jak transakcja by się zakończyła
                for j in range(i + 1, len(series)):
                    future_date_str, future_day_data = series[j]
                    future_low = safe_float(future_day_data['3. low'])
                    future_high = safe_float(future_day_data['4. close']) # Używamy ceny zamknięcia jako uproszczenia dla zysku

                    # Sprawdzenie, czy Stop Loss został osiągnięty
                    if future_low <= stop_loss:
                        pnl = (stop_loss - entry_price)
                        all_trades.append({
                            'ticker': ticker, 'pnl': pnl,
                            'openDate': current_date_str, 'closeDate': future_date_str, 'reason': 'Stop Loss'
                        })
                        break # Zamykamy pętlę dla tej transakcji
                    
                    # Sprawdzenie, czy Cel Zysku został osiągnięty
                    if future_high >= target_price:
                        pnl = (target_price - entry_price)
                        all_trades.append({
                            'ticker': ticker, 'pnl': pnl,
                            'openDate': current_date_str, 'closeDate': future_date_str, 'reason': 'Take Profit'
                        })
                        break # Zamykamy pętlę dla tej transakcji

    except Exception as e:
        print(f"[Wehikuł Czasu] Krytyczny błąd podczas symulacji dla {ticker}: {e}")

    print(f"[Wehikuł Czasu] Backtest zakończony. Zasymulowano {len(all_trades)} transakcji dla {ticker}.")
    return all_trades

