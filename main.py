# main.py
# Główny plik "silnika" aplikacji. Uruchamia serwer API i łączy wszystkie moduły.

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import pandas as pd
from typing import Dict, List

# --- POPRAWIONE IMPORTY Z NAPRAWIONYCH MODUŁÓW ---
from data_fetcher import DataFetcher, transform_to_dataframe
from portfolio_manager import PortfolioManager
from macro_agent import get_macro_climate_analysis
from risk_agent import analyze_portfolio_risk
from selection_agent import run_market_scan
from backtesting_agent import run_backtest_simulation

# --- KROK 1: CENTRALNA INICJALIZACJA APLIKACJI ---

# Pobieramy klucz API ze zmiennej środowiskowej (kluczowe dla Render)
api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
if not api_key:
    raise ValueError("Krytyczny błąd: Brak zmiennej środowiskowej ALPHA_VANTAGE_API_KEY. Aplikacja nie może wystartować.")

# Tworzymy jedną, globalną instancję DataFetcher, która będzie używana w całej aplikacji
data_fetcher = DataFetcher(api_key=api_key)

# Tworzymy jedną, globalną instancję PortfolioManager, przekazując mu fetcher
portfolio_manager = PortfolioManager(fetcher=data_fetcher)

# Inicjalizujemy aplikację FastAPI
app = FastAPI(
    title="Analizator Giełdowy Nasdaq API",
    description="Silnik analityczny dla aplikacji Guru Analizator Akcji Nasdaq",
    version="2.0.0"
)

# Konfiguracja CORS, aby umożliwić komunikację z interfejsem użytkownika
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # W produkcji warto ograniczyć do konkretnej domeny
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- KROK 2: IMPLEMENTACJA WSZYSTKICH ENDPOINTÓW API ---

@app.get("/api/macro_climate", summary="Pobiera analizę makroekonomiczną 'Sokoła'")
async def api_get_macro_climate():
    """Zwraca ocenę klimatu rynkowego na podstawie rzeczywistych wskaźników."""
    return get_macro_climate_analysis(data_fetcher)

@app.get("/api/portfolio_risk", summary="Pobiera analizę ryzyka portfela 'Cerbera'")
async def api_get_portfolio_risk():
    """Pobiera dane historyczne dla spółek w portfelu i oblicza ich korelację."""
    tickers = portfolio_manager._dream_team_tickers
    if len(tickers) < 2:
        return {
            "level": "Brak Danych", "correlation": 0, "color": "text-gray-400",
            "summary": "Portfel musi zawierać co najmniej 2 spółki do analizy ryzyka."
        }
        
    portfolio_data: Dict[str, pd.DataFrame] = {}
    for ticker in tickers:
        historical_data = data_fetcher.get_data({"function": "TIME_SERIES_DAILY", "symbol": ticker, "outputsize": "compact"})
        df = transform_to_dataframe(historical_data)
        if df is not None:
            portfolio_data[ticker] = df
    
    if len(portfolio_data) < 2:
         return {
            "level": "Błąd Danych", "correlation": 0, "color": "text-yellow-400",
            "summary": "Nie udało się pobrać wystarczających danych do analizy korelacji."
        }

    return analyze_portfolio_risk(portfolio_data)

@app.get("/api/full_analysis/{ticker}", summary="Pobiera pełną analizę dla jednej spółki")
async def api_full_analysis(ticker: str):
    """Pobiera dane ogólne, aktualne notowania i generuje prostą rekomendację AI."""
    overview_data = data_fetcher.get_data({"function": "OVERVIEW", "symbol": ticker})
    quote_data_raw = data_fetcher.get_data({"function": "GLOBAL_QUOTE", "symbol": ticker})
    
    if not overview_data or not quote_data_raw or "Global Quote" not in quote_data_raw:
        raise HTTPException(status_code=404, detail=f"Nie można było pobrać pełnych danych dla {ticker}")

    quote_data = quote_data_raw["Global Quote"]
    
    try:
        price = float(quote_data.get("05. price", 0))
        change = float(quote_data.get("09. change", 0))
        change_percent_str = quote_data.get("10. change percent", "0%").replace('%', '')
        change_percent = float(change_percent_str)
        pe_ratio = float(overview_data.get("PERatio", 0))
    except (ValueError, TypeError):
         raise HTTPException(status_code=500, detail=f"Błąd przetwarzania danych dla {ticker}")
    
    # Prosta logika "AI Summary"
    recommendation = "Neutralna Rekomendacja"
    justification = "Spółka o stabilnych wskaźnikach."
    if pe_ratio > 0 and pe_ratio < 20:
        recommendation = "Potencjał Wartościowy (Kupuj)"
        justification = "Atrakcyjna wycena (niski wskaźnik C/Z) sugeruje potencjał wzrostowy."
    elif change_percent > 3:
        recommendation = "Silny Impuls Wzrostowy (Obserwuj)"
        justification = "Znaczący wzrost ceny wskazuje na duże zainteresowanie rynku."

    return {
        "overview": {
            "name": overview_data.get("Name", ticker),
            "price": price,
            "change": change,
            "changePercent": change_percent
        },
        "aiSummary": {
            "recommendation": recommendation,
            "justification": justification
        }
    }

@app.get("/api/portfolio/dream_team", summary="Pobiera listę spółek 'Dream Team' z aktualnymi cenami")
async def api_get_dream_team():
    """Zwraca dynamicznie aktualizowaną listę spółek z portfela."""
    return portfolio_manager.get_dream_team()

@app.get("/api/run_revolution", summary="Uruchamia skanowanie rynku 'Rewolucja AI'")
async def api_run_revolution():
    """
    Uruchamia proces selekcji Fazy 1: skanuje rynek w poszukiwaniu spółek
    o cenie poniżej 5 USD, a następnie poddaje je analizie Agentów Selekcyjnych.
    """
    # W pełnej wersji produkcyjnej, ta lista byłaby dynamicznie pobierana z API
    # np. za pomocą funkcji LISTING_STATUS, która zwraca tysiące spółek.
    # Dla celów demonstracyjnych i wydajnościowych używamy rozszerzonej, statycznej listy.
    full_nasdaq_universe = [
        "AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "TSLA", "META", "AVGO", "COST", "ADBE", "AMD", "INTC", "QCOM", "SBUX", "PYPL", "NFLX",
        "SIRI", "PLUG", "MARA", "RIOT", "TQQQ", "SOFI", "FCEL", "CLSK", "ITUB", "RUN", "WBD", "OPEN", "NKLA", "CHPT", "TLRY", "RIVN"
    ]
    
    print(f"INFO: Rozpoczynanie Fazy 1 Rewolucji AI dla {len(full_nasdaq_universe)} spółek.")
    
    # Krok 1: Filtrowanie wstępne - znajdź spółki poniżej 5 USD
    cheap_stocks: List[str] = []
    print("INFO: Filtrowanie spółek o cenie poniżej 5 USD...")
    for ticker in full_nasdaq_universe:
        quote_data_raw = data_fetcher.get_data({"function": "GLOBAL_QUOTE", "symbol": ticker})
        if quote_data_raw and "Global Quote" in quote_data_raw:
            try:
                price = float(quote_data_raw["Global Quote"].get("05. price", 999))
                if price < 5.0:
                    cheap_stocks.append(ticker)
            except (ValueError, TypeError):
                continue # Pomiń spółki z błędnymi danymi

    print(f"INFO: Znaleziono {len(cheap_stocks)} spółek poniżej 5 USD: {cheap_stocks}")

    if not cheap_stocks:
         return {"message": "Nie znaleziono żadnych spółek spełniających kryterium cenowe < 5 USD.", "candidates": []}

    # Krok 2: Uruchom właściwy skan Agentów Selekcyjnych na odfiltrowanej liście
    scan_results = run_market_scan(cheap_stocks, data_fetcher)
    
    # Krok 3: Zaktualizuj Dream Team i zwróć wyniki
    portfolio_manager.update_dream_team(scan_results['candidates'])
    return scan_results

@app.get("/api/run_backtest/{ticker}", summary="Uruchamia symulację historyczną 'Wehikuł Czasu'")
async def api_run_backtest(ticker: str):
    """Uruchamia backtesting dla wybranej spółki i zwraca wiarygodne wyniki."""
    return run_backtest_simulation(ticker, data_fetcher)


# --- KROK 3: SEKCJA URUCHOMIENIOWA ---

if __name__ == "__main__":
    # Używamy portu zdefiniowanego przez Render, z domyślnym 8000 do testów lokalnych
    port = int(os.environ.get("PORT", 8000))
    # Używamy hosta 0.0.0.0, aby aplikacja była dostępna z zewnątrz w kontenerze Render
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

