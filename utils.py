"""
Moduł z funkcjami pomocniczymi, używanymi przez różnych agentów.
"""

def get_latest_value(data, primary_key, secondary_key=None):
    """
    Bezpiecznie pobiera najnowszą wartość z danych szeregów czasowych Alpha Vantage.
    """
    if not data or primary_key not in data:
        return None
    
    time_series = data[primary_key]
    if not time_series:
        return None
        
    latest_date = next(iter(time_series))
    latest_data = time_series[latest_date]
    
    if secondary_key:
        return latest_data.get(secondary_key)
    return latest_data

def safe_float(value, default=0.0):
    """
    Bezpiecznie konwertuje wartość na float, obsługując None i błędy.
    """
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
