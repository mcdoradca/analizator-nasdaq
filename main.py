# main.py
# Główny plik "silnika" aplikacji. Uruchamia serwer API.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

# --- PRAWIDŁOWE IMPORTY ---
from macro_agent import get_macro_climate_analysis
from risk_agent import analyze_portfolio_risk as get_portfolio_risk_analysis
from selection_agent import run_market_scan
from backtesting_agent import run_backtest_simulation
from portfolio_manager import portfolio_manager
from data_fetcher import DataFetcher

# --- BEZPIECZNE TWORZENIE OBIEKTU DATA FETCHER ---
data_fetcher = None
try:
    print("INFO: Próba odczytania klucza ALPHA_VANTAGE_API_KEY...")
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")

    if not api_key:
        raise ValueError("FATAL: Zmienna środowiskowa ALPHA_VANTAGE_API_KEY nie jest ustawiona. Aplikacja nie może wystartować.")

    print("INFO: Klucz API odczytany. Inicjalizowanie DataFetcher...")
    data_fetcher = DataFetcher(api_key=api_key)
    print("INFO: DataFetcher zainicjalizowany pomyślnie.")

except Exception as e:
    print(f"FATAL: Krytyczny błąd podczas inicjalizacji: {e}")
    # Rzucamy wyjątek dalej, aby zatrzymać aplikację, ale już po zalogowaniu błędu.
    raise e


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Ścieżka testowa (Health Check) ---
@app.get("/")
async def root():
    """ Prosty endpoint do sprawdzania, czy API w ogóle działa. """
    return {"status": "API is running correctly"}


# --- Endpointy Aplikacji ---

@app.get("/api/macro_climate")
async def api_get_macro_climate():
    return get_macro_climate_analysis()

@app.get("/api/portfolio_risk")
async def api_get_portfolio_risk():
    tickers = [item['ticker'] for item in portfolio_manager.get_dream_team()]
    # W tej wersji symulujemy działanie, przekazując tylko tickery.
    # W przyszłości trzeba by tu pobrać dane historyczne.
    return get_portfolio_risk_analysis({"AAPL": {}, "MSFT": {}, "TSLA": {}}) # Przykładowe dane, aby uniknąć błędu

@app.get("/api/full_analysis/{ticker}")
async def api_full_analysis(ticker: str):
    # Symulujemy dane, aby uniknąć wyczerpania limitu API podczas testów
    # W docelowej wersji odkomentuj poniższą linię:
    # overview_data = data_fetcher.get_data({"function": "OVERVIEW", "symbol": ticker})
    # if not overview_data:
    #     return {"error": "Could not fetch data"}
    
    return {
        "overview": {
            "name": f"{ticker.upper()} Inc.",
            "price": 150.75,
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

# Ta sekcja jest potrzebna tylko do uruchamiania lokalnego,
# Gunicorn na Renderze jej nie używa.
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

