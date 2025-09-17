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
from typing import Dict, Optional

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
        df = df.apply(pd.to_numeric)
        # Zmiana nazw kolumn, aby były bardziej czytelne
        df.rename(columns={
            '1. open': 'open',
            '2. high': 'high',
            '3. low': 'low',
            '4. close': 'close',
            '5. volume': 'volume'
        }, inplace=True)
        # Sortowanie od najstarszych do najnowszych dat
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
        # Zgodnie z wymaganiami - 75 zapytań na minutę
        self.requests_per_minute = 75

    def _wait_if_needed(self):
        """Inteligentnie zarządza częstotliwością zapytań, aby nie przekroczyć limitu."""
        now = time.time()
        # Usuń znaczniki czasu starsze niż minuta
        while self.api_call_timestamps and self.api_call_timestamps[0] <= now - 60:
            self.api_call_timestamps.popleft()

        if len(self.api_call_timestamps) >= self.requests_per_minute:
            time_to_wait = 60 - (now - self.api_call_timestamps[0]) + 1 # Dodatkowy bufor 1s
            print(f"INFO: Osiągnięto limit API. Czekam {time_to_wait:.2f}s...")
            time.sleep(time_to_wait)

    def get_data(self, params: dict) -> Optional[dict]:
        """
        Wykonuje zapytanie do API Alpha Vantage.

        Args:
            params (dict): Parametry zapytania (np. {"function": "OVERVIEW", "symbol": "AAPL"}).

        Returns:
            Optional[dict]: Słownik z danymi JSON lub None w przypadku błędu.
        """
        self._wait_if_needed()

        all_params = {"apikey": self.api_key, **params}
        print(f"INFO: Wykonuję zapytanie do API dla funkcji: {params.get('function', 'N/A')}, symbol: {params.get('symbol', 'N/A')}")

        try:
            response = requests.get(self.base_url, params=all_params)
            response.raise_for_status() # Rzuca wyjątek dla błędów HTTP 4xx/5xx

            self.api_call_timestamps.append(time.time())

            data = response.json()
            # Sprawdzanie standardowych komunikatów o błędach lub limitach z Alpha Vantage
            if "Error Message" in data:
                print(f"BŁĄD: Otrzymano błąd z API: {data['Error Message']}")
                return None
            if "Information" in data:
                # To często oznacza osiągnięcie limitu, nawet jeśli nasz manager próbował tego uniknąć
                print(f"INFO: Otrzymano informację z API: {data['Information']}")
                # Traktujemy to jako błąd, aby uniknąć przetwarzania niekompletnych danych
                return None
            return data
        except requests.exceptions.RequestException as e:
            print(f"BŁĄD: Błąd sieciowy podczas komunikacji z API: {e}")
            return None
        except ValueError:
            print("BŁĄD: Nie udało się zdekodować odpowiedzi JSON z API.")
            return None

# Przykładowe użycie i testy po modyfikacji
if __name__ == "__main__":
    # Pamiętaj, aby ustawić klucz API jako zmienną środowiskową
    API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not API_KEY:
        print("OSTRZEŻENIE: Brak klucza ALPHA_VANTAGE_API_KEY w zmiennych środowiskowych.")
        # Zastąp "TWOJ_KLUCZ_API" swoim kluczem tylko do celów testowych
        API_KEY = "TWOJ_KLUCZ_API"

    fetcher = DataFetcher(api_key=API_KEY)

    print("\n--- Test 1: Pobieranie danych OVERVIEW dla AAPL ---")
    aapl_overview = fetcher.get_data({"function": "OVERVIEW", "symbol": "AAPL"})
    if aapl_overview:
        print(f"Pobrano dane dla: {aapl_overview.get('Name')}")
        print(f"Sektor: {aapl_overview.get('Sector')}")
    else:
        print("Nie udało się pobrać danych OVERVIEW.")

    print("\n--- Test 2: Pobieranie i transformacja danych historycznych dla IBM ---")
    ibm_history_json = fetcher.get_data({"function": "TIME_SERIES_DAILY", "symbol": "IBM", "outputsize": "compact"})
    if ibm_history_json:
        ibm_df = transform_to_dataframe(ibm_history_json)
        if ibm_df is not None:
            print("Transformacja do DataFrame zakończona sukcesem.")
            print("Nagłówek danych (ostatnie 5 dni):")
            print(ibm_df.tail())
        else:
            print("Nie udało się przetworzyć danych historycznych.")
    else:
        print("Nie udało się pobrać danych historycznych dla IBM.")