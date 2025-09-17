"""
Moduł Agentów Selekcyjnych ("Rewolucja AI").

Odpowiedzialność: Skanowanie całego rynku Nasdaq, selekcja spółek (Faza 1)
oraz ich dogłębna analiza (Faza 2) w celu wyłonienia "Dream Teamu".
"""
import pandas as pd
from io import StringIO
from utils import safe_float, get_latest_value

# --- Agenci Fazy 2 ---

def agent_plynnosci(daily_data):
    """Analizuje wolumen w poszukiwaniu skoków zainteresowania."""
    try:
        series = list(daily_data['Time Series (Daily)'].values())[:30]
        if len(series) < 30: return False
        
        volumes = [safe_float(day['5. volume']) for day in series]
        avg_volume = sum(volumes) / len(volumes)
        
        # Sprawdza, czy jakikolwiek wolumen z ostatnich 30 dni był 5x większy od średniej
        return any(v > avg_volume * 5 for v in volumes)
    except Exception:
        return False

def agent_impulsu(sma_data, current_price):
    """Sprawdza, czy cena jest powyżej 50-dniowej średniej kroczącej."""
    try:
        latest_sma = safe_float(get_latest_value(sma_data, 'Technical Analysis: SMA', 'SMA'))
        return current_price > latest_sma
    except Exception:
        return False

def agent_zmiennosci(atr_data, current_price):
    """Sprawdza, czy dzienna zmienność (ATR) jest wystarczająco duża."""
    try:
        latest_atr = safe_float(get_latest_value(atr_data, 'Technical Analysis: ATR', 'ATR'))
        if current_price == 0: return False
        return (latest_atr / current_price) >= 0.04
    except Exception:
        return False

# --- Nowy Agent Fazy 1 ---

def agent_listy_rynkowej(data_fetcher):
    """
    Pobiera pełną listę wszystkich spółek notowanych na Nasdaq.
    """
    print("[Rewolucja AI] Agent Listy Rynkowej pobiera listę spółek z Nasdaq...")
    try:
        # Używamy endpointu LISTING_STATUS, który zwraca plik CSV
        csv_data = data_fetcher.get_data({"function": "LISTING_STATUS"})
        if csv_data is None: return []

        # Konwertujemy tekst CSV na obiekt DataFrame biblioteki pandas
        df = pd.read_csv(StringIO(csv_data))
        
        # Filtrujemy, aby zostawić tylko aktywne akcje z giełdy NASDAQ
        nasdaq_stocks = df[(df['exchange'] == 'NASDAQ') & (df['assetType'] == 'Stock') & (df['status'] == 'Active')]
        
        # Zwracamy listę samych tickerów
        tickers = nasdaq_stocks['symbol'].tolist()
        print(f"[Rewolucja AI] Pomyślnie pobrano {len(tickers)} spółek.")
        return tickers
    except Exception as e:
        print(f"[Rewolucja AI] Krytyczny błąd podczas pobierania listy spółek: {e}")
        return []

# --- Główny Proces "Rewolucji AI" ---

def run_market_scan(data_fetcher):
    """
    Orkiestruje cały, dwufazowy proces Rewolucji AI.
    """
    # FAZA 1: Skanowanie rynku i filtrowanie tanich spółek
    
    full_market_list = agent_listy_rynkowej(data_fetcher)
    if not full_market_list:
        return {"candidates": [], "log": ["Błąd: Nie udało się pobrać listy rynku."]}

    faza_1_candidates = []
    log = [f"Rozpoczynam Fazę 1: Skanowanie {len(full_market_list)} spółek..."]
    
    for ticker in full_market_list:
        try:
            quote_data = data_fetcher.get_data({"function": "GLOBAL_QUOTE", "symbol": ticker})
            price = safe_float(get_latest_value(quote_data, 'Global Quote', '05. price'))
            volume = safe_float(get_latest_value(quote_data, 'Global Quote', '06. volume'))

            # Kryterium Fazy 1: cena <= 5$ i wolumen > 100,000
            if 0 < price <= 5.0 and volume > 100000:
                faza_1_candidates.append(ticker)
                log.append(f"[Faza 1] Znaleziono kandydata: {ticker} (Cena: ${price:.2f})")
        except Exception:
            # Pomiń tickery, dla których nie ma danych
            continue
            
    log.append(f"Faza 1 Zakończona. Znaleziono {len(faza_1_candidates)} kandydatów.")
    
    # FAZA 2: Szczegółowa analiza przez wyspecjalizowanych agentów
    
    faza_2_candidates = []
    log.append(f"Rozpoczynam Fazę 2: Analiza {len(faza_1_candidates)} spółek...")

    for ticker in faza_1_candidates:
        try:
            # Pobranie wszystkich danych potrzebnych do analizy Fazy 2
            daily_data = data_fetcher.get_data({"function": "TIME_SERIES_DAILY", "symbol": ticker, "outputsize": "compact"})
            sma_data = data_fetcher.get_data({"function": "SMA", "symbol": ticker, "interval": "daily", "time_period": 50, "series_type": "close"})
            atr_data = data_fetcher.get_data({"function": "ATR", "symbol": ticker, "interval": "daily", "time_period": 14})
            
            if not all([daily_data, sma_data, atr_data]):
                log.append(f"[Faza 2] Pominięto {ticker} - brak kompletnych danych.")
                continue

            current_price = safe_float(get_latest_value(daily_data, 'Time Series (Daily)', '4. close'))
            
            # Głosowanie agentów
            score = 0
            if agent_plynnosci(daily_data): score += 1
            if agent_impulsu(sma_data, current_price): score += 1
            if agent_zmiennosci(atr_data, current_price): score += 1

            # Kryterium Fazy 2: spółka musi zdobyć co najmniej 2 z 3 głosów
            if score >= 2:
                faza_2_candidates.append(ticker)
                log.append(f"[Faza 2] Spółka {ticker} zakwalifikowana. Wynik: {score}/3")
            else:
                log.append(f"[Faza 2] Spółka {ticker} odrzucona. Wynik: {score}/3")

        except Exception as e:
            log.append(f"[Faza 2] Błąd podczas analizy {ticker}: {e}")
            continue
    
    log.append(f"Rewolucja AI zakończona. Wyłoniono {len(faza_2_candidates)} spółek do Dream Teamu.")
    return {"candidates": faza_2_candidates, "log": log}

