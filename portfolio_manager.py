
"""
Moduł Menedżera Portfela.

Odpowiedzialność: Zarządzanie stanem portfela użytkownika, w tym listą
obserwowanych spółek (Dream Team) oraz otwartymi i zamkniętymi pozycjami.
"""

from datetime import datetime
import uuid

class PortfolioManager:
    def __init__(self):
        """
        Inicjalizuje menedżera z pustymi listami.
        Ten moduł NIE komunikuje się bezpośrednio z API w celu pobierania cen.
        Odpowiada wyłącznie za zarządzanie stanem.
        """
        self._dream_team = []
        self._open_positions = []
        self._closed_positions = []
        print("[PortfolioManager] Menedżer portfela został zainicjowany.")

    # --- Zarządzanie Dream Team ---

    def get_dream_team(self):
        """
        Zwraca listę spółek z "Dream Teamu".
        NIE pobiera cen w czasie rzeczywistym, aby oszczędzać limity API.
        Ceny i dane są aktualizowane przez zewnętrzne procesy.
        """
        return self._dream_team

    def update_dream_team(self, new_candidates_list):
        """
        Aktualizuje Dream Team na podstawie wyników skanowania Rewolucji AI.
        Oczekuje listy słowników, a nie tylko tickerów.
        """
        # Oczekujemy, że new_candidates_list to lista obiektów, np.:
        # [{'ticker': 'AAPL', 'status': 'Nowy', 'aiScore': 50, 'currentPrice': 150.0, 'changePercent': 1.2}]
        self._dream_team = new_candidates_list
        tickers = [stock.get('ticker') for stock in new_candidates_list]
        print(f"[PortfolioManager] Dream Team zaktualizowany. Nowi kandydaci: {tickers}")
        return self._dream_team

    def update_dream_team_prices(self, price_updates):
        """
        Metoda do hurtowej aktualizacji cen i danych w Dream Team.
        Oczekuje słownika w formacie {'TICKER': {'currentPrice': X, 'changePercent': Y}}.
        """
        updated_count = 0
        for stock in self._dream_team:
            if stock['ticker'] in price_updates:
                stock.update(price_updates[stock['ticker']])
                updated_count += 1
        print(f"[PortfolioManager] Zaktualizowano ceny dla {updated_count} spółek w Dream Team.")

    # --- Zarządzanie Transakcjami ---

    def open_position(self, ticker, quantity, entry_price, reason, target_price, stop_loss_price):
        """Dodaje nową otwartą pozycję."""
        position = {
            "id": str(uuid.uuid4()),
            "ticker": ticker,
            "quantity": quantity,
            "entryPrice": entry_price,
            "targetPrice": target_price,
            "stopLossPrice": stop_loss_price,
            "openDate": datetime.now().isoformat(),
            "status": "active",
            "reason": reason
        }
        self._open_positions.append(position)
        print(f"[PortfolioManager] Otwarto nową pozycję: {quantity} akcji {ticker} po cenie {entry_price}")
        return position

    def close_position(self, position_id, close_price):
        """Zamyka otwartą pozycję i przenosi ją do historii."""
        position_index = -1
        for i, pos in enumerate(self._open_positions):
            if pos['id'] == position_id:
                position_index = i
                break

        if position_index == -1:
            print(f"[PortfolioManager] BŁĄD: Nie znaleziono otwartej pozycji o ID: {position_id}")
            return None

        closed_position = self._open_positions.pop(position_index)
        closed_position['closePrice'] = close_price
        closed_position['closeDate'] = datetime.now().isoformat()
        closed_position['status'] = 'closed'
        
        pnl = (close_price - closed_position['entryPrice']) * closed_position['quantity']
        pnl_percent = ((close_price / closed_position['entryPrice']) - 1) * 100 if closed_position['entryPrice'] != 0 else 0

        closed_position['pnl'] = round(pnl, 2)
        closed_position['pnlPercent'] = round(pnl_percent, 2)
        
        self._closed_positions.append(closed_position)
        print(f"[PortfolioManager] Zamknięto pozycję dla {closed_position['ticker']}. Zysk/Strata: {pnl:.2f}$")
        return closed_position

    # --- Dostęp do Danych ---

    def get_open_positions(self):
        return self._open_positions

    def get_closed_positions(self):
        return self._closed_positions

    def get_full_portfolio_state(self):
        """Zwraca kompletny stan portfela dla API."""
        return {
            "dreamTeam": self.get_dream_team(),
            "openPositions": self.get_open_positions(),
            "closedPositions": self.get_closed_positions()
        }

