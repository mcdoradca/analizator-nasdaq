# main.py
# Główny plik "silnika" aplikacji. Uruchamia serwer API i łączy wszystkich agentów.

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import pandas as pd
import pandas_ta as ta
from typing import Dict, Any

# --- Importy Agentów i Modułów ---
from data_fetcher import DataFetcher, transform_to_dataframe
from portfolio_manager import PortfolioManager
from selection_agent import run_market_scan
from zlota_liga_agent import run_zlota_liga_analysis
from szybka_liga_agent import run_quick_league_scan
from backtesting_agent import run_backtest_for_ticker
from macro_agent import get_macro_climate_analysis, get_market_barometer
from cockpit_agent import analyze_cockpit_data
from risk_agent import analyze_single_stock_risk, run_portfolio_risk_analysis

# --- Inicjalizacja Aplikacji i Kluczowych Komponentów ---
app = FastAPI(
    title="Analizator Nasdaq API",
    description="Backend dla aplikacji analitycznej Guru Analizator Akcji Nasdaq.",
    version="3.0.0"
)

# --- KONFIGURACJA CORS ---
# Definiujemy listę zaufanych źródeł (frontend)
origins = [
    "https://analizator-nasdaq-1.onrender.com",
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1:8000", # Do testów lokalnych
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Zezwalamy na wszystkie metody (GET, POST, etc.)
    allow_headers=["*"], # Zezwalamy na wszystkie nagłówki
)


api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
if not api_key:
    raise RuntimeError("Brak klucza API! Ustaw zmienną środowiskową ALPHA_VANTAGE_API_KEY.")

data_fetcher = DataFetcher(api_key=api_key)
portfolio_manager = PortfolioManager()


# --- Endpointy API ---

@app.get("/", tags=["Status"])
def read_root():
    """Sprawdza status działania API."""
    return {"status": "API Analizatora Nasdaq działa poprawnie."}

@app.get("/api/macro_climate", tags=["Analiza Rynku"])
async def api_get_macro_climate() -> Dict[str, Any]:
    """Pobiera analizę klimatu makroekonomicznego od Agenta 'Sokół'."""
    return get_macro_climate_analysis(data_fetcher)

@app.get("/api/market_barometer", tags=["Analiza Rynku"])
async def api_get_market_barometer() -> Dict[str, Any]:
    """Pobiera analizę barometru rynku (trend na QQQ)."""
    return get_market_barometer(data_fetcher)

@app.post("/api/run_revolution", tags=["Rewolucja AI"])
async def api_run_revolution() -> Dict[str, Any]:
    """Uruchamia pełny, dwufazowy skan rynku w poszukiwaniu kandydatów do Dream Teamu."""
    scan_results = run_market_scan(data_fetcher)
    portfolio_manager.update_dream_team(scan_results['candidates_objects'])
    return scan_results

@app.get("/api/portfolio/dream_team", tags=["Portfel"])
async def api_get_dream_team() -> list:
    """Zwraca aktualną listę spółek w Dream Team."""
    return portfolio_manager.get_dream_team()

@app.get("/api/portfolio_risk", tags=["Portfel"])
async def api_get_portfolio_risk() -> Dict[str, Any]:
    """Uruchamia analizę ryzyka korelacji dla spółek z Dream Team."""
    tickers = portfolio_manager.get_dream_team_tickers()
    return run_portfolio_risk_analysis(tickers, data_fetcher)


@app.get("/api/full_analysis/{ticker}", tags=["Analiza Spółki"])
async def api_full_analysis(ticker: str) -> Dict[str, Any]:
    """
    Przeprowadza pełną analizę 360 stopni dla pojedynczej spółki.
    """
    try:
        # 1. Pobieranie surowych danych
        overview_data = data_fetcher.get_data({"function": "OVERVIEW", "symbol": ticker})
        daily_data_json = data_fetcher.get_data({"function": "TIME_SERIES_DAILY", "symbol": ticker, "outputsize": "compact"})
        
        if not overview_data or 'Name' not in overview_data or not daily_data_json or "Time Series (Daily)" not in daily_data_json:
            raise HTTPException(status_code=404, detail=f"Brak kluczowych danych dla {ticker}.")

        # 2. Przygotowanie danych do analizy
        df = transform_to_dataframe(daily_data_json)
        if df is None:
             raise HTTPException(status_code=500, detail="Błąd przetwarzania danych historycznych.")
        
        # 3. Pobranie danych rynkowych do analizy ryzyka
        market_df = transform_to_dataframe(data_fetcher.get_data({"function": "TIME_SERIES_DAILY", "symbol": "QQQ", "outputsize": "compact"}))

        # 4. Uruchamianie agentów analitycznych
        risk_analysis = analyze_single_stock_risk(df, market_df, overview_data)
        
        # 5. Przygotowanie finalnej odpowiedzi
        latest_price_data = list(daily_data_json["Time Series (Daily).items())[0][1]
        price = float(latest_price_data['4. close'])
        prev_close = float(list(daily_data_json["Time Series (Daily)"].items())[1][1]['4. close'])
        change = price - prev_close
        change_percent = (change / prev_close) * 100 if prev_close != 0 else 0

        # Proste podsumowanie AI
        ai_summary = {
            "recommendation": "Obserwuj",
            "justification": f"Spółka {overview_data.get('Name')} wykazuje {risk_analysis['riskLevel']} poziom ryzyka. Zalecana dalsza obserwacja."
        }
        if risk_analysis['riskLevel'] == 'Niskie' and change > 0:
            ai_summary['recommendation'] = "Rozważ Pozycję"
        
        return {
            "overview": {
                "symbol": overview_data.get("Symbol"),
                "name": overview_data.get("Name"),
                "sector": overview_data.get("Sector"),
                "price": price,
                "change": change,
                "changePercent": change_percent
            },
            "daily": daily_data_json,
            "risk": risk_analysis,
            "aiSummary": ai_summary
        }
    except Exception as e:
        print(f"[Full Analysis ERROR] for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/run_backtest/{ticker}", tags=["Backtesting"])
async def api_run_backtest(ticker: str) -> Dict[str, Any]:
    """Uruchamia symulację historyczną (backtest) dla wybranego tickera."""
    if not ticker:
        raise HTTPException(status_code=400, detail="Nie podano tickera.")
    
    results = run_backtest_for_ticker(ticker, 365, data_fetcher) # Okres 1 roku
    
    total_pnl = sum(trade['pnl'] for trade in results)
    trade_count = len(results)

    return {
        "ticker": ticker,
        "total_pnl": total_pnl,
        "trade_count": trade_count,
        "trades": results
    }

# --- Uruchomienie Serwera ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

