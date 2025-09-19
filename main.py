# main.py
# Główny plik "silnika" aplikacji. Uruchamia serwer API i łączy wszystkich agentów.

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import pandas as pd
import pandas_ta as ta
from typing import Dict, Any, List
import time

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
    version="3.0.1"
)

# --- OSTATECZNA KONFIGURACJA CORS ---
origins = [
    "https://analizator-nasdaq-1.onrender.com",
    "https://analizator-nasdaq.onrender.com",
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST","OPTIONS"],
    allow_headers=["*"],
)

api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
if not api_key:
    raise RuntimeError("Brak klucza API! Ustaw zmienną środowiskową ALPHA_VANTAGE_API_KEY.")

data_fetcher = DataFetcher(api_key=api_key)
portfolio_manager = PortfolioManager()

# --- Endpointy API ---

@app.get("/", tags=["Status"])
def read_root():
    return {"status": "API Analizatora Nasdaq działa poprawnie."}

@app.get("/api/macro_climate", tags=["Analiza Rynku"])
async def api_get_macro_climate() -> Dict[str, Any]:
    return get_macro_climate_analysis(data_fetcher)

@app.get("/api/market_barometer", tags=["Analiza Rynku"])
async def api_get_market_barometer() -> Dict[str, Any]:
    return get_market_barometer(data_fetcher)

import time  # Dodaj ten import na górze pliku z innymi importami

@app.post("/api/run_revolution", tags=["Rewolucja AI"])
@app.options("/api/run_revolution")
async def api_run_revolution() -> Dict[str, Any]:
    start_time = time.time()
    print(f"[REVOLUTION] Rozpoczynanie market scan... {start_time}")
    
    scan_results = run_market_scan(data_fetcher)
    
    scan_time = time.time() - start_time
    print(f"[REVOLUTION] Market scan zakończony w {scan_time:.2f}s")
    
    if 'candidates_objects' in scan_results:
        portfolio_manager.update_dream_team(scan_results['candidates_objects'])
        print(f"[REVOLUTION] Dream team zaktualizowany")
    
    total_time = time.time() - start_time
    print(f"[REVOLUTION] Cała operacja zakończona w {total_time:.2f}s")
    
    return scan_results
    
@app.get("/api/portfolio/dream_team", tags=["Portfel"])
async def api_get_dream_team() -> list:
    return portfolio_manager.get_dream_team()

@app.get("/api/portfolio_risk", tags=["Portfel"])
async def api_get_portfolio_risk() -> Dict[str, Any]:
    tickers = portfolio_manager.get_dream_team_tickers()
    if not tickers:
        return {"correlation": 0.0, "level": "Brak Danych", "summary": "Portfel musi zawierać min. 2 aktywa.", "color": "text-gray-400"}
    return run_portfolio_risk_analysis(tickers, data_fetcher)

@app.get("/api/full_analysis/{ticker}", tags=["Analiza Spółki"])
async def api_full_analysis(ticker: str) -> Dict[str, Any]:
    try:
        overview_data = data_fetcher.get_data({"function": "OVERVIEW", "symbol": ticker})
        daily_data_json = data_fetcher.get_data({"function": "TIME_SERIES_DAILY", "symbol": ticker, "outputsize": "compact"})
        
        if not overview_data or 'Name' not in overview_data or not daily_data_json or "Time Series (Daily)" not in daily_data_json:
            raise HTTPException(status_code=404, detail=f"Brak kluczowych danych dla {ticker}.")

        df = transform_to_dataframe(daily_data_json)
        if df is None:
             raise HTTPException(status_code=500, detail="Błąd przetwarzania danych historycznych.")
        
        market_df = transform_to_dataframe(data_fetcher.get_data({"function": "TIME_SERIES_DAILY", "symbol": "QQQ", "outputsize": "compact"}))
        risk_analysis = analyze_single_stock_risk(df, market_df, overview_data)
        
        time_series = daily_data_json["Time Series (Daily)"]
        latest_price_data = list(time_series.values())[0]
        previous_price_data = list(time_series.values())[1]

        price = float(latest_price_data['4. close'])
        prev_close = float(previous_price_data['4. close'])
        change = price - prev_close
        change_percent = (change / prev_close) * 100 if prev_close != 0 else 0
        
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
        raise HTTPException(status_code=500, detail=f"Wewnętrzny błąd serwera podczas analizy {ticker}: {e}")

@app.get("/api/run_backtest/{ticker}", tags=["Backtesting"])
async def api_run_backtest(ticker: str) -> Dict[str, Any]:
    if not ticker:
        raise HTTPException(status_code=400, detail="Nie podano tickera.")
    
    results = run_backtest_for_ticker(ticker, 365, data_fetcher)
    total_pnl = sum(trade['pnl'] for trade in results)
    
    return {
        "ticker": ticker,
        "total_pnl": total_pnl,
        "trade_count": len(results),
        "trades": results
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        timeout_keep_alive=120,  # Zwiększ timeout
        workers=1  # Użyj tylko 1 worker na free plan
    )
