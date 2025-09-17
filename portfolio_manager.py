# -*- coding: utf-8 -*-
"""
Moduł Menedżera Portfela.

Odpowiedzialność: Zarządzanie stanem portfela użytkownika ("Dream Team")
i dynamiczne pobieranie aktualnych danych rynkowych dla spółek.
"""
import os
from typing import List, Dict
from data_fetcher import DataFetcher

class PortfolioManager:
    def __init__(self, fetcher: DataFetcher):
        """
        Inicjalizuje menedżera z pustym portfelem i referencją do DataFetcher.
        """
        if not fetcher:
            raise ValueError("DataFetcher jest wymagany do działania PortfolioManagera.")
        self.fetcher = fetcher
        self._dream_team_tickers: List[str] = []

    def get_dream_team(self) -> List[Dict]:
        """
        Zwraca listę spółek z "Dream Teamu" wzbogaconą o aktualne dane rynkowe.
        """
        print("[PortfolioManager] Pobieranie aktualnych danych dla Dream Team...")
        
        hydrated_team = []
        for ticker in self._dream_team_tickers:
            quote_data_raw = self.fetcher.get_data({"function": "GLOBAL_QUOTE", "symbol": ticker})
            
            price = 0.0
            change_percent = 0.0
            status = "Brak Danych"

            if quote_data_raw and "Global Quote" in quote_data_raw:
                quote_data = quote_data_raw["Global Quote"]
                try:
                    price = float(quote_data.get("05. price", 0.0))
                    change_percent_str = quote_data.get("10. change percent", "0.0%").replace('%', '')
                    change_percent = float(change_percent_str)
                    status = "Obserwowany" # Domyślny status po pobraniu danych
                except (ValueError, TypeError):
                    print(f"OSTRZEŻENIE: Nie można było przetworzyć danych dla {ticker}.")
            else:
                 print(f"OSTRZEŻENIE: Nie udało się pobrać danych GLOBAL_QUOTE dla {ticker}.")


            hydrated_team.append({
                "ticker": ticker,
                "status": status,
                "aiScore": 0, # Wartość tymczasowa, zostanie zaimplementowana w przyszłości
                "currentPrice": price,
                "changePercent": change_percent,
            })
            
        return hydrated_team

    def update_dream_team(self, new_candidates_tickers: List[str]):
        """
        Aktualizuje listę tickerów w Dream Team na podstawie wyników skanowania.
        """
        self._dream_team_tickers = new_candidates_tickers
        print(f"[PortfolioManager] Dream Team zaktualizowany. Nowi kandydaci: {new_candidates_tickers}")

# Globalna instancja zostanie utworzona i zarządzana w main.py,
# aby zapewnić jednoczesny dostęp do tej samej instancji fetchera.

# Blok testowy
if __name__ == "__main__":
    API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not API_KEY:
        print("OSTRZEŻENIE: Brak klucza ALPHA_VANTAGE_API_KEY.")
        API_KEY = "TWOJ_KLUCZ_API"
        
    data_fetcher = DataFetcher(api_key=API_KEY)
    portfolio_manager = PortfolioManager(fetcher=data_fetcher)
    
    # Symulacja wyniku z Rewolucji AI
    candidates = ["NVDA", "AMD", "GOOGL"]
    print(f"\n--- Test Menedżera Portfela dla kandydatów: {candidates} ---")
    
    portfolio_manager.update_dream_team(candidates)
    
    # Pobranie i wyświetlenie danych
    dream_team_with_data = portfolio_manager.get_dream_team()
    
    import json
    print("\nAktualne dane dla Dream Team:")
    print(json.dumps(dream_team_with_data, indent=2))
