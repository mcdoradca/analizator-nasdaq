"""
Moduł Agentów Selekcyjnych ("Rewolucja AI").

Odpowiedzialność: Skanowanie całego rynku Nasdaq, selekcja spółek (Faza 1)
oraz ich dogłębna analiza (Faza 2) w celu wyłonienia "Dream Teamu".
"""
import pandas as pd
from io import StringIO
from utils import safe_float, get_latest_value
from typing import List, Dict, Any

# --- Agenci Fazy 2 (bez zmian w logice) ---

def agent_plynnosci(daily_data: Dict) -> bool:
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

def agent_impulsu(sma_data: Dict, current_price: float) -> bool:
    """Sprawdza, czy cena jest powyżej 50-dniowej średniej kroczącej."""
    try:
        latest_sma = safe_float(get_latest_value(sma_data, 'Technical Analysis: SMA', 'SMA'))
        return current_price > latest_sma
    except (KeyError, TypeError):
        return False

def agent_zmiennosci(atr_data: Dict, current_price: float) -> bool:
    """Sprawdza, czy dzienna zmienność (ATR) jest wystarczająco duża."""
    try:
        latest_atr = safe_float(get_latest_value(atr_data, 'Technical Analysis: ATR', 'ATR'))
        if current_price == 0: return False
        # Wymagamy minimum 4% dziennej zmienności
        return (latest_atr / current_price) >= 0.04
    except (KeyError, TypeError):
        return False

# --- Agent Fazy 1 (Naprawiony) ---

def agent_listy_rynkowej(data_fetcher) -> List[str]:
    """
    Pobiera pełną listę wszystkich spółek notowanych na Nasdaq, przetwarzając dane CSV.
    """
    print("[Rewolucja AI] Agent Listy Rynkowej pobiera listę spółek z Nasdaq...")
    try:
        # data_fetcher zwraca teraz surowy tekst CSV
        csv_text_data = data_fetcher.get_data({"function": "LISTING_STATUS"})
        if not csv_text_data or not isinstance(csv_text_data, str): 
            print("[Rewolucja AI] Błąd: Otrzymano nieprawidłowe dane dla listy spółek.")
            return []

        # POPRAWKA: Użycie StringIO do wczytania tekstu CSV do DataFrame
        df = pd.read_csv(StringIO(csv_text_data))
        
        nasdaq_stocks = df[(df['exchange'] == 'NASDAQ') & (df['assetType'] == 'Stock') & (df['status'] == 'Active')]
        
        tickers = nasdaq_stocks['symbol'].tolist()
        print(f"[Rewolucja AI] Pomyślnie pobrano i przetworzono {len(tickers)} spółek.")
        return tickers
    except Exception as e:
        print(f"[Rewolucja AI] Krytyczny błąd podczas przetwarzania listy spółek CSV: {e}")
        return []

# --- Główny Proces "Rewolucji AI" (Naprawiony) ---

def run_market_scan(data_fetcher) -> Dict[str, Any]:
    """
    Orkiestruje cały, dwufazowy proces Rewolucji AI.
    """
    full_market_list = agent_listy_rynkowej(data_fetcher)
    if not full_market_list:
        return {"candidates": [], "log": ["Błąd: Nie udało się pobrać i przetworzyć listy rynku."]}

    # Ograniczenie liczby spółek do analizy w Fazie 1, aby oszczędzić czas i limity API
    # W środowisku produkcyjnym można to usunąć lub dostosować
    full_market_list = full_market_list[:500] 
    log = [f"Rozpoczynam Fazę 1: Skanowanie {len(full_market_list)} spółek..."]
    
    faza_1_candidates = []
    for ticker in full_market_list:
        try:
            quote_data = data_fetcher.get_data({"function": "GLOBAL_QUOTE", "symbol": ticker})
            if not quote_data or 'Global Quote' not in quote_data: continue

            price = safe_float(quote_data['Global Quote'].get('05. price'))
            volume = safe_float(quote_data['Global Quote'].get('06. volume'))

            if 0.1 < price <= 7.0 and volume > 150000:
                faza_1_candidates.append({'ticker': ticker, 'price': price})
                log.append(f"[Faza 1] Znaleziono kandydata: {ticker} (Cena: ${price:.2f})")
        except Exception:
            continue
            
    log.append(f"Faza 1 Zakończona. Znaleziono {len(faza_1_candidates)} kandydatów.")
    
    dream_team = []
    log.append(f"Rozpoczynam Fazę 2: Analiza {len(faza_1_candidates)} spółek...")

    for candidate in faza_1_candidates:
        ticker = candidate['ticker']
        try:
            daily_data = data_fetcher.get_data({"function": "TIME_SERIES_DAILY", "symbol": ticker, "outputsize": "compact"})
            sma_data = data_fetcher.get_data({"function": "SMA", "symbol": ticker, "interval": "daily", "time_period": 50, "series_type": "close"})
            atr_data = data_fetcher.get_data({"function": "ATR", "symbol": ticker, "interval": "daily", "time_period": 14})
            
            if not all([daily_data, sma_data, atr_data]):
                log.append(f"[Faza 2] Pominięto {ticker} - brak kompletnych danych.")
                continue

            current_price = safe_float(get_latest_value(daily_data, 'Time Series (Daily)', '4. close'))
            if current_price == 0: continue # Unikamy dzielenia przez zero

            score = 0
            if agent_plynnosci(daily_data): score += 1
            if agent_impulsu(sma_data, current_price): score += 1
            if agent_zmiennosci(atr_data, current_price): score += 1

            if score >= 2:
                # POPRAWKA: Zwracamy obiekt zgodny z oczekiwaniami PortfolioManagera
                dream_team.append({
                    'ticker': ticker,
                    'status': 'Nowy',
                    'aiScore': score,
                    'currentPrice': current_price
                })
                log.append(f"[Faza 2] Spółka {ticker} zakwalifikowana. Wynik: {score}/3")
        except Exception as e:
            log.append(f"[Faza 2] Błąd podczas analizy {ticker}: {e}")
            continue
    
    log.append(f"Rewolucja AI zakończona. Wyłoniono {len(dream_team)} spółek do Dream Teamu.")
    return {"candidates": dream_team, "log": log}
