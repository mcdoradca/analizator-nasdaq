"""
Moduł Agentów Makroekonomicznych.

Odpowiedzialność: Analiza ogólnej kondycji gospodarki ("Klimat" - Agent Sokół)
oraz siły trendu na szerokim rynku ("Barometr Rynku").
"""
from utils import get_latest_value, safe_float

# --- Agent "Sokół" (Klimat Makroekonomiczny) ---

def agent_sokol(data_fetcher):
    """
    Analizuje kluczowe wskaźniki makroekonomiczne (inflacja, stopy, bezrobocie).
    """
    try:
        # Pobieranie danych
        cpi_data = data_fetcher.get_data({"function": "CPI", "interval": "monthly"})
        rate_data = data_fetcher.get_data({"function": "FEDERAL_FUNDS_RATE", "interval": "monthly"})
        unemployment_data = data_fetcher.get_data({"function": "UNEMPLOYMENT"})

        # Walidacja danych
        if not all([cpi_data, rate_data, unemployment_data]) or \
           len(cpi_data.get('data', [])) < 2 or \
           len(rate_data.get('data', [])) < 2 or \
           len(unemployment_data.get('data', [])) < 2:
            return {"status": "Brak Danych Makro", "color": "text-gray-400", "icon": "fa-question-circle"}

        # Obliczanie trendów
        cpi_trend = safe_float(cpi_data['data'][0]['value']) - safe_float(cpi_data['data'][1]['value'])
        rate_trend = safe_float(rate_data['data'][0]['value']) - safe_float(rate_data['data'][1]['value'])
        unemployment_trend = safe_float(unemployment_data['data'][0]['value']) - safe_float(unemployment_data['data'][1]['value'])

        # Logika oceny
        score = 0
        if cpi_trend < 0: score += 2
        elif cpi_trend > 0.1: score -= 2
        if rate_trend <= 0: score += 2
        else: score -= 2
        if unemployment_trend <= 0: score += 1
        else: score -= 1
        
        if score >= 3:
            return {"status": "Sprzyjający Ryzyku", "color": "text-green-400", "icon": "fa-feather-alt"}
        if score <= -2:
            return {"status": "Wysoka Ostrożność", "color": "text-red-400", "icon": "fa-shield-alt"}
        return {"status": "Neutralny / Zmienny", "color": "text-yellow-400", "icon": "fa-compass"}

    except Exception as e:
        print(f"[Agent Sokół] Błąd analizy makro: {e}")
        return {"status": "Błąd Analizy", "color": "text-gray-400", "icon": "fa-wifi"}

def get_macro_climate_analysis(data_fetcher):
    """Główna funkcja do wywołania analizy klimatu przez Agenta "Sokół"."""
    print("[Makro] Agent 'Sokół' analizuje klimat makroekonomiczny...")
    return agent_sokol(data_fetcher)


# --- Agent Barometru Rynkowego ---

def agent_barometru_rynkowego(data_fetcher):
    """
    Analizuje siłę trendu na indeksie Nasdaq (QQQ).
    """
    try:
        # Pobieranie danych dla QQQ
        daily_data = data_fetcher.get_data({"function": "TIME_SERIES_DAILY", "symbol": "QQQ", "outputsize": "compact"})
        sma20_data = data_fetcher.get_data({"function": "SMA", "symbol": "QQQ", "interval": "daily", "time_period": 20, "series_type": "close"})
        sma50_data = data_fetcher.get_data({"function": "SMA", "symbol": "QQQ", "interval": "daily", "time_period": 50, "series_type": "close"})

        # Walidacja danych
        if not all([daily_data, sma20_data, sma50_data]):
             return {"status": "Brak Danych", "color": "text-gray-400", "icon": "fa-question-circle"}

        price = safe_float(get_latest_value(daily_data, 'Time Series (Daily)', '4. close'))
        sma20 = safe_float(get_latest_value(sma20_data, 'Technical Analysis: SMA', 'SMA'))
        sma50 = safe_float(get_latest_value(sma50_data, 'Technical Analysis: SMA', 'SMA'))

        if price == 0 or sma20 == 0 or sma50 == 0:
            return {"status": "Błąd Obliczeń", "color": "text-yellow-400", "icon": "fa-exclamation-triangle"}

        # Logika oceny trendu
        if price > sma20 > sma50:
            return {"status": "Silny Trend Wzrostowy", "color": "text-green-400", "icon": "fa-arrow-alt-circle-up"}
        if price < sma20 < sma50:
            return {"status": "Silny Trend Spadkowy", "color": "text-red-400", "icon": "fa-arrow-alt-circle-down"}
        
        return {"status": "Konsolidacja", "color": "text-yellow-400", "icon": "fa-arrows-alt-h"}

    except Exception as e:
        print(f"[Agent Barometru] Błąd analizy: {e}")
        return {"status": "Błąd API", "color": "text-gray-400", "icon": "fa-wifi"}

def get_market_barometer(data_fetcher):
    """Główna funkcja do wywołania analizy przez Agenta Barometru."""
    print("[Makro] Agent Barometru analizuje rynek (QQQ)...")
    return agent_barometru_rynkowego(data_fetcher)

