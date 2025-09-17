
"""
Moduł do komunikacji z API Alpha Vantage.
Odpowiedzialność: Bezpieczne i wydajne pobieranie danych giełdowych,
z uwzględnieniem limitów API.
"""
import requests
import os
import time
from collections import deque
from typing import Dict, Any, Optional

class DataFetcher:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Klucz API jest wymagany.")
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.api_call_timestamps = deque()
        self.requests_per_minute = 75  # Limit dla klucza premium
        print(f"INFO: DataFetcher zainicjalizowany z kluczem: {api_key[:5]}...")

    def _wait_if_needed(self):
        """Inteligentnie zarządza częstotliwością zapytań."""
        now = time.time()
        # Usuń znaczniki starsze niż minuta
        while self.api_call_timestamps and self.api_call_timestamps[0] <= now - 60:
            self.api_call_timestamps.popleft()

        if len(self.api_call_timestamps) >= self.requests_per_minute:
            time_to_wait = 60 - (now - self.api_call_timestamps[0])
            print(f"INFO: Osiągnięto limit API. Czekam {time_to_wait:.2f}s...")
            time.sleep(time_to_wait + 0.1)  # Dodajemy margines błędu

    def get_data(self, params: dict) -> Optional[Dict[str, Any]]:
        """
        Wykonuje zapytanie do API Alpha Vantage.
        """
        self._wait_if_needed()

        all_params = {"apikey": self.api_key, **params}
        function_name = params.get("function", "UNKNOWN")

        try:
            print(f"DEBUG: Wywołanie API funkcja '{function_name}', parametry: { {k: v for k, v in all_params.items() if k != 'apikey'} }")
            response = requests.get(self.base_url, params=all_params, timeout=10)
            response.raise_for_status()  # Rzuca wyjątek dla błędów HTTP 4xx/5xx

            self.api_call_timestamps.append(time.time())

            data = response.json()

            # Sprawdź typowe komunikaty o błędach z Alpha Vantage
            if "Error Message" in data:
                error_msg = data["Error Message"]
                print(f"ERROR: Błąd API dla {function_name}: {error_msg}")
                return None
            if "Information" in data:
                info_msg = data["Information"]
                print(f"INFO: Informacja z API: {info_msg}")
                return None
            if "Note" in data and "rate limit" in data["Note"].lower():
                print(f"WARNING: Ostrzeżenie o limicie: {data['Note']}")
                # Czekamy chwilę i możemy spróbować ponownie lub odrzucić
                time.sleep(2)
                return None

            print(f"DEBUG: Pobrano pomyślnie dane dla '{function_name}'")
            return data

        except requests.exceptions.Timeout:
            print(f"ERROR: Timeout dla zapytania {function_name}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Błąd sieciowy dla {function_name}: {e}")
            return None
        except ValueError as e:
            print(f"ERROR: Błąd dekodowania JSON dla {function_name}: {e}")
            return None

# Globalna instancja, która będzie używana w całej aplikacji
# Zostanie zainicjalizowana w main.py
data_fetcher = None
