
"""
Moduł Agenta Makroekonomicznego "Sokół".
Odpowiedzialność: Analiza ogólnej kondycji gospodarki i klimatu rynkowego.
"""
from typing import Dict, Any
from src.data_fetcher import data_fetcher

def get_macro_climate_analysis() -> Dict[str, Any]:
    """
    Przeprowadza analizę makroekonomiczną na podstawie rzeczywistych danych.
    """
    print("INFO: Agent 'Sokół' analizuje klimat makroekonomiczny...")

    # 1. Pobierz kluczowy wskaźnik - stopę funduszy federalnych (FED FUNDS RATE)
    params_rates = {"function": "FEDERAL_FUNDS_RATE", "interval": "monthly"}
    rates_data = data_fetcher.get_data(params_rates) if data_fetcher else None

    # 2. Pobierz wskaźnik CPI (inflacja)
    params_cpi = {"function": "CPI", "interval": "monthly"}
    cpi_data = data_fetcher.get_data(params_cpi) if data_fetcher else None

    analysis_result = {
        "status": "Brak Danych",
        "color": "text-gray-400",
        "icon": "fa-question-circle",
        "summary": "Nie udało się pobrać danych makroekonomicznych. Sprawdź połączenie z API.",
        "indicators": {}  # Dodajemy szczegółowe dane
    }

    try:
        # Analiza stóp procentowych
        if rates_data and "data" in rates_data and len(rates_data["data"]) > 0:
            latest_rate = rates_data["data"][0]
            rate_value = float(latest_rate["value"])
            analysis_result["indicators"]["fed_rate"] = rate_value
        else:
            print("WARNING: Nie udało się pobrać danych o stopach procentowych")
            analysis_result["indicators"]["fed_rate"] = None

        # Analiza inflacji (CPI)
        if cpi_data and "data" in cpi_data and len(cpi_data["data"]) > 0:
            latest_cpi = cpi_data["data"][0]
            cpi_value = float(latest_cpi["value"])
            analysis_result["indicators"]["cpi"] = cpi_value
        else:
            print("WARNING: Nie udało się pobrać danych CPI")
            analysis_result["indicators"]["cpi"] = None

        # Logika oceny klimatu (uproszczona)
        fed_rate = analysis_result["indicators"]["fed_rate"]
        cpi = analysis_result["indicators"]["cpi"]

        if fed_rate is not None and cpi is not None:
            if fed_rate < 2.0 and cpi < 3.0:
                analysis_result.update({
                    "status": "Bardzo Sprzyjający",
                    "color": "text-green-400",
                    "icon": "fa-sun",
                    "summary": "Niskie stopy procentowe i kontrola inflacji tworzą doskonałe warunki dla rynków akcji."
                })
            elif fed_rate < 3.5 and cpi < 4.5:
                analysis_result.update({
                    "status": "Umiarkowany",
                    "color": "text-yellow-400",
                    "icon": "fa-cloud-sun",
                    "summary": "Warunki makro są stabilne, ale wymagają czujności wobec potencjalnej zmienności."
                })
            else:
                analysis_result.update({
                    "status": "Ostrożności",
                    "color": "text-red-400",
                    "icon": "fa-cloud-showers-heavy",
                    "summary": "Podwyższone stopy procentowe i/lub inflacja mogą powodować presję na rynki akcji."
                })
        else:
            # Jeśli mamy tylko jeden wskaźnik, podejmujemy decyzję na jego podstawie
            if fed_rate is not None and fed_rate < 2.5:
                analysis_result.update({
                    "status": "Sprzyjający",
                    "color": "text-green-300",
                    "icon": "fa-cloud-sun",
                    "summary": "Niskie stopy procentowe wspierają rynek akcji."
                })

    except (KeyError, ValueError, IndexError) as e:
        print(f"ERROR: Błąd przetwarzania danych makro: {e}")
        # Pozostaw domyślny wynik "Brak Danych"

    print(f"INFO: Analiza makro zakończona. Status: {analysis_result['status']}")
    return analysis_result
