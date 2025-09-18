"""
Moduł Agenta "Złotej Ligi".

Odpowiedzialność: Przeprowadzanie dogłębnej, 360-stopniowej analizy spółek
z "Dream Teamu" w celu wyłonienia najlepszych kandydatów do inwestycji
średnioterminowych.
"""

# POPRAWKA: Usunięto kropkę z importu, aby działał w płaskiej strukturze plików.
from utils import get_latest_value, safe_float

# --- Agenci-Eksperci (Logika Analityczna) ---

def expert_agent_technik(tech_data):
    """
    Ekspert Technik – "Czytający z Wykresów".
    Ocenia sygnały z kluczowych wskaźników technicznych.
    Zwraca wynik w skali 0-100.
    """
    score = 50  # Punkt wyjściowy
    try:
        rsi_val = safe_float(get_latest_value(tech_data.get('rsi'), 'Technical Analysis: RSI', 'RSI'))
        stoch_k = safe_float(get_latest_value(tech_data.get('stoch'), 'Technical Analysis: STOCH', 'SlowK'))
        adx_val = safe_float(get_latest_value(tech_data.get('adx'), 'Technical Analysis: ADX', 'ADX'))
        
        # Sprawdzamy czy dane nie są puste
        if rsi_val is None or stoch_k is None or adx_val is None:
             return 50

        # Analiza RSI i Stochastycznego
        if rsi_val < 30 and stoch_k < 20: score += 25
        elif rsi_val < 40 and stoch_k < 30: score += 15
        if rsi_val > 70 and stoch_k > 80: score -= 25

        # Analiza MACD
        macd_data = tech_data.get('macd')
        if macd_data:
            macd_hist = get_latest_value(macd_data, 'Technical Analysis: MACD', 'MACD_Hist')
            if macd_hist is not None and safe_float(macd_hist) > 0: score += 20

        # Analiza Wstęg Bollingera
        bbands_data = tech_data.get('bbands')
        if bbands_data:
            bbands = get_latest_value(bbands_data, 'Technical Analysis: BBANDS')
            if bbands:
                price = safe_float(tech_data.get('price'))
                lower_band = safe_float(bbands.get('Real Lower Band'))
                if price and lower_band and price <= lower_band: score += 20

        # Wzmocnienie oceny przez ADX
        if adx_val > 25 and score > 60: score += 10
        if adx_val > 25 and score < 40: score -= 10

    except Exception as e:
        print(f"[Ekspert Technik] Błąd analizy: {e}")
        return 50 # Zwróć neutralny wynik w przypadku błędu
        
    return max(0, min(100, score))


def expert_agent_fundamentalista(overview_data):
    """
    Ekspert Fundamentalista – "Księgowy-Detektyw".
    Ocenia kluczowe wskaźniki finansowe spółki.
    Zwraca wynik w skali 0-100.
    """
    if not overview_data or not isinstance(overview_data, dict):
        return 30 # Niska ocena za brak danych
    score = 50
    try:
        pe = safe_float(overview_data.get('PERatio'), default=999)
        pb = safe_float(overview_data.get('PriceToBookRatio'), default=999)
        eps = safe_float(overview_data.get('EPS'), default=0)

        if 0 < pe < 20: score += 25
        elif pe > 40 or pe == 0: score -= 20
        
        if 0 < pb < 3: score += 20
        elif pb > 7: score -= 15

        if eps > 0: score += 25
        else: score -= 25
        
    except Exception as e:
        print(f"[Ekspert Fundamentalista] Błąd analizy: {e}")
        return 50

    return max(0, min(100, score))


def expert_agent_kwant(daily_data, overview_data):
    """
    Ekspert Kwant – "Historyk i Statystyk".
    Analizuje historyczną częstotliwość wzrostów i ryzyko (Beta).
    Zwraca wynik w skali 0-100.
    """
    if not daily_data or not isinstance(daily_data, dict) or not overview_data:
        return 30
    score = 50
    try:
        # Analiza częstotliwości dni wzrostowych
        series = list(daily_data.get('Time Series (Daily)', {}).values())[:90]
        if len(series) > 1:
            growth_days = sum(1 for i in range(len(series) - 1) if safe_float(series[i]['4. close']) > safe_float(series[i+1]['4. close']))
            growth_frequency = (growth_days / len(series)) * 100
            if growth_frequency > 55: score += 20
            elif growth_frequency > 50: score += 10

        # Analiza Bety
        beta = safe_float(overview_data.get('Beta'), default=1.0)
        if 0.8 < beta < 1.5: score += 15
        elif beta > 2.0: score -= 15

    except Exception as e:
        print(f"[Ekspert Kwant] Błąd analizy: {e}")
        return 50
        
    return max(0, min(100, score))


def expert_agent_straznik(news_data, ticker):
    """
    Ekspert Strażnik – "Analityk Nastrojów".
    Ocenia sentyment w najnowszych wiadomościach.
    Zwraca wynik w skali 0-100.
    """
    try:
        if not news_data or not isinstance(news_data, dict) or 'feed' not in news_data:
            return 60 # Neutralny, jeśli brak wiadomości
            
        sentiments = [
            safe_float(s.get('sentiment_score', 0.0)) for item in news_data.get('feed', [])
            for s in item.get('ticker_sentiment', []) if s.get('ticker') == ticker
        ]
        
        if not sentiments:
            return 60

        avg_sentiment = sum(sentiments) / len(sentiments)

        if avg_sentiment > 0.35: return 100 # Bardzo Pozytywny
        if avg_sentiment > 0.1: return 80  # Pozytywny
        if avg_sentiment < -0.35: return 0   # Bardzo Negatywny
        if avg_sentiment < -0.1: return 20  # Negatywny
        return 60 # Neutralny
    except Exception as e:
        print(f"[Ekspert Strażnik] Błąd analizy: {e}")
        return 60


# --- Główna Funkcja Orkiestrująca ---

def run_zlota_liga_analysis(tickers, data_fetcher):
    """
    Uruchamia pełną analizę 360 stopni "Złotej Ligi" dla podanych tickerów.
    """
    print(f"[Złota Liga] Rozpoczynam głęboką analizę {len(tickers)} spółek...")
    results = []

    for ticker in tickers:
        print(f"[Złota Liga] Analizuję {ticker}...")
        try:
            # Zebranie wszystkich danych potrzebnych ekspertom
            overview = data_fetcher.get_data({"function": "OVERVIEW", "symbol": ticker})
            daily = data_fetcher.get_data({"function": "TIME_SERIES_DAILY", "symbol": ticker, "outputsize": "compact"})
            news = data_fetcher.get_data({"function": "NEWS_SENTIMENT", "tickers": ticker})
            quote = data_fetcher.get_data({"function": "GLOBAL_QUOTE", "symbol": ticker})
            
            # Walidacja kluczowych danych
            if not overview or not daily or not quote:
                print(f"[Złota Liga] Pomijam {ticker} - brak podstawowych danych.")
                continue

            tech_data_payload = {
                'price': get_latest_value(quote, "Global Quote", "05. price"),
                'rsi': data_fetcher.get_data({"function": "RSI", "symbol": ticker, "interval": "daily", "time_period": 14, "series_type": "close"}),
                'macd': data_fetcher.get_data({"function": "MACD", "symbol": ticker, "interval": "daily", "series_type": "close"}),
                'stoch': data_fetcher.get_data({"function": "STOCH", "symbol": ticker, "interval": "daily"}),
                'bbands': data_fetcher.get_data({"function": "BBANDS", "symbol": ticker, "interval": "daily", "time_period": 20, "series_type": "close"}),
                'adx': data_fetcher.get_data({"function": "ADX", "symbol": ticker, "interval": "daily", "time_period": 14})
            }

            # Uruchomienie ekspertów
            tech_score = expert_agent_technik(tech_data_payload)
            fundamental_score = expert_agent_fundamentalista(overview)
            quant_score = expert_agent_kwant(daily, overview)
            sentry_score = expert_agent_straznik(news, ticker)

            avg_score = (tech_score + fundamental_score + quant_score + sentry_score) / 4

            results.append({
                'ticker': ticker,
                'techScore': tech_score,
                'fundamentalScore': fundamental_score,
                'quantScore': quant_score,
                'sentryScore': sentry_score,
                'avgScore': round(avg_score)
            })
            print(f"[Złota Liga] Analiza {ticker} zakończona. Wynik: {avg_score:.0f}/100.")

        except Exception as e:
            print(f"[Złota Liga] Krytyczny błąd podczas analizy 360 stopni dla {ticker}: {e}")
            
    print(f"[Złota Liga] Analiza zakończona. Oceniono {len(results)} spółek.")
    return sorted(results, key=lambda x: x['avgScore'], reverse=True)
