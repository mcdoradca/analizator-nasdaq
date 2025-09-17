# -*- coding: utf-8 -*-
"""
Moduł Agenta Makroekonomicznego "Sokół".

Odpowiedzialność: Analiza ogólnej kondycji gospodarki i klimatu rynkowego
na podstawie rzeczywistych danych z API.
"""
from typing import Dict, List, Optional
import os
from data_fetcher import DataFetcher

def get_latest_value(data: Optional[Dict], data_key: str = "data") -> Optional[float]:
    """Pomocnicza funkcja do wyciągania najnowszej wartości ze wskaźnika."""
    if data and data.get(data_key) and len(data[data_key]) > 0:
        try:
            return float(data[data_key][0]['value'])
        except (ValueError, KeyError):
            return None
    return None

def get_macro_climate_analysis(fetcher: DataFetcher) -> Dict:
    """
    Przeprowadza analizę makroekonomiczną na podstawie kluczowych wskaźników z Alpha Vantage.
    """
    print("INFO: Agent 'Sokół' analizuje klimat makroekonomiczny...")

    # Pobieranie danych dla kluczowych wskaźników
    cpi_data = fetcher.get_data({"function": "CPI", "interval": "monthly"})
    fed_rate_data = fetcher.get_data({"function": "FEDERAL_FUNDS_RATE", "interval": "monthly"})
    unemployment_data = fetcher.get_data({"function": "UNEMPLOYMENT"})
    sentiment_data = fetcher.get_data({"function": "CONSUMER_SENTIMENT"})

    # Prosty system punktacji: +1 dla pozytywnego sygnału, -1 dla negatywnego
    score = 0
    summary_points: List[str] = []

    # 1. Analiza Inflacji (CPI)
    # Spadek inflacji jest generalnie pozytywny dla rynku.
    if cpi_data and cpi_data.get("data") and len(cpi_data["data"]) > 1:
        latest_cpi = float(cpi_data["data"][0]['value'])
        previous_cpi = float(cpi_data["data"][1]['value'])
        if latest_cpi < previous_cpi:
            score += 1
            summary_points.append(f"Inflacja spada ({latest_cpi:.2f}).")
        else:
            score -= 1
            summary_points.append(f"Inflacja rośnie ({latest_cpi:.2f}).")
    else:
        summary_points.append("Brak danych o inflacji.")

    # 2. Analiza Stóp Procentowych
    # Stabilne lub spadające stopy są pozytywne.
    if fed_rate_data and fed_rate_data.get("data") and len(fed_rate_data["data"]) > 1:
        latest_rate = float(fed_rate_data["data"][0]['value'])
        previous_rate = float(fed_rate_data["data"][1]['value'])
        if latest_rate <= previous_rate:
            score += 1
            summary_points.append(f"Stopy procentowe stabilne/spadają ({latest_rate:.2f}%).")
        else:
            score -= 1
            summary_points.append(f"Stopy procentowe rosną ({latest_rate:.2f}%).")
    else:
        summary_points.append("Brak danych o stopach procentowych.")
        
    # 3. Analiza Bezrobocia
    # Niskie i spadające bezrobocie jest pozytywne.
    latest_unemployment = get_latest_value(unemployment_data)
    if latest_unemployment:
        # Im niższe bezrobocie, tym lepiej.
        if latest_unemployment < 4.0:
            score += 1
            summary_points.append(f"Bezrobocie niskie ({latest_unemployment:.2f}%).")
        else:
            score -= 1
            summary_points.append(f"Bezrobocie podwyższone ({latest_unemployment:.2f}%).")
    else:
         summary_points.append("Brak danych o bezrobociu.")
         
    # 4. Analiza Nastrojów Konsumentów
    # Wysokie nastroje są pozytywne.
    latest_sentiment = get_latest_value(sentiment_data)
    if latest_sentiment:
        if latest_sentiment > 80:
             score += 1
             summary_points.append("Nastroje konsumentów są optymistyczne.")
        elif latest_sentiment < 60:
             score -= 1
             summary_points.append("Nastroje konsumentów są pesymistyczne.")
        else:
             summary_points.append("Nastroje konsumentów są neutralne.")
    else:
        summary_points.append("Brak danych o nastrojach.")

    # Finalna ocena na podstawie wyniku
    summary = " ".join(summary_points)
    
    if score >= 2:
        return {
            "status": "Sprzyjający Ryzyku",
            "color": "text-green-400",
            "icon": "fa-arrow-trend-up",
            "summary": summary
        }
    elif score <= -2:
        return {
            "status": "Unikaj Ryzyka",
            "color": "text-red-500",
            "icon": "fa-arrow-trend-down",
            "summary": summary
        }
    else:
        return {
            "status": "Neutralny",
            "color": "text-blue-400",
            "icon": "fa-arrows-left-right",
            "summary": summary
        }

# Blok do testowania modułu w izolacji
if __name__ == "__main__":
    API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not API_KEY:
        print("OSTRZEŻENIE: Brak klucza ALPHA_VANTAGE_API_KEY. Testy mogą się nie powść.")
        API_KEY = "TWOJ_KLUCZ_API"

    fetcher = DataFetcher(api_key=API_KEY)

    print("\n--- Test Agenta 'Sokół' ---")
    macro_analysis = get_macro_climate_analysis(fetcher)
    
    import json
    print("\nWynik analizy 'Sokoła':")
    print(json.dumps(macro_analysis, indent=2, ensure_ascii=False))
