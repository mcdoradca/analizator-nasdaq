
"""
Główny plik aplikacji FastAPI.
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Import naszych modułów
from src.data_fetcher import DataFetcher, data_fetcher
from src.analysis.macro_agent import get_macro_climate_analysis
from src.analysis.selection_agent import run_market_scan
from src.analysis.backtesting_agent import run_backtest_simulation
from src.analysis.risk_agent import analyze_portfolio_risk
from src.portfolio_manager import portfolio_manager

# --- INICJALIZACJA APLIKACJI ---
app = FastAPI(title="Guru Analizator Akcji Nasdaq", version="1.0")

# Konfiguracja CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # W produkcji zastąp konkretnymi domenami
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- INICJALIZACJA DATA FETCHER ---
try:
    print("INFO: Próba odczytania klucza ALPHA_VANTAGE_API_KEY...")
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    
    if not api_key:
        raise ValueError("Błąd: Zmienna środowiskowa ALPHA_VANTAGE_API_KEY nie jest ustawiona!")
    
    print(f"INFO: Znaleziono klucz API: {api_key[:8]}...")
    data_fetcher = DataFetcher(api_key=api_key)
    print("INFO: DataFetcher zainicjalizowany pomyślnie!")

except Exception as e:
    print(f"FATAL: Błąd inicjalizacji DataFetcher: {e}")
    print("Aplikacja będzie działać w trybie ograniczonym (tylko dane mockowane)")
    data_fetcher = None

# --- ENDPOINTY API ---
@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "OK", "message": "Guru Analizator Akcji Nasdaq API is running"}

@app.get("/api/macro_climate")
async def api_macro_climate():
    """Pobiera analizę klimatu makroekonomicznego."""
    try:
        analysis = get_macro_climate_analysis()
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd analizy makro: {str(e)}")

@app.get("/api/portfolio/dream_team")
async def api_get_dream_team():
    """Pobiera aktualny Dream Team z cenami."""
    try:
        team = portfolio_manager.get_dream_team()
        return team
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd pobierania Dream Team: {str(e)}")

@app.get("/api/run_revolution")
async def api_run_revolution():
    """Uruchamia skanowanie rynku (Rewolucja AI)."""
    try:
        # Tutaj powinna być prawdziwa lista tickerów z Nasdaq
        # Na razie używamy przykładowej listy
        sample_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX"]
        result = run_market_scan(sample_tickers)
        
        # Zaktualizuj Dream Team jeśli znaleziono kandydatów
        if result["candidates"]:
            portfolio_manager.update_dream_team(result["candidates"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd skanowania rynku: {str(e)}")

@app.get("/api/run_backtest/{ticker}")
async def api_run_backtest(ticker: str):
    """Uruchamia backtest dla podanego tickera."""
    try:
        result = run_backtest_simulation(ticker)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd backtestu: {str(e)}")

@app.get("/api/portfolio_risk")
async def api_portfolio_risk():
    """Analizuje ryzyko bieżącego portfela."""
    try:
        # Pobierz tickery z Dream Teamu
        dream_team = portfolio_manager.get_dream_team()
        tickers = [stock["ticker"] for stock in dream_team]
        
        # Przeprowadź analizę ryzyka
        risk_analysis = analyze_portfolio_risk(tickers)
        return risk_analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd analizy ryzyka: {str(e)}")

# --- SERWOWANIE PLIKÓW STATYCZNYCH (Frontend) ---
@app.get("/frontend")
async def serve_frontend():
    """Serwuje główny interfejs użytkownika."""
    return FileResponse("index.html")

# Możesz też dodać obsługę statycznych plików jeśli masz więcej assetów
# app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
