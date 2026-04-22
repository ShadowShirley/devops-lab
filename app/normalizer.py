from dataclasses import dataclass


@dataclass
class WeatherRecord:
    city: str
    source: str
    temperature: float | None
    humidity: int | None
    wind_speed: float | None
    wind_dir: int | None
    description: str | None


def normalize(raw: dict, source: str) -> WeatherRecord:
    if source == "openweathermap":
        return WeatherRecord(
            city=raw["name"],
            source=source,
            temperature=raw["main"]["temp"],
            humidity=raw["main"]["humidity"],
            wind_speed=raw["wind"]["speed"],
            wind_dir=raw["wind"].get("deg"),
            description=raw["weather"][0]["description"] if raw.get("weather") else None,
        )
    if source == "open-meteo":
        cw = raw["current_weather"]
        humidity = None
        hourly = raw.get("hourly", {})
        if hourly.get("relativehumidity_2m"):
            humidity = hourly["relativehumidity_2m"][0]
        return WeatherRecord(
            city=raw["_city"],
            source=source,
            temperature=cw["temperature"],
            humidity=humidity,
            wind_speed=cw["windspeed"],
            wind_dir=cw["winddirection"],
            description=None,
        )
    raise ValueError(f"Unknown source: {source}")
