import httpx

from backend.config import settings

WMO_DESCRIPTIONS = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Icy fog", 51: "Light drizzle", 53: "Drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow",
    80: "Rain showers", 81: "Showers", 82: "Heavy showers",
    95: "Thunderstorm", 99: "Thunderstorm with hail",
}

WMO_ICONS = {
    0: "\u2600\ufe0f", 1: "\U0001f324\ufe0f", 2: "\u26c5", 3: "\u2601\ufe0f",
    45: "\U0001f32b\ufe0f", 48: "\U0001f32b\ufe0f", 51: "\U0001f326\ufe0f", 53: "\U0001f326\ufe0f",
    61: "\U0001f327\ufe0f", 63: "\U0001f327\ufe0f", 65: "\U0001f327\ufe0f",
    71: "\u2744\ufe0f", 73: "\u2744\ufe0f", 75: "\u2744\ufe0f",
    80: "\U0001f326\ufe0f", 81: "\U0001f326\ufe0f", 82: "\u26c8\ufe0f",
    95: "\u26c8\ufe0f", 99: "\u26c8\ufe0f",
}


async def get_weather() -> dict | None:
    """Fetch current weather from Open-Meteo for Fort Collins, CO."""
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={settings.weather_lat}&longitude={settings.weather_lon}"
            f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m"
            f"&daily=temperature_2m_max,temperature_2m_min"
            f"&temperature_unit=fahrenheit&wind_speed_unit=mph&timezone=America%2FDenver&forecast_days=1"
        )
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(url)
            data = r.json()

        cur = data.get("current", {})
        daily = data.get("daily", {})
        code = cur.get("weather_code", 0)
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])

        return {
            "temp_f": round(cur.get("temperature_2m", 0)),
            "desc": WMO_DESCRIPTIONS.get(code, f"Code {code}"),
            "icon": WMO_ICONS.get(code, "\U0001f321\ufe0f"),
            "humidity": cur.get("relative_humidity_2m", 0),
            "feels_like": round(cur.get("apparent_temperature", 0)),
            "wind_mph": round(cur.get("wind_speed_10m", 0)),
            "high": round(max_temps[0]) if max_temps else None,
            "low": round(min_temps[0]) if min_temps else None,
        }
    except Exception:
        return None
