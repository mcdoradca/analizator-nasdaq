"""
Moduł Silnika Backtestingu "Wehikuł Czasu".

Odpowiedzialność: Przeprowadzanie symulacji historycznych dla strategii
"Szybkiej Ligi", aby zweryfikować jej skuteczność.
"""
import pandas as pd
import pandas_ta as ta
from typing import List, Dict, Any, Callable

# UWAGA: Usunięto bezpośrednie importy z szybka_liga_agent, aby przełamać pętlę zależności.
# Logika agentów będzie przekazywana jako argumenty.

def run_backtest(
    tickers: List[str],
    period: int,
    risk_level: int,
    data_fetcher: Any,
    strategy_logic: Dict[str, Callable]
) -> List[Dict[str, Any]]:
    """
    Uruchamia symulację historyczną (backtest) dla podanej listy tickerów.

    Args:
        tickers: Lista tickerów do przetestowania.
        period: Okres symulacji w dniach (np. 365).
        risk_level: Poziom ryzyka (1-3), który determinuje, jak silny musi być sygnał.
        data_fetcher: Instancja klasy DataFetcher.
        strategy_logic: Słownik zawierający funkcje agentów Szybkiej Ligi.
                        np. {'sygnalu': agent_sygnalu, 'potwierdzenia': agent_potwierdzenia, ...}

    Returns:
        Lista słowników, gdzie każdy słownik reprezentuje jedną zamkniętą transakcję.
    """
    all_trades = []
    agent_sygnalu = strategy_logic['sygnalu']
    agent_potwierdzenia = strategy_logic['potwierdzenia']
    agent_historyczny = strategy_logic['historyczny']

    for ticker in tickers:
        try:
            daily_data_json = data_fetcher.get_data({"function": "TIME_SERIES_DAILY", "symbol": ticker, "outputsize": "full"})
            if not daily_data_json: continue

            df = pd.DataFrame.from_dict(daily_data_json['Time Series (Daily)'], orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.apply(pd.to_numeric)
            df.rename(columns={
                '1. open': 'open', '2. high': 'high', '3. low': 'low',
                '4. close': 'close', '5. volume': 'volume'
            }, inplace=True)
            df.sort_index(ascending=True, inplace=True)
            
            # Obliczamy wskaźniki od razu dla całej serii danych
            df.ta.sma(length=50, append=True)
            df.ta.bbands(length=20, append=True)
            df.ta.rsi(length=14, append=True)
            df.ta.stoch(k=14, d=3, smooth_k=3, append=True)

            historical_data = df.iloc[-period-50:]
            if len(historical_data) < 52: continue

            for i in range(50, len(historical_data)):
                # Przekazujemy do agentów tylko potrzebny fragment historii
                data_slice = historical_data.iloc[:i]
                
                # Symulujemy wywołania agentów
                signal_result = agent_sygnalu(data_slice) # Przekazujemy DataFrame
                if signal_result.get('signal'):
                    confirmation_score = agent_potwierdzenia(data_slice)
                    history_result = agent_historyczny(data_slice)
                    total_score = 1 + confirmation_score + history_result['historyScore']

                    if total_score >= risk_level:
                        entry_price = signal_result['entry']
                        stop_loss = entry_price * 0.95 # Uproszczony stop-loss
                        target_price = entry_price * 1.025

                        # Sprawdzamy przyszłość, aby zamknąć transakcję
                        for j in range(i + 1, len(historical_data)):
                            future_day = historical_data.iloc[j]
                            if future_day['low'] <= stop_loss:
                                all_trades.append({'ticker': ticker, 'pnl': stop_loss - entry_price, 'closeDate': future_day.name})
                                break
                            if future_day['high'] >= target_price:
                                all_trades.append({'ticker': ticker, 'pnl': target_price - entry_price, 'closeDate': future_day.name})
                                break
        except Exception as e:
            print(f"[Backtest] Błąd podczas analizy {ticker}: {e}")
            continue
            
    return all_trades

