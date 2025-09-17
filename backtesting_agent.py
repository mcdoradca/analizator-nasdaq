"""
Moduł Silnika Backtestingu "Wehikuł Czasu".

Odpowiedzialność: Przeprowadzanie zaawansowanych symulacji historycznych
dla strategii "Szybkiej Ligi" na podstawie zdefiniowanych przez użytkownika
parametrów.
"""
from datetime import datetime, timedelta
import numpy as np

# Import logiki agentów Szybkiej Ligi, aby na niej bazować
from szybka_liga_agent import agent_sygnalu, agent_potwierdzenia, agent_historyczny
from utils import safe_float

# --- Funkcje Pomocnicze do Obliczania Wskaźników ---
# Te funkcje muszą być tutaj, aby symulować wskaźniki na danych historycznych

def calculate_sma(series, period):
    if len(series) < period: return None
    return sum(series[-period:]) / period

def calculate_bbands(series, period=20, nbdev=2):
    if len(series) < period: return None
    sma = calculate_sma(series, period)
    std_dev = np.std(series[-period:])
    return {
        'Real Lower Band': sma - (nbdev * std_dev),
        'Real Upper Band': sma + (nbdev * std_dev)
    }

def calculate_rsi(series, period=14):
    if len(series) < period + 1: return None
    deltas = np.diff(series)
    gains = deltas[deltas > 0]
    losses = -deltas[deltas < 0]
    avg_gain = np.mean(gains[-period:]) if len(gains) > 0 else 0
    avg_loss = np.mean(losses[-period:]) if len(losses) > 0 else 1
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_stoch(series, period=14):
    if len(series) < period: return None
    highs = [d['2. high'] for d in series]
    lows = [d['3. low'] for d in series]
    closes = [d['4. close'] for d in series]
    
    l14 = min(lows[-period:])
    h14 = max(highs[-period:])
    
    slow_k = ((closes[-1] - l14) / (h14 - l14)) * 100 if (h14 - l14) != 0 else 0
    return slow_k

# --- Główny Silnik Backtestingu ---

def run_backtest(tickers, period_days, risk_level, data_fetcher):
    """
    Uruchamia pełny backtest dla strategii "Szybkiej Ligi".
    """
    print(f"[Wehikuł Czasu] Rozpoczynam backtest dla {len(tickers)} spółek, okres: {period_days} dni, ryzyko: {risk_level}.")
    all_trades = []
    
    end_date = datetime.now()

    for ticker in tickers:
        try:
            full_daily_data = data_fetcher.get_data({
                "function": "TIME_SERIES_DAILY", "symbol": ticker, "outputsize": "full"
            })
            if not full_daily_data or 'Time Series (Daily)' not in full_daily_data:
                continue

            series = sorted(
                [(k, {k.replace('. ', ''): safe_float(v) for k, v in val.items()}) for k, val in full_daily_data['Time Series (Daily)'].items()],
                key=lambda item: datetime.strptime(item[0], '%Y-%m-%d')
            )
            
            for i in range(90, len(series)):
                current_date_str, current_day_data = series[i]
                current_date = datetime.strptime(current_date_str, '%Y-%m-%d')

                if current_date < (end_date - timedelta(days=period_days)):
                    continue

                historical_slice = [s[1] for s in series[:i+1]]
                historical_slice_dict = dict(series[:i+1])
                mock_daily_data = {'Time Series (Daily)': historical_slice_dict}
                
                # Symulacja obliczeń wskaźników na danych historycznych
                close_prices = [s['4close'] for s in historical_slice]
                mock_sma_data = {'Technical Analysis: SMA': {current_date_str: {'SMA': calculate_sma(close_prices, 50)}}}
                mock_bbands_data = {'Technical Analysis: BBANDS': {current_date_str: calculate_bbands(close_prices)}}
                mock_rsi_data = {'Technical Analysis: RSI': {current_date_str: {'RSI': calculate_rsi(close_prices)}}}
                mock_stoch_data = {'Technical Analysis: STOCH': {current_date_str: {'SlowK': calculate_stoch(historical_slice)}}}

                # Uruchomienie agentów Szybkiej Ligi z pełnymi danymi
                signal_result = agent_sygnalu(mock_daily_data, mock_sma_data, mock_bbands_data)
                
                if signal_result.get('signal'):
                    confirmation_score = agent_potwierdzenia(mock_rsi_data, mock_stoch_data)
                    history_result = agent_historyczny(mock_daily_data)
                    total_score = 1 + confirmation_score + history_result['historyScore']

                    if total_score >= risk_level:
                        entry_price = signal_result['entry']
                        stop_loss = signal_result['stopLoss']
                        target_price = entry_price * 1.025

                        trade_closed = False
                        for j in range(i + 1, len(series)):
                            future_date_str, future_day_data = series[j]
                            future_low = future_day_data['3low']
                            future_high = future_day_data['2high']

                            if future_low <= stop_loss:
                                all_trades.append({
                                    'ticker': ticker, 'pnl': stop_loss - entry_price,
                                    'openDate': current_date_str, 'closeDate': future_date_str
                                })
                                trade_closed = True
                                break
                            
                            if future_high >= target_price:
                                all_trades.append({
                                    'ticker': ticker, 'pnl': target_price - entry_price,
                                    'openDate': current_date_str, 'closeDate': future_date_str
                                })
                                trade_closed = True
                                break
                        
                        if trade_closed:
                            i += 5

        except Exception as e:
            print(f"[Wehikuł Czasu] Błąd podczas symulacji dla {ticker}: {e}")

    print(f"[Wehikuł Czasu] Backtest zakończony. Zasymulowano {len(all_trades)} transakcji.")
    return sorted(all_trades, key=lambda x: datetime.strptime(x['closeDate'], '%Y-%m-%d'))

