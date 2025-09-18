"""
Moduł Silnika Backtestingu "Wehikuł Czasu".

Odpowiedzialność: Przeprowadzanie zaawansowanych symulacji historycznych
dla strategii "Szybkiej Ligi" na podstawie zdefiniowanych przez użytkownika
parametrów.
"""
from datetime import datetime, timedelta
import numpy as np

# Zaktualizowany import - używamy nowej, właściwej funkcji sygnałowej
from szybka_liga_agent import agent_korekty_fibonacciego, agent_potwierdzenia, agent_historyczny
from utils import safe_float
import pandas as pd

# --- Funkcje Pomocnicze do Obliczania Wskaźników ---
# Pozostają na potrzeby mockowania danych dla agentów
def calculate_rsi(series: pd.Series, period=14):
    if len(series) < period + 1: return None
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_stoch(high_series: pd.Series, low_series: pd.Series, close_series: pd.Series, period=14):
    if len(high_series) < period: return None
    l14 = low_series.rolling(window=period).min()
    h14 = high_series.rolling(window=period).max()
    k_percent = 100 * ((close_series - l14) / (h14 - l14))
    return k_percent

# --- Główny Silnik Backtestingu (Naprawiony) ---

def run_backtest(tickers, period_days, risk_level, data_fetcher):
    """
    Uruchamia pełny backtest dla strategii "Szybkiej Ligi" z poprawioną logiką.
    """
    print(f"[Wehikuł Czasu] Rozpoczynam backtest dla {len(tickers)} spółek, okres: {period_days} dni, ryzyko: {risk_level}.")
    all_trades = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period_days)

    for ticker in tickers:
        try:
            full_daily_data_json = data_fetcher.get_data({
                "function": "TIME_SERIES_DAILY", "symbol": ticker, "outputsize": "full"
            })
            if not full_daily_data_json: continue

            df = pd.DataFrame.from_dict(full_daily_data_json['Time Series (Daily)'], orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.apply(pd.to_numeric)
            df.rename(columns={
                '1. open': 'open', '2. high': 'high', '3. low': 'low', '4. close': 'close', '5. volume': 'volume'
            }, inplace=True)
            df.sort_index(ascending=True, inplace=True)
            
            # Symulujemy wskaźniki na całej serii, aby uniknąć błędów
            df['rsi'] = calculate_rsi(df['close'])
            df['stoch_k'] = calculate_stoch(df['high'], df['low'], df['close'])

            # Iterujemy po danych historycznych
            for i in range(30, len(df)): # Zaczynamy od 30, aby mieć wystarczająco danych
                current_date = df.index[i]
                if current_date < start_date:
                    continue

                # Tworzenie "migawki" danych historycznych na dany dzień
                historical_df = df.iloc[:i+1]
                mock_daily_data = {'Time Series (Daily)': historical_df.iloc[::-1].to_dict('index')}
                
                # Uruchomienie agentów z symulowanymi danymi
                # POPRAWKA 1: Wywołanie poprawnej funkcji 'agent_korekty_fibonacciego'
                signal_result = agent_korekty_fibonacciego(mock_daily_data)
                
                if signal_result.get('signal'):
                    # Tworzenie mockowych danych dla agentów potwierdzenia
                    current_rsi = historical_df.iloc[-1]['rsi']
                    current_stoch = historical_df.iloc[-1]['stoch_k']
                    mock_rsi_data = {'Technical Analysis: RSI': {str(current_date.date()): {'RSI': current_rsi}}}
                    mock_stoch_data = {'Technical Analysis: STOCH': {str(current_date.date()): {'SlowK': current_stoch}}}

                    confirmation_score = agent_potwierdzenia(mock_rsi_data, mock_stoch_data)
                    history_result = agent_historyczny(mock_daily_data)
                    total_score = 1 + confirmation_score + history_result['historyScore']

                    if total_score >= 1: # Zgodnie z logiką szybka_liga (1 + 0/1 + 0/1)
                        # POPRAWKA 2: Dostęp do planu transakcyjnego z nowej struktury
                        entry_price = signal_result['entry']
                        stop_loss = signal_result['plan']['stopLoss']
                        target_price = signal_result['plan']['target']
                        
                        trade_closed = False
                        # Symulacja przyszłości od momentu otwarcia transakcji
                        for j in range(i + 1, len(df)):
                            future_day = df.iloc[j]
                            
                            if future_day['low'] <= stop_loss:
                                all_trades.append({
                                    'ticker': ticker, 'pnl': stop_loss - entry_price,
                                    'openDate': str(current_date.date()), 'closeDate': str(future_day.name.date())
                                })
                                trade_closed = True
                                break
                            
                            if future_day['high'] >= target_price:
                                all_trades.append({
                                    'ticker': ticker, 'pnl': target_price - entry_price,
                                    'openDate': str(current_date.date()), 'closeDate': str(future_day.name.date())
                                })
                                trade_closed = True
                                break
                        
                        if trade_closed:
                            i += 5 # Przeskakujemy kilka dni, aby uniknąć ponownego wejścia

        except Exception as e:
            print(f"[Wehikuł Czasu] Błąd podczas symulacji dla {ticker}: {e}")

    print(f"[Wehikuł Czasu] Backtest zakończony. Zasymulowano {len(all_trades)} transakcji.")
    return sorted(all_trades, key=lambda x: datetime.strptime(x['closeDate'], '%Y-%m-%d'))
