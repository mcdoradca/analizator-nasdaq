"""
Moduł "Rady Mędrców" ("Złota Liga").

Odpowiedzialność: Przeprowadzenie dogłębnej, 360-stopniowej analizy spółek
z "Dream Teamu", aby wyłonić te o największym potencjale w średnim terminie.
"""
from utils import get_latest_value, safe_float # POPRAWIONY IMPORT

# --- Wyspecjalizowani Agenci-Eksperci ---

def expert_agent_technik(tech_signals):
    """Ocenia zaawansowane wskaźniki techniczne."""
    score = 0
    if not tech_signals: return 50
    
    rsi_val = tech_signals.get('rsi')
    macd_hist = tech_signals.get('macd_hist')
    stoch_k = tech_signals.get('stoch_k')
    
    if rsi_val:
        if rsi_val < 30: score += 25
        elif rsi_val > 70: score -= 25

    if macd_hist and macd_hist > 0: score += 20
    elif macd_hist and macd_hist < 0: score -= 20
        
    if stoch_k and stoch_k < 20: score += 25
    elif stoch_k and stoch_k > 80: score -= 25

    return max(0, min(100, 50 + score))


def expert_agent_fundamentalista(overview_data):
    """Analizuje kondycję finansową firmy."""
    score = 50
    if not overview_data: return score
    
    pe_ratio = safe_float(overview_data.get('PERatio'))
    pb_ratio = safe_float(overview_data.get('PriceToBookRatio'))
    eps = safe_float(overview_data.get('EPS'))

    if 0 < pe_ratio < 15: score += 20
    elif pe_ratio > 40: score -= 15
        
    if 0 < pb_ratio < 3: score += 15
    
    if eps > 0: score += 15
    else: score -= 20
        
    return max(0, min(100, score))


def expert_agent_kwant(stock_df, overview_data):
    """Bada historyczne zachowanie i ryzyko akcji."""
    score = 50
    if stock_df is None or overview_data is None: return score
    
    # Analiza zmienności (ATR)
    stock_df['atr'] = stock_df['high'].rolling(14).max() - stock_df['low'].rolling(14).min()
    avg_atr_percent = (stock_df['atr'].mean() / stock_df['close'].mean()) * 100
    if avg_atr_percent > 4: score += 15 # Preferujemy spółki z energią
        
    # Analiza bety
    beta = safe_float(overview_data.get('Beta'))
    if 1.2 < beta < 2.5: score += 10 # Umiarkowane ryzyko
    elif beta >= 2.5: score -= 10 # Zbyt ryzykowne

    return max(0, min(100, score))


def expert_agent_straznik(news_data):
    """Ocenia nastroje panujące wokół spółki w mediach."""
    if not news_data or not news_data.get('feed'):
        return 60 # Neutralny wynik, gdy brak danych

    sentiments = [
        safe_float(item['ticker_sentiment'][0]['sentiment_score'])
        for item in news_data['feed']
        if item.get('ticker_sentiment')
    ]
    
    if not sentiments: return 60

    avg_sentiment = sum(sentiments) / len(sentiments)
    
    if avg_sentiment > 0.35: return 100 # Bardzo pozytywny
    if avg_sentiment > 0.15: return 80  # Pozytywny
    if avg_sentiment < -0.35: return 0   # Bardzo negatywny
    if avg_sentiment < -0.15: return 20  # Negatywny
    return 60 # Neutralny

# --- Główna Funkcja Orkiestrująca ---

def run_golden_league_analysis(dream_team_tickers, data_fetcher, stock_data_cache):
    """
    Orkiestruje pracę wszystkich ekspertów Złotej Ligi.
    """
    league_results = []

    for ticker in dream_team_tickers:
        try:
            # Używamy danych z cache, które zostały pobrane w main.py
            api_data = stock_data_cache.get(ticker)
            if not api_data: continue

            # Uruchomienie poszczególnych agentów-ekspertów
            tech_score = expert_agent_technik(api_data.get("indicators"))
            fundamental_score = expert_agent_fundamentalista(api_data.get("overview"))
            quant_score = expert_agent_kwant(api_data.get("stock_df"), api_data.get("overview"))
            sentry_score = expert_agent_straznik(api_data.get("news"))

            league_results.append({
                "ticker": ticker,
                "techScore": tech_score,
                "fundamentalScore": fundamental_score,
                "quantScore": quant_score,
                "sentryScore": sentry_score
            })
        except Exception as e:
            print(f"[Złota Liga] Błąd podczas analizy {ticker}: {e}")
            continue
            
    return league_results

