# main.py
# Główny plik "silnika" aplikacji. Uruchamia serwer API i łączy wszystkich agentów.

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import pandas as pd # Usunięto import pandas_ta
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# --- Importy Agentów i Modułów ---
from data_fetcher import DataFetcher, transform_to_dataframe
from portfolio_manager import PortfolioManager
# Upewniamy się, że importy są poprawne względem płaskiej struktury plików
from selection_agent import run_market_scan
from zlota_liga_agent import run_zlota_liga_analysis
from szybka_liga_agent import run_quick_league_scan
from backtesting_agent import run_backtest
from macro_agent import get_macro_climate_analysis, get_market_barometer
from cockpit_agent import run_cockpit_analysis # Poprawiono nazwę funkcji
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
    allow_origins=["*"], # W produkcji warto to ograniczyć do domeny frontendu
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
    # Zgodnie z logiką portfolio_manager, przekazujemy listę tickerów
    portfolio_manager.update_dream_team(scan_results.get('candidates', []))
    return scan_results

@app.get("/api/scan_quick_league")
async def api_scan_quick_league():
    # portfolio_manager.get_dream_team() zwraca listę słowników
    tickers = [stock['ticker'] for stock in portfolio_manager.get_dream_team()]
    if not tickers: return []
    return run_quick_league_scan(tickers, data_fetcher)

@app.get("/api/analyze_golden_league")
async def api_analyze_golden_league():
    tickers = [stock['ticker'] for stock in portfolio_manager.get_dream_team()]
    if not tickers: return []
    return run_zlota_liga_analysis(tickers, data_fetcher)

@app.get("/api/cockpit_data")
async def api_get_cockpit_data():
    return run_cockpit_analysis(portfolio_manager.get_closed_positions())

@app.get("/api/portfolio_state")
async def api_get_portfolio_state():
    return portfolio_manager.get_full_portfolio_state()

@app.post("/api/open_position")
async def api_open_position(payload: PositionPayload):
    # Pydantic v2 używa model_dump() zamiast dict()
    pos_id = portfolio_manager.open_position(**payload.model_dump())
    return {"status": "success", "positionId": pos_id}

@app.post("/api/close_position")
async def api_close_position(payload: ClosePositionPayload):
    closed_pos = portfolio_manager.close_position(payload.id, payload.closePrice)
    if not closed_pos:
        raise HTTPException(status_code=404, detail="Pozycja nie znaleziona.")
    return {"status": "success", "closedPosition": closed_pos}
    
@app.get("/api/run_backtest")
async def api_run_backtest(period_days: int = 365, risk_level: int = 2):
    tickers = [stock['ticker'] for stock in portfolio_manager.get_dream_team()]
    if not tickers:
        raise HTTPException(status_code=400, detail="Dream Team jest pusty.")
    return run_backtest(tickers, period_days, risk_level, data_fetcher)

@app.get("/api/full_analysis/{ticker}")
async def api_full_analysis(ticker: str):
    """
    Przebudowany endpoint do pełnej analizy 360 stopni.
    Zbiera wszystkie dane, oblicza wskaźniki i zwraca kompletny pakiet analityczny.
    """
    overview_data = data_fetcher.get_data({"function": "OVERVIEW", "symbol": ticker})
    daily_data_json = data_fetcher.get_data({"function": "TIME_SERIES_DAILY", "symbol": ticker, "outputsize": "full"})
    qqq_daily_json = data_fetcher.get_data({"function": "TIME_SERIES_DAILY", "symbol": "QQQ", "outputsize": "compact"})

    if not overview_data or not daily_data_json:
        raise HTTPException(status_code=404, detail=f"Brak kluczowych danych dla {ticker}.")

    stock_df = transform_to_dataframe(daily_data_json)
    market_df = transform_to_dataframe(qqq_daily_json)
    if stock_df is None or stock_df.empty:
        raise HTTPException(status_code=500, detail="Błąd przetwarzania danych historycznych.")

    # --- Obliczanie wskaźników przy użyciu PANDAS ---
    
    # 1. RSI
    delta = stock_df['close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(com=13, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(com=13, adjust=False).mean()
    rs = gain / loss
    stock_df['RSI_14'] = 100 - (100 / (1 + rs))

    # 2. MACD
    exp12 = stock_df['close'].ewm(span=12, adjust=False).mean()
    exp26 = stock_df['close'].ewm(span=26, adjust=False).mean()
    stock_df['MACD_12_26_9'] = exp12 - exp26
    stock_df['MACDs_12_26_9'] = stock_df['MACD_12_26_9'].ewm(span=9, adjust=False).mean()
    stock_df['MACDh_12_26_9'] = stock_df['MACD_12_26_9'] - stock_df['MACDs_12_26_9']

    # 3. Bollinger Bands
    sma20 = stock_df['close'].rolling(window=20).mean()
    std20 = stock_df['close'].rolling(window=20).std()
    stock_df['BBU_20_2.0'] = sma20 + (std20 * 2)
    stock_df['BBL_20_2.0'] = sma20 - (std20 * 2)

    # 4. Stochastic Oscillator
    low14 = stock_df['low'].rolling(window=14).min()
    high14 = stock_df['high'].rolling(window=14).max()
    stock_df['STOCHk_14_3_3'] = 100 * ((stock_df['close'] - low14) / (high14 - low14))
    stock_df['STOCHd_14_3_3'] = stock_df['STOCHk_14_3_3'].rolling(window=3).mean()
    
    # 5. ADX
    plus_dm = stock_df['high'].diff()
    minus_dm = stock_df['low'].diff()
    plus_dm[(plus_dm < 0) | (plus_dm <= minus_dm)] = 0
    minus_dm[(minus_dm < 0) | (minus_dm <= plus_dm)] = 0
    tr1 = pd.DataFrame(stock_df['high'] - stock_df['low'])
    tr2 = pd.DataFrame(abs(stock_df['high'] - stock_df['close'].shift(1)))
    tr3 = pd.DataFrame(abs(stock_df['low'] - stock_df['close'].shift(1)))
    tr = pd.concat([tr1, tr2, tr3], axis=1, join='inner').max(axis=1)
    atr = tr.ewm(com=13, adjust=False).mean()
    plus_di = 100 * (plus_dm.ewm(com=13, adjust=False).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(com=13, adjust=False).mean() / atr)
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.ewm(com=13, adjust=False).mean()
    stock_df['ADX_14'] = adx

    risk_analysis = analyze_single_stock_risk(stock_df, market_df, overview_data)
    
    latest_indicators = stock_df.iloc[-1].to_dict()

    return {
        "overview": overview_data,
        "daily_data_for_chart": json.loads(stock_df.reset_index().to_json(orient='records', date_format='iso')),
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
    # Render używa zmiennej PORT do określenia, na którym porcie ma nasłuchiwać aplikacja.
    port = int(os.environ.get("PORT", 8000))
    # 'reload=True' jest przydatne w dewelopmence, ale na produkcji Render może zarządzać restartami.
    # Użycie "main:app" jest standardem dla Gunicorn/Uvicorn.
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
