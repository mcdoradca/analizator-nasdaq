"""
Moduł Agenta "Kokpitu".

Odpowiedzialność: Przeprowadzanie zaawansowanej analityki na historii
transakcji portfela w celu generowania wskaźników i spostrzeżeń.
"""

def agent_analityki_portfela(closed_positions):
    """
    Analizuje zamknięte pozycje i oblicza kluczowe wskaźniki wydajności
    zgodnie z wymaganiami interfejsu z pliku AnalizaNasdaq7.0.html.
    """
    if not closed_positions:
        return {
            "totalPnl": 0,
            "winRate": 0,
            "totalTrades": 0,
            "profitFactor": "N/A",
            "avgProfit": 0,
            "avgLoss": 0
        }

    total_trades = len(closed_positions)
    winning_trades = [p for p in closed_positions if p.get('pnl', 0) > 0]
    losing_trades = [p for p in closed_positions if p.get('pnl', 0) < 0]

    total_pnl = sum(p.get('pnl', 0) for p in closed_positions)
    win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0

    total_profit = sum(p.get('pnl', 0) for p in winning_trades)
    total_loss = abs(sum(p.get('pnl', 0) for p in losing_trades))

    avg_profit = total_profit / len(winning_trades) if winning_trades else 0
    avg_loss = total_loss / len(losing_trades) if losing_trades else 0

    if total_loss > 0:
        profit_factor = total_profit / total_loss
    else:
        profit_factor = "∞"  # Nieskończoność, jeśli nie ma strat

    return {
        "totalPnl": round(total_pnl, 2),
        "winRate": round(win_rate, 1),
        "totalTrades": total_trades,
        "profitFactor": round(profit_factor, 2) if isinstance(profit_factor, float) else profit_factor,
        "avgProfit": round(avg_profit, 2),
        "avgLoss": round(avg_loss, 2)
    }

def run_cockpit_analysis(closed_positions):
    """
    Główna funkcja orkiestrująca analizę kokpitu.
    W przyszłości może zarządzać wieloma agentami analitycznymi.
    """
    print(f"[Kokpit] Uruchamiam analizę dla {len(closed_positions)} zamkniętych transakcji.")
    
    analytics = agent_analityki_portfela(closed_positions)
    
    print("[Kokpit] Analiza statystyk portfela zakończona.")
    return analytics