import os
import requests

OWM_BASE = "https://api.openweathermap.org/data/2.5/weather"
GEOCODING_BASE = "https://geocoding-api.open-meteo.com/v1/search"
OPENMETEO_BASE = "https://api.open-meteo.com/v1/forecast"


def fetch_openweathermap(city: str) -> dict:
    api_key = os.environ["OWM_API_KEY"]
    resp = requests.get(
        OWM_BASE,
        params={"q": city, "appid": api_key, "units": "metric"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def _geocode(city: str) -> tuple[float, float]:
    resp = requests.get(
        GEOCODING_BASE,
        params={"name": city, "count": 1, "language": "ru"},
        timeout=10,
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])
    if not results:
        raise ValueError(f"City not found: {city}")
    return results[0]["latitude"], results[0]["longitude"]


def fetch_openmeteo(city: str) -> dict:
    lat, lon = _geocode(city)
    resp = requests.get(
        OPENMETEO_BASE,
        params={
            "latitude": lat,
            "longitude": lon,
            "current_weather": True,
            "hourly": "relativehumidity_2m",
            "timezone": "auto",
            "forecast_days": 1,
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    data["_city"] = city
    return data
