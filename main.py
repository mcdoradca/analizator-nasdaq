# main.py
# Główny plik "silnika" aplikacji. Uruchamia serwer API i łączy wszystkich agentów.

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import pandas_ta as ta
from pantic import BaseModel
from typing import List, Dict, Any, Optional

# --- Importy Agentów i Modułów ---
from data_fetcher import DataFetcher, transform_to_dataframe
from portfolio_manager import PortfolioManager
from selection_agent import run_market_scan
from zlota_liga_agent import run_golden_league_analysis
# UWAGA: Zmieniamy import, aby mieć dostęp do poszczególnych agentów
from szybka_liga_agent import run_quick_league_scan, agent_sygnalu, agent_potwierdzenia, agent_historyczny
from backtesting_agent import run_backtest
from macro_agent import get_macro_climate_analysis, get_market_barometer
from cockpit_agent import analyze_cockpit_data
from risk_agent import analyze_single_stock_risk

# --- Struktury Danych (Modele Pydantic) ---
class PositionPayload(BaseModel):
    ticker: str
    quantity: int
    entryPrice: float
    targetPrice: float
    stopLossPrice: float
    reason: Optional[str] = None

class ClosePositionPayload(BaseModel):
    id: str
    closePrice: float

# --- Inicjalizacja Aplikacji i Kluczowych Komponentów ---
app = FastAPI(title="Analizator Nasdaq API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
if not api_key:
    raise RuntimeError("Brak klucza API! Ustaw zmienną środowiskową ALPHA_VANTAGE_API_KEY.")

data_fetcher = DataFetcher(api_key=api_key)
portfolio_manager = PortfolioManager()

# --- Endpointy API ---

@app.get("/")
def read_root():
    return {"status": "API Analizatora Nasdaq działa poprawnie."}

@app.get("/api/macro_climate")
async def api_get_macro_climate():
    return get_macro_climate_analysis(data_fetcher)

@app.get("/api/market_barometer")
async def api_get_market_barometer():
    return get_market_barometer(data_fetcher)

@app.post("/api/run_revolution")
async def api_run_revolution():
    scan_results = run_market_scan(data_fetcher)
    portfolio_manager.update_dream_team(scan_results['candidates'])
    return scan_results

@app.get("/api/scan_quick_league")
async def api_scan_quick_league():
    tickers = portfolio_manager.get_dream_team_tickers()
    if not tickers: return []
    return run_quick_league_scan(tickers, data_fetcher)

@app.get("/api/analyze_golden_league")
async def api_analyze_golden_league():
    tickers = portfolio_manager.get_dream_team_tickers()
    if not tickers: return []
    return run_golden_league_analysis(tickers, data_fetcher)

@app.get("/api/cockpit_data")
async def api_get_cockpit_data():
    return analyze_cockpit_data(portfolio_manager.get_closed_positions())

@app.get("/api/portfolio_state")
async def api_get_portfolio_state():
    return portfolio_manager.get_full_portfolio_state({}) # Ceny będą pobierane po stronie klienta

@app.post("/api/open_position")
async def api_open_position(payload: PositionPayload):
    pos_id = portfolio_manager.open_position(**payload.dict())
    return {"status": "success", "positionId": pos_id}

@app.post("/api/close_position")
async def api_close_position(payload: ClosePositionPayload):
    closed_pos = portfolio_manager.close_position(payload.id, payload.closePrice)
    if not closed_pos:
        raise HTTPException(status_code=404, detail="Pozycja nie znaleziona.")
    return {"status": "success", "closedPosition": closed_pos}
    
@app.get("/api/run_backtest")
async def api_run_backtest(period: int = 365, risk_level: int = 2):
    """
    Przebudowany endpoint do uruchamiania backtestu.
    Teraz przekazuje logikę agentów jako argument, aby uniknąć cyklicznych importów.
    """
    tickers = portfolio_manager.get_dream_team_tickers()
    if not tickers:
        raise HTTPException(status_code=400, detail="Dream Team jest pusty.")
    
    # Przygotowujemy słownik z logiką strategii
    strategy_logic = {
        'sygnalu': agent_sygnalu,
        'potwierdzenia': agent_potwierdzenia,
        'historyczny': agent_historyczny
    }
    
    return run_backtest(tickers, period, risk_level, data_fetcher, strategy_logic)

@app.get("/api/full_analysis/{ticker}")
async def api_full_analysis(ticker: str):
    """
    Przebudowany endpoint do pełnej analizy 360 stopni.
    Zbiera wszystkie dane, oblicza wskaźniki i zwraca kompletny pakiet analityczny.
    """
    # 1. Pobieranie surowych danych
    overview_data = data_fetcher.get_data({"function": "OVERVIEW", "symbol": ticker})
    daily_data_json = data_fetcher.get_data({"function": "TIME_SERIES_DAILY", "symbol": ticker, "outputsize": "full"})
    qqq_daily_json = data_fetcher.get_data({"function": "TIME_SERIES_DAILY", "symbol": "QQQ", "outputsize": "compact"})

    if not overview_data or not daily_data_json:
        raise HTTPException(status_code=404, detail=f"Brak kluczowych danych dla {ticker}.")

    # 2. Transformacja danych do DataFrame
    stock_df = transform_to_dataframe(daily_data_json)
    market_df = transform_to_dataframe(qqq_daily_json)
    if stock_df is None:
        raise HTTPException(status_code=500, detail="Błąd przetwarzania danych historycznych.")

    # 3. Obliczanie wskaźników technicznych za pomocą pandas-ta
    stock_df.ta.rsi(length=14, append=True)
    stock_df.ta.macd(fast=12, slow=26, signal=9, append=True)
    stock_df.ta.bbands(length=20, append=True)
    stock_df.ta.stoch(k=14, d=3, smooth_k=3, append=True)
    stock_df.ta.adx(length=14, append=True)

    # 4. Uruchamianie agentów analitycznych
    risk_analysis = analyze_single_stock_risk(stock_df, market_df, overview_data)
    
    # 5. Przygotowanie finalnej odpowiedzi
    latest_indicators = stock_df.iloc[-1].to_dict()

    return {
        "overview": overview_data,
        "daily": daily_data_json,
        "risk": risk_analysis,
        "indicators": {
            "rsi": latest_indicators.get('RSI_14'),
            "macd_line": latest_indicators.get('MACD_12_26_9'),
            "macd_signal": latest_indicators.get('MACDs_12_26_9'),
            "macd_hist": latest_indicators.get('MACDh_12_26_9'),
            "bbands_upper": latest_indicators.get('BBU_20_2.0'),
            "bbands_lower": latest_indicators.get('BBL_20_2.0'),
            "stoch_k": latest_indicators.get('STOCHk_14_3_3'),
            "stoch_d": latest_indicators.get('STOCHd_14_3_3'),
            "adx": latest_indicators.get('ADX_14')
        }
    }

# --- Uruchomienie Serwera ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

