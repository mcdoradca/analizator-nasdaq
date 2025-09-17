# main.py
# Główny plik "silnika" aplikacji. Uruchamia serwer API.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

# --- PRAWIDŁOWE IMPORTY ---
from macro_agent import get_macro_climate_analysis
# Poprawiona nazwa funkcji!
from risk_agent import analyze_portfolio_risk as get_portfolio_risk_analysis
from selection_agent import run_market_scan
from backtesting_agent import run_backtest_simulation
from portfolio_manager import portfolio_manager
# Importujemy KLASĘ, a nie obiekt
from data_fetcher import DataFetcher

# --- PRAWIDŁOWE TWORZENIE OBIEKTU DATA FETCHER ---
# Pobieramy klucz API ze zmiennej środowiskowej.
# Musisz ustawić tę zmienną w Google Cloud!
api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
if not api_key:
    print("OSTRZEŻENIE: Brak zmiennej środowiskowej ALPHA_VANTAGE_API_KEY.")
    # Możesz tu wstawić klucz domyślny do testów, ale nie jest to zalecane
    # api_key = "TWOJ_KLUCZ_API"

# Tworzymy instancję DataFetcher
data_fetcher = DataFetcher(api_key=api_key)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Endpointy (bez zmian, ale teraz powinny działać) ---

@app.get("/api/macro_climate")
async def api_get_macro_climate():
    return get_macro_climate_analysis()

@app.get("/api/portfolio_risk")
async def api_get_portfolio_risk():
    tickers = [item['ticker'] for item in portfolio_manager.get_dream_team()]
    # Ta funkcja wymagałaby pobrania danych historycznych dla każdego tickera
    # W tej wersji demonstracyjnej symuluje działanie, przekazując tylko tickery
    # W przyszłości trzeba by tu pobrać dane i przekazać słownik jak w risk_agent
    return get_portfolio_risk_analysis(tickers) # Symulowane wywołanie

@app.get("/api/full_analysis/{ticker}")
async def api_full_analysis(ticker: str):
    overview_data = data_fetcher.get_data({"function": "OVERVIEW", "symbol": ticker})
    if not overview_data:
        # Zwracamy błąd lub domyślny obiekt, żeby frontend się nie zepsuł
        return {"error": "Could not fetch data"}

    return {
        "overview": {
            "name": overview_data.get("Name", f"{ticker} Inc."),
            "price": 150.75, # Dane symulowane
            "change": 2.5,
            "changePercent": 1.68
        },
        "aiSummary": {
            "recommendation": "Potencjał Wzrostowy (Kupuj)",
            "justification": "Analiza wskazuje na pozytywne sygnały."
        }
    }

@app.get("/api/portfolio/dream_team")
async def api_get_dream_team():
    return portfolio_manager.get_dream_team()

@app.get("/api/run_revolution")
async def api_run_revolution():
    example_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"]
    scan_results = run_market_scan(example_tickers)
    portfolio_manager.update_dream_team(scan_results['candidates'])
    return scan_results

@app.get("/api/run_backtest/{ticker}")
async def api_run_backtest(ticker: str):
    return run_backtest_simulation(ticker)

# Kluczowa sekcja do uruchomienia serwera
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)