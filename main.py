# main.py
# Główny plik "silnika" aplikacji. Uruchamia serwer API i łączy wszystkich agentów.

import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from typing import Dict, Any, List

# --- Importy Agentów i Modułów ---
from data_fetcher import DataFetcher, transform_to_dataframe
from portfolio_manager import PortfolioManager
from selection_agent import agent_listy_rynkowej, run_revolution_step
from backtesting_agent import run_backtest_for_ticker
from macro_agent import get_macro_climate_analysis, get_market_barometer
from risk_agent import analyze_single_stock_risk, run_portfolio_risk_analysis
from zlota_liga_agent import run_zlota_liga_analysis
from szybka_liga_agent import run_quick_league_scan
from cockpit_agent import analyze_cockpit_data

# --- Inicjalizacja Aplikacji ---
app = FastAPI(
    title="Analizator Nasdaq API",
    description="Backend dla aplikacji analitycznej Guru Analizator Akcji Nasdaq.",
    version="3.2.1"
)

# --- KLUCZOWA POPRAWKA: Konfiguracja CORS ---
# Definiujemy jawną listę zaufanych adresów URL.
# Render.com może używać różnych subdomen, dlatego dodajemy obie.
origins = [
    "https://analizator-nasdaq.onrender.com",
    "https://analizator-nasdaq-1.onrender.com",
    "http://localhost",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Używamy zdefiniowanej, bezpiecznej listy
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# --- Inicjalizacja Singletonów ---
api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
if not api_key:
    raise RuntimeError("Brak klucza API! Ustaw zmienną środowiskową ALPHA_VANTAGE_API_KEY.")

data_fetcher = DataFetcher(api_key=api_key)
portfolio_manager = PortfolioManager()

# --- Pętla Skanowania w Tle ---
async def revolution_background_loop():
    print("[Background] Pętla Rewolucji AI uruchomiona.")
    while True:
        state = portfolio_manager.get_revolution_state()
        if state.get("is_active"):
            run_revolution_step(portfolio_manager, data_fetcher)
        await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(revolution_background_loop())

# --- Endpointy ---
@app.get("/", tags=["Status"])
def read_root():
    return {"status": "API Analizatora Nasdaq działa poprawnie."}

@app.get("/api/macro_climate", tags=["Analiza Rynku"])
async def api_get_macro_climate():
    return get_macro_climate_analysis(data_fetcher)

@app.get("/api/market_barometer", tags=["Analiza Rynku"])
async def api_get_market_barometer():
    return get_market_barometer(data_fetcher)

@app.post("/api/revolution/start", tags=["Rewolucja AI"])
async def start_revolution_endpoint():
    state = portfolio_manager.get_revolution_state()
    if state["is_active"]:
        raise HTTPException(status_code=400, detail="Rewolucja AI jest już w toku.")
    
    # Reset stanu, jeśli skanowanie było zakończone
    if state["is_completed"]:
        portfolio_manager.reset_revolution()
        
    market_list = agent_listy_rynkowej(data_fetcher)
    if not market_list:
        raise HTTPException(status_code=500, detail="Nie udało się pobrać listy rynku z Alpha Vantage.")
    
    portfolio_manager.start_revolution(market_list)
    return {"message": "Rewolucja AI została uruchomiona w tle."}


@app.post("/api/revolution/pause", tags=["Rewolucja AI"])
async def pause_revolution_endpoint():
    portfolio_manager.pause_revolution()
    return {"message": "Rewolucja AI została wstrzymana."}

@app.get("/api/revolution/status", tags=["Rewolucja AI"])
async def get_revolution_status():
    return portfolio_manager.get_revolution_state()

@app.get("/api/portfolio/dream_team", tags=["Portfel"])
async def api_get_dream_team():
    return portfolio_manager.get_dream_team()

@app.get("/api/scan/golden_league", tags=["Ligi"])
async def api_get_golden_league():
    tickers = portfolio_manager.get_dream_team_tickers()
    if not tickers:
        return [] # Zwróć pustą listę, jeśli Dream Team jest pusty
    return run_zlota_liga_analysis(tickers, data_fetcher)

@app.get("/api/scan/quick_league", tags=["Ligi"])
async def api_get_quick_league():
    tickers = portfolio_manager.get_dream_team_tickers()
    if not tickers:
        return [] # Zwróć pustą listę, jeśli Dream Team jest pusty
    return run_quick_league_scan(tickers, data_fetcher)

@app.get("/api/full_analysis/{ticker}", tags=["Analiza Spółki"])
async def api_full_analysis(ticker: str):
    try:
        overview_data = data_fetcher.get_data({"function": "OVERVIEW", "symbol": ticker})
        daily_data_json = data_fetcher.get_data({"function": "TIME_SERIES_DAILY", "symbol": ticker, "outputsize": "compact"})
        if not overview_data or 'Name' not in overview_data or not daily_data_json or 'Time Series (Daily)' not in daily_data_json:
            raise HTTPException(status_code=404, detail=f"Brak kompletnych danych dla {ticker}.")
        df = transform_to_dataframe(daily_data_json)
        market_df_json = data_fetcher.get_data({"function": "TIME_SERIES_DAILY", "symbol": "QQQ", "outputsize": "compact"})
        market_df = transform_to_dataframe(market_df_json)
        risk_analysis = analyze_single_stock_risk(df, market_df, overview_data)
        time_series = daily_data_json["Time Series (Daily)"]
        latest_price_data = list(time_series.values())[0]
        previous_price_data = list(time_series.values())[1]
        price = float(latest_price_data['4. close'])
        prev_close = float(previous_price_data['4. close'])
        change = price - prev_close
        change_percent = (change / prev_close) * 100 if prev_close != 0 else 0
        ai_summary = {"recommendation": "Obserwuj", "justification": f"Spółka {overview_data.get('Name')} wykazuje {risk_analysis['riskLevel']} poziom ryzyka."}
        if risk_analysis['riskLevel'] == 'Niskie' and change > 0:
            ai_summary['recommendation'] = "Rozważ Pozycję"
        return {"overview": {"symbol": overview_data.get("Symbol"),"name": overview_data.get("Name"),"sector": overview_data.get("Sector"),"price": price,"change": change,"changePercent": change_percent},"daily": daily_data_json,"risk": risk_analysis,"aiSummary": ai_summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolio_risk", tags=["Portfel"])
async def api_get_portfolio_risk():
    tickers = portfolio_manager.get_dream_team_tickers()
    if not tickers or len(tickers) < 2:
        return {"correlation": 0.0, "level": "Brak Danych", "summary": "Portfel musi zawierać min. 2 aktywa.", "color": "text-gray-400"}
    return run_portfolio_risk_analysis(tickers, data_fetcher)

@app.get("/api/run_backtest/{ticker}", tags=["Backtesting"])
async def api_run_backtest(ticker: str):
    if not ticker:
        raise HTTPException(status_code=400, detail="Nie podano tickera.")
    trades = run_backtest_for_ticker(ticker, 365, data_fetcher)
    total_pnl = sum(trade.get('pnl', 0) for trade in trades)
    return {"ticker": ticker, "total_pnl": total_pnl, "trade_count": len(trades), "trades": trades}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
