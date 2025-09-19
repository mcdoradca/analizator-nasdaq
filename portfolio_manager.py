"""
Moduł Menedżera Portfela.

Odpowiedzialność: Zarządzanie stanem portfela użytkownika, w tym listą
obserwowanych spółek (Dream Team), otwartymi i zamkniętymi pozycjami oraz
stanem długotrwałych procesów, jak "Rewolucja AI".
"""

from datetime import datetime
import uuid
from typing import List, Dict, Any

class PortfolioManager:
    def __init__(self):
        """
        Inicjalizuje menedżera ze stanem portfela oraz stanem Rewolucji AI.
        """
        self._dream_team: List[Dict[str, Any]] = []
        self._open_positions: List[Dict[str, Any]] = []
        self._closed_positions: List[Dict[str, Any]] = []
        
        # NOWY BLOK: Stan procesu "Rewolucja AI"
        self._revolution_state = {
            "is_active": False,          # Czy skanowanie jest włączone
            "phase": 1,                  # Aktualna faza (1 lub 2)
            "last_scanned_index": -1,    # Indeks ostatnio skanowanego tickera z pełnej listy
            "full_market_list": [],      # Pełna lista tickerów do przeskanowania
            "phase1_candidates": [],     # Kandydaci znalezieni w Fazie 1
            "log": ["Rewolucja AI jest gotowa do startu."]
        }
        print("[PortfolioManager] Menedżer portfela został zainicjowany.")

    # --- Zarządzanie Dream Team ---

    def get_dream_team(self) -> List[Dict[str, Any]]:
        """Zwraca listę spółek z "Dream Teamu"."""
        return self._dream_team

    def get_dream_team_tickers(self) -> List[str]:
        """Zwraca listę samych tickerów z Dream Team."""
        return [stock.get('ticker', '') for stock in self._dream_team if 'ticker' in stock]

    def update_dream_team(self, new_candidates_list: List[Dict[str, Any]]):
        """Aktualizuje Dream Team na podstawie wyników skanowania Rewolucji AI."""
        self._dream_team = new_candidates_list
        tickers = [stock.get('ticker') for stock in new_candidates_list]
        print(f"[PortfolioManager] Dream Team zaktualizowany. Nowi kandydaci: {tickers}")

    # --- NOWA SEKCJA: Zarządzanie Stanem Rewolucji AI ---

    def get_revolution_state(self) -> Dict[str, Any]:
        """Zwraca aktualny stan procesu Rewolucji AI."""
        return self._revolution_state

    def start_revolution(self, full_market_list: List[str]):
        """Rozpoczyna lub wznawia proces Rewolucji AI."""
        self._revolution_state["is_active"] = True
        # Jeśli to nowy start, zresetuj wszystko
        if self._revolution_state["last_scanned_index"] == -1:
            self._revolution_state["full_market_list"] = full_market_list
            self._revolution_state["phase1_candidates"] = []
            self._revolution_state["log"] = [f"Rozpoczęto Rewolucję AI. Cel: {len(full_market_list)} spółek."]
        else:
            self._revolution_state["log"].append("Wznowiono Rewolucję AI.")
        print("[PortfolioManager] Stan Rewolucji AI: AKTYWNY.")

    def pause_revolution(self):
        """Wstrzymuje proces Rewolucji AI."""
        if self._revolution_state["is_active"]:
            self._revolution_state["is_active"] = False
            self._revolution_state["log"].append("Rewolucja AI została wstrzymana przez użytkownika.")
            print("[PortfolioManager] Stan Rewolucji AI: WSTRZYMANY.")

    def save_revolution_progress(self, last_scanned_index: int, new_candidates: List[Dict[str, Any]]):
        """Zapisuje postęp skanowania Fazy 1."""
        self._revolution_state["last_scanned_index"] = last_scanned_index
        self._revolution_state["phase1_candidates"].extend(new_candidates)
        self._revolution_state["log"].append(f"Zapisano postęp. Przeskanowano do indeksu {last_scanned_index}. Znaleziono dotąd {len(self._revolution_state['phase1_candidates'])} kandydatów.")
        print(f"[PortfolioManager] Zapisano postęp Rewolucji do indeksu: {last_scanned_index}")

    def complete_revolution(self):
        """Resetuje stan po zakończeniu całego procesu."""
        self._revolution_state = {
            "is_active": False,
            "phase": 1,
            "last_scanned_index": -1,
            "full_market_list": [],
            "phase1_candidates": [],
            "log": ["Rewolucja AI zakończona pomyślnie. Gotowa do nowego startu."]
        }
        print("[PortfolioManager] Rewolucja AI zakończona i zresetowana.")

    # --- Zarządzanie Transakcjami ---

    def open_position(self, ticker: str, quantity: int, entry_price: float, reason: str, target_price: float, stop_loss_price: float) -> Dict[str, Any]:
        """Dodaje nową otwartą pozycję."""
        position = {
            "id": str(uuid.uuid4()),
            "ticker": ticker, "quantity": quantity, "entryPrice": entry_price,
            "targetPrice": target_price, "stopLossPrice": stop_loss_price,
            "openDate": datetime.now().isoformat(), "status": "active", "reason": reason
        }
        self._open_positions.append(position)
        print(f"[PortfolioManager] Otwarto nową pozycję: {quantity} akcji {ticker} po cenie {entry_price}")
        return position

    def close_position(self, position_id: str, close_price: float) -> Dict[str, Any] | None:
        """Zamyka otwartą pozycję i przenosi ją do historii."""
        position_to_close = next((p for p in self._open_positions if p['id'] == position_id), None)
        if not position_to_close:
            print(f"[PortfolioManager] BŁĄD: Nie znaleziono otwartej pozycji o ID: {position_id}")
            return None

        self._open_positions.remove(position_to_close)
        
        pnl = (close_price - position_to_close['entryPrice']) * position_to_close['quantity']
        
        closed_position = {
            **position_to_close,
            "closePrice": close_price,
            "closeDate": datetime.now().isoformat(),
            "status": 'closed',
            "pnl": round(pnl, 2)
        }
        self._closed_positions.append(closed_position)
        print(f"[PortfolioManager] Zamknięto pozycję dla {closed_position['ticker']}. Zysk/Strata: {pnl:.2f}$")
        return closed_position

    # --- Dostęp do Danych ---

    def get_open_positions(self) -> List[Dict[str, Any]]:
        return self._open_positions

    def get_closed_positions(self) -> List[Dict[str, Any]]:
        return self._closed_positions

