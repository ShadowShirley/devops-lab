import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from unittest.mock import patch, MagicMock
from sources import fetch_openweathermap, fetch_openmeteo

OWM_RESPONSE = {
    "name": "Moscow",
    "main": {"temp": 12.5, "humidity": 72},
    "wind": {"speed": 5.1, "deg": 180},
    "weather": [{"description": "light rain"}],
}

GEOCODING_RESPONSE = {
    "results": [{"latitude": 55.7558, "longitude": 37.6173}]
}

OPENMETEO_RESPONSE = {
    "current_weather": {"temperature": 11.8, "windspeed": 4.3, "winddirection": 200},
    "hourly": {"relativehumidity_2m": [68]},
}


def test_fetch_openweathermap_returns_dict(monkeypatch):
    monkeypatch.setenv("OWM_API_KEY", "test-key")
    mock_resp = MagicMock()
    mock_resp.json.return_value = OWM_RESPONSE
    mock_resp.raise_for_status = MagicMock()
    with patch("sources.requests.get", return_value=mock_resp):
        result = fetch_openweathermap("Moscow")
    assert result["name"] == "Moscow"
    assert result["main"]["temp"] == 12.5


def test_fetch_openweathermap_passes_api_key(monkeypatch):
    monkeypatch.setenv("OWM_API_KEY", "my-secret-key")
    mock_resp = MagicMock()
    mock_resp.json.return_value = OWM_RESPONSE
    mock_resp.raise_for_status = MagicMock()
    with patch("sources.requests.get", return_value=mock_resp) as mock_get:
        fetch_openweathermap("Moscow")
    call_params = mock_get.call_args[1]["params"]
    assert call_params["appid"] == "my-secret-key"
    assert call_params["q"] == "Moscow"


def test_fetch_openweathermap_raises_without_key(monkeypatch):
    monkeypatch.delenv("OWM_API_KEY", raising=False)
    with pytest.raises(KeyError):
        fetch_openweathermap("Moscow")


def test_fetch_openmeteo_returns_dict_with_city():
    geo_resp = MagicMock()
    geo_resp.json.return_value = GEOCODING_RESPONSE
    geo_resp.raise_for_status = MagicMock()
    weather_resp = MagicMock()
    weather_resp.json.return_value = OPENMETEO_RESPONSE
    weather_resp.raise_for_status = MagicMock()
    with patch("sources.requests.get", side_effect=[geo_resp, weather_resp]):
        result = fetch_openmeteo("Moscow")
    assert result["_city"] == "Moscow"
    assert result["current_weather"]["temperature"] == 11.8


def test_fetch_openmeteo_raises_on_unknown_city():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"results": []}
    mock_resp.raise_for_status = MagicMock()
    with patch("sources.requests.get", return_value=mock_resp):
        with pytest.raises(ValueError, match="City not found"):
            fetch_openmeteo("NonExistentCity123XYZ")
