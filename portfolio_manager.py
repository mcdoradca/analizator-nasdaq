
"""
Moduł Menedżera Portfela.
Odpowiedzialność: Zarządzanie stanem portfela użytkownika.
"""
from typing import List, Dict, Any
from src.data_fetcher import data_fetcher

class PortfolioManager:
    def __init__(self):
        """
        Inicjalizuje menedżera z przykładowym portfelem.
        W rzeczywistości portfel powinien być ładowany z bazy danych.
        """
        self._dream_team = [
            {"ticker": "AAPL", "status": "W formie", "aiScore": 82},
            {"ticker": "MSFT", "status": "Stabilny", "aiScore": 65},
            {"ticker": "TSLA", "status": "Gwiazda Zespołu", "aiScore": 91},
        ]
        print("[PortfolioManager] Zainicjalizowany z przykładowym Dream Teamem")

    def _fetch_current_price(self, ticker: str) -> Dict[str, Any]:
        """Pobiera aktualną cenę i zmianę dla danego tickera."""
        if not data_fetcher:
            return {"currentPrice": 0.0, "changePercent": 0.0}

        quote_data = data_fetcher.get_data({"function": "GLOBAL_QUOTE", "symbol": ticker})
        if not quote_data or "Global Quote" not in quote_data:
            print(f"WARNING: Nie udało się pobrać ceny dla {ticker}")
            return {"currentPrice": 0.0, "changePercent": 0.0}

        try:
            quote = quote_data["Global Quote"]
            current_price = float(quote["05. price"])
            change_percent = float(quote["10. change percent"].strip('%'))
            return {"currentPrice": current_price, "changePercent": change_percent}
        except (KeyError, ValueError) as e:
            print(f"ERROR: Błąd parsowania ceny dla {ticker}: {e}")
            return {"currentPrice": 0.0, "changePercent": 0.0}

    def get_dream_team(self) -> List[Dict[str, Any]]:
        """
        Zwraca listę spółek z "Dream Teamu" z AKTUALNYMI cenami.
        """
        print("[PortfolioManager] Aktualizowanie Dream Teamu...")
        updated_team = []

        for stock in self._dream_team:
            ticker = stock["ticker"]
            price_data = self._fetch_current_price(ticker)
            
            updated_stock = {
                "ticker": stock["ticker"],
                "status": stock["status"],
                "aiScore": stock["aiScore"],
                "currentPrice": price_data["currentPrice"],
                "changePercent": price_data["changePercent"]
            }
            updated_team.append(updated_stock)

        print(f"[PortfolioManager] Zwrócono zaktualizowany Dream Team ({len(updated_team)} spółek)")
        return updated_team

    def update_dream_team(self, new_candidates_tickers: List[str]) -> List[Dict[str, Any]]:
        """
        Aktualizuje Dream Team na podstawie wyników skanowania.
        """
        print(f"[PortfolioManager] Aktualizowanie Dream Teamu nowymi kandydatami: {new_candidates_tickers}")
        
        new_team = []
        for ticker in new_candidates_tickers:
            price_data = self._fetch_current_price(ticker)
            new_team.append({
                "ticker": ticker,
                "status": "Nowy Kandydat",
                "aiScore": 50,  # Domyślny wynik dla nowych kandydatów
                "currentPrice": price_data["currentPrice"],
                "changePercent": price_data["changePercent"]
            })

        self._dream_team = new_team
        print(f"[PortfolioManager] Dream Team zaktualizowany. Nowi kandydaci: {new_candidates_tickers}")
        return self._dream_team

# Tworzymy jedną, globalną instancję menedżera
portfolio_manager = PortfolioManager()
