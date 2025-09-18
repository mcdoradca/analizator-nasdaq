# -*- coding: utf-8 -*-
"""
Moduł do komunikacji z API Alpha Vantage.

Odpowiedzialność: Bezpieczne i wydajne pobieranie danych giełdowych,
z uwzględnieniem limitów API, buforowania oraz transformacji danych do użytecznego formatu.
"""
import requests
import os
import time
from collections import deque
import pandas as pd
from typing import Dict, Optional, Any
import json

def transform_to_dataframe(data: Dict, data_key: str = "Time Series (Daily)") -> Optional[pd.DataFrame]:
    """
    Transformuje odpowiedź JSON z Alpha Vantage do pandas.DataFrame.

    Args:
        data (Dict): Surowa odpowiedź JSON z API.
        data_key (str): Klucz w JSON, pod którym znajdują się dane szeregu czasowego.

    Returns:
        Optional[pd.DataFrame]: DataFrame z danymi lub None w przypadku błędu.
    """
    if not data or data_key not in data:
        print(f"Błąd transformacji: Brak klucza '{data_key}' w odpowiedzi API.")
        return None
    try:
        df = pd.DataFrame.from_dict(data[data_key], orient='index')
        df.index = pd.to_datetime(df.index)
        # Konwersja wszystkich kolumn numerycznych, ignorując błędy dla nienumerycznych
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='ignore')

        df.rename(columns=lambda c: c.split('. ')[1] if '. ' in c else c, inplace=True)
        df.sort_index(ascending=True, inplace=True)
        return df
    except Exception as e:
        print(f"Wystąpił błąd podczas konwersji danych do DataFrame: {e}")
        return None

class DataFetcher:
    def __init__(self, api_key: str, cache_duration_seconds: int = 14400): # 4 godziny cache
        if not api_key:
            raise ValueError("Klucz API jest wymagany.")
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.api_call_timestamps = deque()
        self.requests_per_minute = 75 # Zgodnie z wymaganiami premium API
        self.cache: Dict[str, Any] = {}
        self.cache_duration = cache_duration_seconds

    def _wait_if_needed(self):
        """Inteligentnie zarządza częstotliwością zapytań, aby nie przekroczyć limitu."""
        while True:
            now = time.time()
            # Usuń znaczniki czasu starsze niż minuta
            while self.api_call_timestamps and self.api_call_timestamps[0] <= now - 60:
                self.api_call_timestamps.popleft()

            if len(self.api_call_timestamps) < self.requests_per_minute:
                break
            
            time_to_wait = 60 - (now - self.api_call_timestamps[0]) + 1
            print(f"INFO: Osiągnięto limit API. Czekam {time_to_wait:.2f}s...")
            time.sleep(time_to_wait)

    def get_data(self, params: dict, retries: int = 3) -> Optional[dict]:
        """
        Wykonuje zapytanie do API Alpha Vantage z obsługą cache'a i ponowień.

        Args:
            params (dict): Parametry zapytania (np. {"function": "OVERVIEW", "symbol": "AAPL"}).
            retries (int): Liczba prób ponowienia zapytania.

        Returns:
            Optional[dict]: Słownik z danymi JSON lub None w przypadku błędu.
        """
        # Generowanie unikalnego klucza dla cache na podstawie parametrów
        cache_key = json.dumps(params, sort_keys=True)
        
        # Sprawdzenie, czy dane są w cache i czy nie są przestarzałe
        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_duration:
                print(f"INFO: Zwracam dane z cache dla {params.get('function', 'N/A')}, symbol: {params.get('symbol', 'N/A')}")
                return data

        all_params = {"apikey": self.api_key, **params}
        
        for attempt in range(retries):
            self._wait_if_needed()
            
            print(f"INFO: Wykonuję zapytanie do API (próba {attempt + 1}/{retries}) dla: {params.get('function', 'N/A')}, symbol: {params.get('symbol', 'N/A')}")
            
            try:
                response = requests.get(self.base_url, params=all_params, timeout=15)
                response.raise_for_status()

                # Obsługa LISTING_STATUS, który zwraca CSV a nie JSON
                if params.get("function") == "LISTING_STATUS":
                    # Zwracamy surowy tekst, aby moduł wywołujący mógł go przetworzyć
                    # W przyszłości można to zunifikować, ale na razie trzymamy się logiki z selection_agent
                    self.api_call_timestamps.append(time.time())
                    # Cache'ujemy surowy tekst CSV
                    self.cache[cache_key] = (response.text, time.time())
                    return {"csv_data": response.text} # Zwracamy w formie słownika dla spójności

                data = response.json()
                self.api_call_timestamps.append(time.time())

                if "Error Message" in data:
                    print(f"BŁĄD: Otrzymano błąd z API: {data['Error Message']}")
                    return None
                if "Information" in data:
                    print(f"INFO: Otrzymano informację z API (prawdopodobnie limit): {data['Information']}. Ponawiam próbę...")
                    time.sleep(5) # Krótka przerwa przed ponowieniem
                    continue

                # Zapisanie pomyślnej odpowiedzi w cache
                self.cache[cache_key] = (data, time.time())
                return data

            except requests.exceptions.RequestException as e:
                print(f"BŁĄD: Błąd sieciowy (próba {attempt + 1}/{retries}): {e}")
                time.sleep(2 ** attempt) # Exponential backoff
            except ValueError:
                print(f"BŁĄD: Nie udało się zdekodować odpowiedzi JSON (próba {attempt + 1}/{retries}).")
                return None
        
        print(f"BŁĄD: Nie udało się pobrać danych dla {params} po {retries} próbach.")
        return None
