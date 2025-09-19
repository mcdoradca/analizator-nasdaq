# -*- coding: utf-8 -*-
"""
POPRAWIONY PortfolioManager - 100% KOMPATYBILNY Z sel.oo.txt
"""

from datetime import datetime
import uuid
from typing import List, Dict, Any, Optional

class PortfolioManager:
    def __init__(self):
        """
        Inicjalizuje menedżera ze stanem portfela oraz stanem Rewolucji AI.
        """
        self._dream_team: List[Dict[str, Any]] = []
        self._open_positions: List[Dict[str, Any]] = []
        self._closed_positions: List[Dict[str, Any]] = []
        
        # 💡 KLUCZOWA ZMIANA: phase1_candidates → qualified_candidates
        self._revolution_state = {
            "is_active": False,
            "is_completed": False,
            "last_scanned_index": -1,
            "full_market_list": [],
            "qualified_candidates": [],  # ✅ ZMIENIONO NAZWE
            "log": ["Rewolucja AI jest gotowa do startu."]
        }
        print("[PortfolioManager] Menedżer portfela został zainicjowany.")

    # --- ZARZĄDZANIE STANEM REWOLUCJI AI ---

    def get_revolution_state(self) -> Dict[str, Any]:
        return self._revolution_state

    def start_revolution(self, full_market_list: List[str]):
        self._revolution_state["is_active"] = True
        self._revolution_state["is_completed"] = False
        if self._revolution_state["last_scanned_index"] == -1:
            self._revolution_state["full_market_list"] = full_market_list
            self._revolution_state["qualified_candidates"] = []  # ✅ ZMIENIONO
            self._revolution_state["log"] = [f"Rozpoczęto Rewolucję AI. Cel: {len(full_market_list)} spółek."]
        else:
            self._revolution_state["log"].append("Wznowiono wstrzymaną Rewolucję AI.")
        print("[PortfolioManager] Stan Rewolucji AI: AKTYWNY.")

    def pause_revolution(self):
        if self._revolution_state["is_active"]:
            self._revolution_state["is_active"] = False
            self._revolution_state["log"].append("Rewolucja AI została wstrzymana.")
            print("[PortfolioManager] Stan Rewolucji AI: WSTRZYMANY.")

    def save_progress(self, last_scanned_index: int, new_candidates: List[Dict[str, Any]], log_messages: List[str]):
        """
        💡 KLUCZOWA ZMIANA: qualified_candidates zamiast phase1_candidates
        """
        self._revolution_state["last_scanned_index"] = last_scanned_index
        self._revolution_state["qualified_candidates"].extend(new_candidates)  # ✅ ZMIENIONO
        self._revolution_state["log"].extend(log_messages)
        self._revolution_state["log"] = self._revolution_state["log"][-100:]
        print(f"[PortfolioManager] Zapisano postęp Rewolucji do indeksu: {last_scanned_index}")

    def complete_revolution(self):
        """💡 KLUCZOWA ZMIANA: qualified_candidates zamiast phase1_candidates"""
        print("[PortfolioManager] Finalizowanie Rewolucji AI...")
        self._dream_team = self._revolution_state["qualified_candidates"]  # ✅ ZMIENIONO
        
        self._revolution_state["is_completed"] = True
        self._revolution_state["is_active"] = False
        self._revolution_state["log"].append("Rewolucja AI zakończona. Dream Team zaktualizowany.")
        print("[PortfolioManager] Rewolucja AI zakończona.")

    def reset_revolution(self):
        """💡 KLUCZOWA ZMIANA: qualified_candidates zamiast phase1_candidates"""
        self._revolution_state = {
            "is_active": False,
            "is_completed": False,
            "last_scanned_index": -1,
            "full_market_list": [],
            "qualified_candidates": [],  # ✅ ZMIENIONO
            "log": ["Rewolucja AI jest gotowa do startu."]
        }
        print("[PortfolioManager] Stan Rewolucji AI zresetowany.")

    # --- RESZTA METOD (bez zmian) ---
    def get_dream_team(self) -> List[Dict[str, Any]]:
        return self._dream_team

    def get_dream_team_tickers(self) -> List[str]:
        return [stock['ticker'] for stock in self._dream_team if 'ticker' in stock]

    def update_dream_team(self, new_candidates_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not isinstance(new_candidates_list, list):
            print("[PortfolioManager] BŁĄD: Oczekiwano listy kandydatów.")
            return self._dream_team
        self._dream_team = new_candidates_list
        tickers = self.get_dream_team_tickers()
        print(f"[PortfolioManager] Dream Team zaktualizowany. Nowi kandydaci: {tickers}")
        return self._dream_team

    # ... (reszta metod bez zmian)
