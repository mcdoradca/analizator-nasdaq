# -*- coding: utf-8 -*-
"""
Moduł do komunikacji z API Alpha Vantage.

Odpowiedzialność: Bezpieczne i wydajne pobieranie danych giełdowych,
z uwzględnieniem limitów API oraz transformacja danych do użytecznego formatu.
"""
import requests
import os
import time
from collections import deque
import pandas as pd
from typing import Dict, Optional, Any

# --- Cache ---
# Prosty cache w pamięci z czasem wygaśnięcia
_cache: Dict[str, Any] = {}
CACHE_DURATION = 4 * 60 * 60  # 4 godziny

def transform_to_dataframe(data: Dict, data_key: str = "Time Series (Daily)") -> Optional[pd.DataFrame]:
    if not data or not isinstance(data, dict) or data_key not in data:
        print(f"Błąd transformacji: Brak klucza '{data_key}' lub nieprawidłowy format danych.")
        return None
    try:
        df = pd.DataFrame.from_dict(data[data_key], orient='index')
        df.index = pd.to_datetime(df.index)
        df = df.apply(pd.to_numeric)
        df.rename(columns={
            '1. open': 'open', '2. high': 'high', '3. low': 'low', '4. close': 'close', '5. volume': 'volume'
        }, inplace=True)
        df.sort_index(ascending=True, inplace=True)
        return df
    except Exception as e:
        print(f"Wystąpił błąd podczas konwersji danych do DataFrame: {e}")
        return None

class DataFetcher:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Klucz API jest wymagany.")
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.api_call_timestamps = deque()
        self.requests_per_minute = 75
        self.retry_attempts = 3
        self.retry_delay = 5  # sekundy

    def _wait_if_needed(self):
        now = time.time()
        while self.api_call_timestamps and self.api_call_timestamps[0] <= now - 60:
            self.api_call_timestamps.popleft()
        if len(self.api_call_timestamps) >= self.requests_per_minute:
            time_to_wait = 60 - (now - self.api_call_timestamps[0]) + 1
            print(f"INFO: Osiągnięto limit API. Czekam {time_to_wait:.2f}s...")
            time.sleep(time_to_wait)

    def get_data(self, params: dict) -> Optional[Any]:
        cache_key = frozenset(params.items())
        now = time.time()
        if cache_key in _cache and (now - _cache[cache_key]['timestamp']) < CACHE_DURATION:
            print(f"INFO: Zwracam dane z cache dla: {params.get('function')}, {params.get('symbol', '')}")
            return _cache[cache_key]['data']

        self._wait_if_needed()
        all_params = {"apikey": self.api_key, **params}
        
        for attempt in range(self.retry_attempts):
            try:
                print(f"INFO: Wykonuję zapytanie do API dla funkcji: {params.get('function', 'N/A')}, symbol: {params.get('symbol', 'N/A')}")
                response = requests.get(self.base_url, params=all_params, timeout=20)
                response.raise_for_status()
                
                self.api_call_timestamps.append(time.time())

                # --- KLUCZOWA POPRAWKA: Obsługa CSV i JSON ---
                content_type = response.headers.get('Content-Type', '')
                if 'csv' in content_type:
                    data = response.text
                else:
                    data = response.json()
                
                if isinstance(data, dict):
                    if "Error Message" in data:
                        print(f"BŁĄD API: {data['Error Message']}")
                        return None
                    if "Information" in data:
                        print(f"INFO API: {data['Information']}")
                        time.sleep(self.retry_delay) # Czekamy, bo to może być informacja o limicie
                        continue
                
                _cache[cache_key] = {'data': data, 'timestamp': now}
                return data

            except requests.exceptions.RequestException as e:
                print(f"BŁĄD: Błąd sieciowy (próba {attempt + 1}/{self.retry_attempts}): {e}")
                time.sleep(self.retry_delay * (attempt + 1))
            except ValueError:
                print("BŁĄD: Nie udało się zdekodować odpowiedzi JSON z API.")
                return None
        
        return None

