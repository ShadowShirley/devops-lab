# Weather Aggregator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Развернуть агрегатор погоды из двух источников (OpenWeatherMap + Open-Meteo) с PostgreSQL, Metabase, pgAdmin, Nginx в Docker Compose с CI через GitHub Actions.

**Architecture:** Монолитное Flask-приложение собирает данные по нажатию кнопки, нормализует их через dataclass WeatherRecord и сохраняет в PostgreSQL. Nginx роутит `/` на Flask, редиректит `/analytics` на Metabase (порт 3000) и `/admin` на pgAdmin (порт 5050).

**Tech Stack:** Python 3.11, Flask 3, psycopg2-binary, PostgreSQL 15, pgAdmin 4, Metabase, Nginx alpine, Docker Compose v2, GitHub Actions, flake8, pytest.

---

## File Map

| Файл | Роль |
|---|---|
| `app/sources.py` | HTTP-запросы к OWM и Open-Meteo |
| `app/normalizer.py` | WeatherRecord dataclass + normalize() |
| `app/db.py` | create_table(), insert_record(), get_logs() |
| `app/app.py` | Flask routes: /, /collect, /logs |
| `app/templates/base.html` | Navbar layout |
| `app/templates/index.html` | Форма + результат |
| `app/templates/logs.html` | Таблица истории |
| `app/tests/test_normalizer.py` | Юнит-тесты нормализатора |
| `app/tests/test_sources.py` | Юнит-тесты парсера (mock HTTP) |
| `app/requirements.txt` | Python зависимости |
| `app/Dockerfile` | Образ Flask-приложения |
| `nginx/nginx.conf` | Маршрутизация трафика |
| `docker-compose.yml` | Оркестрация 5 сервисов |
| `.env.example` | Шаблон переменных окружения |
| `.github/workflows/ci.yml` | GitHub Actions: flake8 + pytest |
| `README.md` | Документация проекта |

---

## Task 1: Scaffold проекта

**Files:**
- Create: `app/__init__.py` (пустой)
- Create: `app/tests/__init__.py` (пустой)
- Create: `.env.example`
- Create: `.gitignore`

- [ ] **Шаг 1: Создать структуру директорий**

```bash
mkdir -p app/templates app/tests nginx .github/workflows
touch app/__init__.py app/tests/__init__.py
```

- [ ] **Шаг 2: Создать `.env.example`**

```env
OWM_API_KEY=your_openweathermap_api_key_here
POSTGRES_DB=weather_db
POSTGRES_USER=weather_user
POSTGRES_PASSWORD=secret
POSTGRES_HOST=db
PGADMIN_DEFAULT_EMAIL=admin@admin.com
PGADMIN_DEFAULT_PASSWORD=admin
SECRET_KEY=change-me-in-production
```

- [ ] **Шаг 3: Создать `.gitignore`**

```gitignore
.env
__pycache__/
*.pyc
venv/
.superpowers/
*.egg-info/
```

- [ ] **Шаг 4: Commit**

```bash
git add app/__init__.py app/tests/__init__.py .env.example .gitignore
git commit -m "chore: project scaffold"
```

---

## Task 2: Модуль нормализации (TDD)

**Files:**
- Create: `app/normalizer.py`
- Create: `app/tests/test_normalizer.py`

- [ ] **Шаг 1: Написать падающие тесты**

Создать `app/tests/test_normalizer.py`:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from normalizer import normalize, WeatherRecord

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
```

- [ ] **Шаг 2: Запустить тесты — убедиться что падают**

```bash
cd app && python -m pytest tests/test_normalizer.py -v
```

Ожидаем: `ModuleNotFoundError: No module named 'normalizer'`

- [ ] **Шаг 3: Реализовать `app/normalizer.py`**

```python
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
```

- [ ] **Шаг 4: Запустить тесты — убедиться что проходят**

```bash
cd app && python -m pytest tests/test_normalizer.py -v
```

Ожидаем: `4 passed`

- [ ] **Шаг 5: Commit**

```bash
git add app/normalizer.py app/tests/test_normalizer.py
git commit -m "feat: add normalizer with WeatherRecord dataclass"
```

---

## Task 3: Модуль источников данных (TDD)

**Files:**
- Create: `app/sources.py`
- Create: `app/tests/test_sources.py`

- [ ] **Шаг 1: Написать падающие тесты**

Создать `app/tests/test_sources.py`:

```python
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
```

- [ ] **Шаг 2: Запустить — убедиться что падают**

```bash
cd app && python -m pytest tests/test_sources.py -v
```

Ожидаем: `ModuleNotFoundError: No module named 'sources'`

- [ ] **Шаг 3: Реализовать `app/sources.py`**

```python
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
```

- [ ] **Шаг 4: Запустить — убедиться что проходят**

```bash
cd app && python -m pytest tests/test_sources.py -v
```

Ожидаем: `5 passed`

- [ ] **Шаг 5: Прогнать все тесты**

```bash
cd app && python -m pytest tests/ -v
```

Ожидаем: `9 passed`

- [ ] **Шаг 6: Commit**

```bash
git add app/sources.py app/tests/test_sources.py
git commit -m "feat: add weather sources (OWM + Open-Meteo)"
```

---

## Task 4: Модуль базы данных

**Files:**
- Create: `app/db.py`

(Тесты для db.py требуют реального Postgres, поэтому покрываем интеграционно через запуск всей системы в Task 7)

- [ ] **Шаг 1: Создать `app/db.py`**

```python
import os
import psycopg2


def get_conn():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "db"),
        dbname=os.environ.get("POSTGRES_DB", "weather_db"),
        user=os.environ.get("POSTGRES_USER", "weather_user"),
        password=os.environ.get("POSTGRES_PASSWORD", "secret"),
    )


def create_table():
    conn = get_conn()
    with conn, conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS weather_records (
                id          SERIAL PRIMARY KEY,
                city        VARCHAR(100) NOT NULL,
                source      VARCHAR(50)  NOT NULL,
                temperature NUMERIC(5,2),
                humidity    INTEGER,
                wind_speed  NUMERIC(5,2),
                wind_dir    INTEGER,
                description VARCHAR(200),
                fetched_at  TIMESTAMP NOT NULL DEFAULT NOW(),
                UNIQUE (city, source, fetched_at)
            )
        """)
    conn.close()


def insert_record(record) -> None:
    conn = get_conn()
    with conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO weather_records
                (city, source, temperature, humidity, wind_speed, wind_dir, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (
                record.city, record.source, record.temperature,
                record.humidity, record.wind_speed, record.wind_dir,
                record.description,
            ),
        )
    conn.close()


def get_logs(limit: int = 50) -> list[dict]:
    conn = get_conn()
    with conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT city, source, temperature, humidity, wind_speed, fetched_at
            FROM weather_records
            ORDER BY fetched_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    conn.close()
    return rows
```

- [ ] **Шаг 2: Commit**

```bash
git add app/db.py
git commit -m "feat: add database module (create_table, insert_record, get_logs)"
```

---

## Task 5: Flask приложение и шаблоны

**Files:**
- Create: `app/app.py`
- Create: `app/templates/base.html`
- Create: `app/templates/index.html`
- Create: `app/templates/logs.html`

- [ ] **Шаг 1: Создать `app/app.py`**

```python
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from sources import fetch_openweathermap, fetch_openmeteo
from normalizer import normalize
from db import create_table, insert_record, get_logs

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

_table_created = False


@app.before_request
def init_db():
    global _table_created
    if not _table_created:
        try:
            create_table()
            _table_created = True
        except Exception:
            pass


@app.route("/")
def index():
    result = session.pop("last_result", None)
    return render_template("index.html", result=result)


@app.route("/collect", methods=["POST"])
def collect():
    city = request.form.get("city", "").strip()
    if not city:
        flash("Введите название города")
        return redirect(url_for("index"))

    records = []
    errors = []

    for fetch_fn, source in [
        (fetch_openweathermap, "openweathermap"),
        (fetch_openmeteo, "open-meteo"),
    ]:
        try:
            raw = fetch_fn(city)
            record = normalize(raw, source)
            insert_record(record)
            records.append(record)
        except Exception as e:
            errors.append(f"{source}: {e}")

    session["last_result"] = {
        "city": city,
        "records": [
            {
                "source": r.source,
                "temperature": r.temperature,
                "humidity": r.humidity,
                "wind_speed": r.wind_speed,
                "description": r.description,
            }
            for r in records
        ],
        "errors": errors,
    }
    return redirect(url_for("index"))


@app.route("/logs")
def logs():
    rows = get_logs()
    return render_template("logs.html", rows=rows)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

- [ ] **Шаг 2: Создать `app/templates/base.html`**

```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>WeatherAgg</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: system-ui, sans-serif; background: #0d1117; color: #e6edf3; min-height: 100vh; }
        nav { background: #161b22; border-bottom: 1px solid #30363d; padding: 12px 24px; display: flex; gap: 24px; align-items: center; }
        nav a { color: #8b949e; text-decoration: none; font-size: 14px; }
        nav .brand { color: #58a6ff; font-weight: bold; margin-right: 12px; }
        nav a:hover, nav a.active { color: #e6edf3; }
        main { max-width: 960px; margin: 32px auto; padding: 0 24px; }
        h1 { font-size: 22px; margin-bottom: 20px; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin-bottom: 16px; }
        .btn { background: #238636; color: #fff; border: none; padding: 8px 18px; border-radius: 6px; cursor: pointer; font-size: 14px; }
        .btn:hover { background: #2ea043; }
        input[type=text] { background: #0d1117; border: 1px solid #30363d; border-radius: 6px; padding: 8px 12px; color: #e6edf3; font-size: 14px; width: 280px; }
        .flash { background: #3d1212; border: 1px solid #f85149; border-radius: 6px; padding: 10px 16px; margin-bottom: 16px; font-size: 13px; color: #ff7b72; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #21262d; }
        th { color: #8b949e; font-weight: 500; }
        .muted { color: #8b949e; }
        .temp { color: #79c0ff; font-weight: bold; }
    </style>
</head>
<body>
<nav>
    <a href="/" class="brand">🌤 WeatherAgg</a>
    <a href="/" {% if request.path == '/' %}class="active"{% endif %}>Главная</a>
    <a href="/analytics">Аналитика ↗</a>
    <a href="/admin">Администрирование ↗</a>
    <a href="/logs" {% if request.path == '/logs' %}class="active"{% endif %}>Логи</a>
</nav>
<main>
    {% with messages = get_flashed_messages() %}
      {% if messages %}{% for msg in messages %}<div class="flash">{{ msg }}</div>{% endfor %}{% endif %}
    {% endwith %}
    {% block content %}{% endblock %}
</main>
</body>
</html>
```

- [ ] **Шаг 3: Создать `app/templates/index.html`**

```html
{% extends "base.html" %}
{% block content %}
<h1>Агрегатор погодных данных</h1>

<div class="card">
    <form method="POST" action="/collect" style="display:flex;gap:10px;align-items:center;">
        <input type="text" name="city" placeholder="Введите город (напр. Москва)" required>
        <button type="submit" class="btn">Собрать данные</button>
    </form>
</div>

{% if result %}
<div class="card">
    <div class="muted" style="font-size:13px;margin-bottom:12px;">📍 {{ result.city }}</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
        {% for r in result.records %}
        <div style="background:#0d1117;border:1px solid #30363d;border-radius:6px;padding:14px;">
            <div class="muted" style="font-size:11px;margin-bottom:4px;">{{ r.source }}</div>
            <div class="temp" style="font-size:28px;">
                {% if r.temperature is not none %}{{ r.temperature }}°C{% else %}—{% endif %}
            </div>
            <div class="muted" style="font-size:12px;margin-top:6px;">
                {% if r.humidity %}Влажность: {{ r.humidity }}%{% endif %}
                {% if r.wind_speed %} · Ветер: {{ r.wind_speed }} м/с{% endif %}
            </div>
            {% if r.description %}
            <div style="font-size:12px;color:#7ee787;margin-top:4px;">{{ r.description }}</div>
            {% endif %}
        </div>
        {% endfor %}
    </div>
    {% if result.errors %}
    <div style="margin-top:10px;font-size:12px;color:#f85149;">
        {% for e in result.errors %}⚠ {{ e }}<br>{% endfor %}
    </div>
    {% endif %}
</div>
{% endif %}
{% endblock %}
```

- [ ] **Шаг 4: Создать `app/templates/logs.html`**

```html
{% extends "base.html" %}
{% block content %}
<h1>История сборов</h1>
<div class="card">
    {% if rows %}
    <table>
        <thead>
            <tr>
                <th>Время</th><th>Город</th><th>Источник</th>
                <th>Темп.</th><th>Влажность</th><th>Ветер</th>
            </tr>
        </thead>
        <tbody>
            {% for row in rows %}
            <tr>
                <td class="muted">{{ row.fetched_at.strftime('%d.%m %H:%M') }}</td>
                <td>{{ row.city }}</td>
                <td class="muted">{{ row.source }}</td>
                <td class="temp">
                    {% if row.temperature is not none %}{{ row.temperature }}°C{% else %}—{% endif %}
                </td>
                <td>{% if row.humidity is not none %}{{ row.humidity }}%{% else %}—{% endif %}</td>
                <td>{% if row.wind_speed is not none %}{{ row.wind_speed }} м/с{% else %}—{% endif %}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <p class="muted">Данных пока нет. Соберите первую запись на главной странице.</p>
    {% endif %}
</div>
{% endblock %}
```

- [ ] **Шаг 5: Commit**

```bash
git add app/app.py app/templates/
git commit -m "feat: add Flask app with routes /, /collect, /logs"
```

---

## Task 6: requirements.txt и Dockerfile

**Files:**
- Create: `app/requirements.txt`
- Create: `app/Dockerfile`

- [ ] **Шаг 1: Создать `app/requirements.txt`**

```
Flask==3.0.3
requests==2.32.3
psycopg2-binary==2.9.9
python-dotenv==1.0.1
pytest==8.2.2
flake8==7.1.0
```

- [ ] **Шаг 2: Создать `app/Dockerfile`**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV FLASK_APP=app.py
EXPOSE 5000
CMD ["python", "app.py"]
```

- [ ] **Шаг 3: Проверить что образ собирается**

```bash
cd app && docker build -t weather-app:test .
```

Ожидаем: `Successfully built ...`

- [ ] **Шаг 4: Commit**

```bash
git add app/requirements.txt app/Dockerfile
git commit -m "feat: add Dockerfile and requirements"
```

---

## Task 7: Docker Compose и Nginx

**Files:**
- Create: `nginx/nginx.conf`
- Create: `docker-compose.yml`

- [ ] **Шаг 1: Создать `nginx/nginx.conf`**

```nginx
events {}

http {
    server {
        listen 80;

        location / {
            proxy_pass         http://app:5000;
            proxy_set_header   Host $host;
            proxy_set_header   X-Real-IP $remote_addr;
            proxy_read_timeout 60s;
        }

        location /analytics {
            return 301 http://localhost:3000;
        }

        location /admin {
            return 301 http://localhost:5050;
        }
    }
}
```

- [ ] **Шаг 2: Создать `docker-compose.yml`**

```yaml
services:
  db:
    image: postgres:15
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-weather_db}
      POSTGRES_USER: ${POSTGRES_USER:-weather_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-secret}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-weather_user}"]
      interval: 5s
      timeout: 5s
      retries: 10

  app:
    build: ./app
    restart: unless-stopped
    environment:
      OWM_API_KEY: ${OWM_API_KEY}
      POSTGRES_HOST: db
      POSTGRES_DB: ${POSTGRES_DB:-weather_db}
      POSTGRES_USER: ${POSTGRES_USER:-weather_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-secret}
      SECRET_KEY: ${SECRET_KEY:-dev-secret}
    depends_on:
      db:
        condition: service_healthy

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - app

  pgadmin:
    image: dpage/pgadmin4
    restart: unless-stopped
    ports:
      - "5050:80"
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_DEFAULT_EMAIL:-admin@admin.com}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_DEFAULT_PASSWORD:-admin}
    depends_on:
      db:
        condition: service_healthy

  metabase:
    image: metabase/metabase
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      MB_DB_TYPE: postgres
      MB_DB_DBNAME: ${POSTGRES_DB:-weather_db}
      MB_DB_PORT: 5432
      MB_DB_USER: ${POSTGRES_USER:-weather_user}
      MB_DB_PASS: ${POSTGRES_PASSWORD:-secret}
      MB_DB_HOST: db
    depends_on:
      db:
        condition: service_healthy

volumes:
  postgres_data:
```

- [ ] **Шаг 3: Скопировать `.env.example` в `.env` и заполнить OWM_API_KEY**

```bash
cp .env.example .env
# Открыть .env и вставить реальный ключ OWM_API_KEY
# Получить ключ на: https://openweathermap.org/api → Sign Up → API Keys
```

- [ ] **Шаг 4: Запустить всю систему**

```bash
docker-compose up -d --build
```

Ожидаем: все 5 контейнеров `Started`

- [ ] **Шаг 5: Проверить что все контейнеры живы**

```bash
docker-compose ps
```

Ожидаем: все сервисы в статусе `running`

- [ ] **Шаг 6: Проверить главную страницу**

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost
```

Ожидаем: `200`

- [ ] **Шаг 7: Commit**

```bash
git add nginx/nginx.conf docker-compose.yml
git commit -m "feat: add Docker Compose and Nginx config"
```

---

## Task 8: GitHub Actions CI

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Шаг 1: Создать `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install flake8 pytest requests

      - name: Lint with flake8
        run: flake8 app/ --max-line-length=120 --exclude=app/tests/__init__.py

      - name: Run tests
        run: |
          cd app
          python -m pytest tests/ -v
```

- [ ] **Шаг 2: Запушить в GitHub и убедиться что Actions запустились**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions with flake8 and pytest"
git push origin main
```

Открыть вкладку **Actions** в репозитории на GitHub — ожидаем зелёный `✓`

---

## Task 9: Настройка pgAdmin

Выполняется вручную в браузере после запуска `docker-compose up -d`.

- [ ] **Шаг 1: Открыть pgAdmin**

Перейти на `http://localhost:5050`  
Войти: `admin@admin.com` / `admin`

- [ ] **Шаг 2: Добавить сервер PostgreSQL**

Нажать **Add New Server**:
- **Name:** `weather`
- Вкладка **Connection:**
  - Host: `db`
  - Port: `5432`
  - Database: `weather_db`
  - Username: `weather_user`
  - Password: `secret`

Нажать **Save**

- [ ] **Шаг 3: Убедиться что таблица видна**

Раскрыть: `weather → Databases → weather_db → Schemas → public → Tables → weather_records`

---

## Task 10: Настройка Metabase

Выполняется вручную в браузере. Metabase запускается ~2 минуты.

- [ ] **Шаг 1: Открыть Metabase**

Перейти на `http://localhost:3000`  
Пройти начальную настройку (язык, имя, email, пароль)

- [ ] **Шаг 2: Подключить базу данных**

В процессе настройки или через **Settings → Databases → Add database**:
- Type: `PostgreSQL`
- Host: `db`
- Port: `5432`
- Database name: `weather_db`
- Username: `weather_user`
- Password: `secret`

Нажать **Save**

- [ ] **Шаг 3: Создать дашборд "Погодный мониторинг"**

Перейти в **+ New → Dashboard**, назвать "Погодный мониторинг"

- [ ] **Шаг 4: Добавить вопрос 1 — температура по времени**

**+ New → Question → weather_records**  
- Summarize: нет (raw data)
- Filter: нет
- Visualization: Line chart
- X: `fetched_at`, Y: `temperature`, Series: `source`  
Сохранить как "Температура по источникам", добавить на дашборд

- [ ] **Шаг 5: Добавить вопрос 2 — средний ветер по городам**

**+ New → Question → weather_records**  
- Summarize: Average of `wind_speed`, grouped by `city`
- Visualization: Bar chart  
Сохранить как "Средний ветер по городам", добавить на дашборд

- [ ] **Шаг 6: Добавить вопрос 3 — таблица записей**

**+ New → Question → weather_records**  
- Columns: `city`, `source`, `temperature`, `fetched_at`
- Sort: `fetched_at` DESC
- Visualization: Table  
Сохранить как "Все записи", добавить на дашборд

---

## Task 11: README

**Files:**
- Modify: `README.md`

- [ ] **Шаг 1: Перезаписать `README.md`** со следующей структурой:

  Заголовок: `# WeatherAgg — Агрегатор погодных данных`

  Разделы:
  - **Описание:** Контрольная работа, вариант 8.3. Сбор погоды из OWM + Open-Meteo, хранение в PostgreSQL.
  - **Архитектура** (ASCII-схема):
    ```
    Браузер → Nginx :80
      ├── /           → Flask app :5000
      ├── /analytics  → redirect → Metabase :3000
      └── /admin      → redirect → pgAdmin :5050
    Flask → OpenWeatherMap API, Open-Meteo API, PostgreSQL
    ```
  - **Требования:** Docker, Docker Compose, OWM API ключ
  - **Запуск:**
    ```bash
    cp .env.example .env   # вставить OWM_API_KEY
    docker-compose up -d --build
    ```
  - **Доступ:** таблица с URL для каждого сервиса (localhost, localhost:3000, localhost:5050)
  - **CI/CD:** описание GitHub Actions пайплайна
  - **Остановка:** `docker-compose down` / `docker-compose down -v`
  - **Скриншоты:** секция с изображениями из `docs/screenshots/`

- [ ] **Шаг 2: Добавить скриншоты** (после финального запуска)

Сделать скриншоты:
- Главная страница с результатом сбора
- Страница логов с несколькими записями
- Metabase дашборд
- pgAdmin с таблицей weather_records  

Сохранить в `docs/screenshots/` и добавить в README.

- [ ] **Шаг 3: Commit**

```bash
git add README.md docs/screenshots/
git commit -m "docs: add README with architecture and screenshots"
git push origin main
```

---

## Финальная проверка

- [ ] `docker-compose up -d` поднимает 5 контейнеров без ошибок
- [ ] `http://localhost` — главная страница открывается
- [ ] Форма принимает город, данные от обоих источников сохраняются
- [ ] `/logs` — показывает историю
- [ ] `http://localhost:5050` — pgAdmin, видна таблица `weather_records`
- [ ] `http://localhost:3000` — Metabase, дашборд с 3 графиками
- [ ] GitHub Actions — зелёный `✓` на вкладке Actions
- [ ] Повторный запрос с тем же городом не создаёт дубли

```bash
# Финальная проверка всех тестов
cd app && python -m pytest tests/ -v

# Проверка линтера
flake8 app/ --max-line-length=120
```
