import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest  # noqa: E402
from normalizer import normalize, WeatherRecord  # noqa: E402

OWM_SAMPLE = {
    "name": "Moscow",
    "main": {"temp": 12.5, "humidity": 72},
    "wind": {"speed": 5.1, "deg": 180},
    "weather": [{"description": "light rain"}],
}

OPENMETEO_SAMPLE = {
    "_city": "Moscow",
    "current_weather": {
        "temperature": 11.8,
        "windspeed": 4.3,
        "winddirection": 200,
    },
    "hourly": {"relativehumidity_2m": [68, 70]},
}


def test_normalize_owm_returns_weather_record():
    record = normalize(OWM_SAMPLE, "openweathermap")
    assert isinstance(record, WeatherRecord)


def test_normalize_owm_fields():
    record = normalize(OWM_SAMPLE, "openweathermap")
    assert record.city == "Moscow"
    assert record.source == "openweathermap"
    assert record.temperature == 12.5
    assert record.humidity == 72
    assert record.wind_speed == 5.1
    assert record.wind_dir == 180
    assert record.description == "light rain"


def test_normalize_openmeteo_fields():
    record = normalize(OPENMETEO_SAMPLE, "open-meteo")
    assert record.city == "Moscow"
    assert record.source == "open-meteo"
    assert record.temperature == 11.8
    assert record.wind_speed == 4.3
    assert record.wind_dir == 200
    assert record.humidity == 68


def test_normalize_unknown_source_raises():
    with pytest.raises(ValueError, match="Unknown source"):
        normalize({}, "unknown")
