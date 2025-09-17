"""
Moduł Zespołu Taktycznego AI ("Szybka Liga").

Odpowiedzialność: Skanowanie spółek z "Dream Teamu" w poszukiwaniu
krótkoterminowych, precyzyjnych okazji transakcyjnych opartych na strategii
"Łowcy Impulsu i Korekty".
"""
from utils import safe_float, get_latest_value

# --- NOWA, EKSPERCKA JEDNOSTKA: Agent Korekty Fibonacciego ---

def agent_korekty_fibonacciego(daily_data, period=30):
    """
    Identyfikuje spółki po silnym impulsie wzrostowym, które dokonują
    zdrowej korekty do kluczowych poziomów zniesienia Fibonacciego.
    """
    try:
        series = list(daily_data['Time Series (Daily)'].items())[:period]
        if len(series) < 10: return {}

        prices = [(s[0], {k.replace('. ', ''): safe_float(v) for k, v in s[1].items()}) for s in series]
        
        # Znajdź lokalny dołek i szczyt ostatniego impulsu
        recent_high = max(p[1]['2high'] for p in prices)
        high_date_index = [p[1]['2high'] for p in prices].index(recent_high)
        
        # Szukamy dołka, który poprzedzał ten szczyt
        recent_low = min(p[1]['3low'] for p in prices[high_date_index:])
        
        current_price = prices[0][1]['4close']
        
        # Jeśli jesteśmy wciąż na szczycie, nie ma sygnału
        if current_price >= recent_high:
            return {}

        # Oblicz poziomy Fibonacciego
        price_range = recent_high - recent_low
        fibo_382 = recent_high - 0.382 * price_range
        fibo_500 = recent_high - 0.500 * price_range
        fibo_618 = recent_high - 0.618 * price_range

        # Sprawdź, czy cena dotknęła strefy kupna
        if fibo_500 <= current_price <= fibo_382:
            return {
                'signal': 'Korekta do strefy Fibonacciego',
                'entry': current_price,
                'plan': {
                    'target': recent_high,
                    'stopLoss': fibo_618
                }
            }
        
        return {}
    except Exception:
        return {}

# --- Istniejący Agenci Pomocniczy (bez zmian) ---

def agent_potwierdzenia(rsi_data, stoch_data):
    """Sprawdza, czy rynek nie jest wykupiony (RSI, Stoch)."""
    try:
        rsi = safe_float(get_latest_value(rsi_data, 'Technical Analysis: RSI', 'RSI'))
        stoch = safe_float(get_latest_value(stoch_data, 'Technical Analysis: STOCH', 'SlowK'))
        if rsi > 75 or stoch > 85:
            return 0
        return 1
    except Exception:
        return 0

def agent_historyczny(daily_data):
    """Weryfikuje, czy spółka ma historię dynamicznych wzrostów wewnątrzsesyjnych."""
    stats = {'1.5': 0, '2.0': 0, '3.0': 0}
    try:
        series = list(daily_data['Time Series (Daily)'].values())[:90]
        for day in series:
            op = safe_float(day['1. open'])
            hi = safe_float(day['2. high'])
            if op == 0: continue
            
            intraday_change = ((hi / op) - 1) * 100
            if intraday_change >= 3.0: stats['3.0'] += 1
            if intraday_change >= 2.0: stats['2.0'] += 1
            if intraday_change >= 1.5: stats['1.5'] += 1
            
        history_score = 1 if stats['2.0'] >= 5 else 0
        return {'historyScore': history_score, 'stats': stats}
    except Exception:
        return {'historyScore': 0, 'stats': stats}

# --- Główna Funkcja Orkiestrująca Skanowanie (PRZEBUDOWANA) ---

def run_quick_league_scan(dream_team_tickers, data_fetcher):
    """
    Orkiestruje pracę wszystkich agentów Szybkiej Ligi, aby wyłonić okazje.
    """
    opportunities = []
    print(f"[Szybka Liga] Rozpoczynam skanowanie {len(dream_team_tickers)} spółek...")

    for ticker in dream_team_tickers:
        try:
            # Pobranie danych
            daily_data = data_fetcher.get_data({"function": "TIME_SERIES_DAILY", "symbol": ticker, "outputsize": "compact"})
            rsi_data = data_fetcher.get_data({"function": "RSI", "symbol": ticker, "interval": "daily", "time_period": 14, "series_type": "close"})
            stoch_data = data_fetcher.get_data({"function": "STOCH", "symbol": ticker, "interval": "daily"})
            
            if not all([daily_data, rsi_data, stoch_data]):
                continue

            # 1. Nowy Agent Korekty Fibonacciego szuka głównego sygnału
            signal_result = agent_korekty_fibonacciego(daily_data)
            
            if signal_result.get('signal'):
                # 2. Pozostali agenci oceniają sygnał
                confirmation_score = agent_potwierdzenia(rsi_data, stoch_data)
                history_result = agent_historyczny(daily_data)
                total_score = 1 + confirmation_score + history_result['historyScore']
                
                # 3. Sprawdzamy, czy plan ma sens (ryzyko < potencjalny zysk)
                plan = signal_result['plan']
                risk = signal_result['entry'] - plan['stopLoss']
                reward = plan['target'] - signal_result['entry']
                if risk <= 0 or reward <= 0 or reward / risk < 1.5: # Podnosimy poprzeczkę
                    continue

                opportunities.append({
                    'ticker': ticker,
                    'signal': signal_result['signal'],
                    'plan': plan,
                    'stats': history_result['stats'],
                    'score': total_score
                })
        except Exception as e:
            print(f"[Szybka Liga] Błąd podczas analizy {ticker}: {e}")
            continue
            
    print(f"[Szybka Liga] Skanowanie zakończone. Znaleziono {len(opportunities)} okazji.")
    return opportunities

