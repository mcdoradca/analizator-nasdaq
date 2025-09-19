"""
Moduł Agentów Selekcyjnych ("Rewolucja AI").

Odpowiedzialność: Skanowanie rynku Nasdaq w sposób odporny na błędy,
z możliwością wstrzymywania i wznawiania, w celu wyłonienia "Dream Teamu",
zgodnie z zaawansowanymi standardami produkcyjnymi.
"""
import pandas as pd
from io import StringIO
from typing import Dict, Any, List
from utils import safe_float, get_latest_value
from portfolio_manager import PortfolioManager
from data_fetcher import DataFetcher

# Definiujemy, ile spółek agent ma skanować w jednej partii.
SCAN_BATCH_SIZE = 50

# --- Agenci Fazy 2 ---

def agent_plynnosci(daily_data: Dict[str, Any]) -> bool:
    """Analizuje wolumen w poszukiwaniu skoków zainteresowania."""
    try:
        series = list(daily_data['Time Series (Daily)'].values())[:30]
        if len(series) < 30: return False
        volumes = [safe_float(day['5. volume']) for day in series]
        if not volumes: return False
        avg_volume = sum(volumes) / len(volumes)
        if avg_volume == 0: return False
        return any(v > avg_volume * 5 for v in volumes)
    except (KeyError, IndexError, TypeError):
        return False

def agent_impulsu(sma_data: Dict[str, Any], current_price: float) -> bool:
    """Sprawdza, czy cena jest powyżej 50-dniowej średniej kroczącej."""
    try:
        latest_sma = safe_float(get_latest_value(sma_data, 'Technical Analysis: SMA', 'SMA'))
        return current_price > latest_sma
    except (KeyError, IndexError, TypeError):
        return False

def agent_zmiennosci(atr_data: Dict[str, Any], current_price: float) -> bool:
    """Sprawdza, czy dzienna zmienność (ATR) jest wystarczająco duża."""
    try:
        latest_atr = safe_float(get_latest_value(atr_data, 'Technical Analysis: ATR', 'ATR'))
        if current_price == 0: return False
        return (latest_atr / current_price) >= 0.04
    except (KeyError, IndexError, TypeError):
        return False

# --- Agent Pobierający Listę Rynku ---

def agent_listy_rynkowej(data_fetcher: DataFetcher) -> list[str]:
    """Pobiera pełną listę wszystkich spółek notowanych na Nasdaq."""
    print("[Rewolucja AI] Agent Listy Rynkowej pobiera listę spółek...")
    try:
        # KLUCZOWA POPRAWKA: Pobieramy dane w formacie tekstowym (CSV)
        csv_text = data_fetcher.get_data({"function": "LISTING_STATUS"}, response_format='csv')
        if not csv_text or not isinstance(csv_text, str): 
            print("[Rewolucja AI] Błąd: Nie otrzymano danych CSV lub dane są w złym formacie.")
            return []
        
        # Używamy StringIO, aby pandas mógł odczytać string jak plik
        df = pd.read_csv(StringIO(csv_text))
        
        nasdaq_stocks = df[(df['exchange'] == 'NASDAQ') & (df['assetType'] == 'Stock') & (df['status'] == 'Active')]
        
        tickers = nasdaq_stocks['symbol'].tolist()
        print(f"[Rewolucja AI] Pomyślnie pobrano {len(tickers)} spółek.")
        return tickers
    except Exception as e:
        print(f"[Rewolucja AI] Krytyczny błąd podczas przetwarzania listy spółek: {e}")
        return []

# --- NOWA, ZINTEGROWANA LOGIKA STERUJĄCA ---

def run_revolution_step(portfolio_manager: PortfolioManager, data_fetcher: DataFetcher) -> Dict[str, Any]:
    """
    Wykonuje jeden, zintegrowany krok (partię) Rewolucji AI, łącząc Fazę 1 i 2.
    """
    state = portfolio_manager.get_revolution_state()
    if not state.get("is_active", False):
        return state

    full_list = state["full_market_list"]
    start_index = state["last_scanned_index"] + 1
    end_index = min(start_index + SCAN_BATCH_SIZE, len(full_list))
    
    log_messages = [f"Rozpoczynam partię od {start_index} do {end_index-1}..."]
    newly_qualified_objects = []

    for i in range(start_index, end_index):
        if not portfolio_manager.get_revolution_state()["is_active"]:
            log_messages.append("Wykryto pauzę. Zatrzymuję bieżącą partię.")
            portfolio_manager.save_progress(i - 1, newly_qualified_objects, log_messages)
            return portfolio_manager.get_revolution_state()

        ticker = full_list[i]
        
        try:
            quote_data = data_fetcher.get_data({"function": "GLOBAL_QUOTE", "symbol": ticker})
            price = safe_float(get_latest_value(quote_data, 'Global Quote', '05. price'))
            volume = safe_float(get_latest_value(quote_data, 'Global Quote', '06. volume'))

            if not (0 < price <= 5.0 and volume > 100000):
                continue
            
            log_messages.append(f"[{ticker}] Faza 1: OK. Cena: ${price:.2f}, Wolumen: {volume}.")

            daily_data = data_fetcher.get_data({"function": "TIME_SERIES_DAILY", "symbol": ticker, "outputsize": "compact"})
            sma_data = data_fetcher.get_data({"function": "SMA", "symbol": ticker, "interval": "daily", "time_period": 50, "series_type": "close"})
            atr_data = data_fetcher.get_data({"function": "ATR", "symbol": ticker, "interval": "daily", "time_period": 14})
            
            if not daily_data or "Time Series (Daily)" not in daily_data or not sma_data or not atr_data:
                log_messages.append(f"[{ticker}] Faza 2: Odrzucono - brak kompletnych danych analitycznych.")
                continue

            current_price = safe_float(get_latest_value(daily_data, 'Time Series (Daily)', '4. close'))

            score = 0
            if agent_plynnosci(daily_data): score += 1
            if agent_impulsu(sma_data, current_price): score += 1
            if agent_zmiennosci(atr_data, current_price): score += 1

            if score >= 2:
                change_str = get_latest_value(quote_data, 'Global Quote', '10. change percent', '0%').replace('%','')
                newly_qualified_objects.append({
                    "ticker": ticker, "status": "Nowy Kandydat",
                    "currentPrice": current_price,
                    "changePercent": safe_float(change_str, default=None),
                    "aiScore": score
                })
                log_messages.append(f"[{ticker}] Faza 2: ZAKWALIFIKOWANO. Wynik: {score}/3.")
            else:
                log_messages.append(f"[{ticker}] Faza 2: Odrzucono - zbyt niski wynik ({score}/3).")
                
        except Exception as e:
            log_messages.append(f"[{ticker}] Błąd krytyczny: {e}")
            continue
            
    portfolio_manager.save_progress(end_index - 1, newly_qualified_objects, log_messages)

    if end_index == len(full_list):
        print("[Rewolucja AI] Cały proces skanowania zakończony.")
        portfolio_manager.complete_revolution()
        
    return portfolio_manager.get_revolution_state()
