# Weather Aggregator — Design Spec

**Date:** 2026-04-21  
**Variant:** 8.3 — Агрегатор погодных данных  
**Sources:** OpenWeatherMap API + Open-Meteo API

---

## 1. Goal

Разработать и развернуть систему сбора, нормализации и визуализации погодных данных из двух источников. Пользователь вводит город в браузере, нажимает кнопку — система запрашивает оба API, нормализует данные, сохраняет в PostgreSQL. Метрики доступны через Metabase. БД администрируется через pgAdmin. Все компоненты запускаются через Docker Compose. CI/CD через GitHub Actions.

---

## 2. Architecture

**5 Docker-контейнеров:**

| Сервис | Образ | Порт (внутренний) |
|---|---|---|
| `app` | Python 3.11-slim + Flask | 5000 |
| `nginx` | nginx:alpine | 80 (публичный) |
| `db` | postgres:15 | 5432 |
| `pgadmin` | dpage/pgadmin4 | 5050 |
| `metabase` | metabase/metabase | 3000 |

**Nginx маршрутизация:**

| Путь | Проксирует на |
|---|---|
| `/` | `app:5000` |
| `/analytics` | `metabase:3000` |
| `/admin` | `pgadmin:5050` |

**Внешние API (вызываются Flask-приложением по запросу пользователя):**
- OpenWeatherMap: `https://api.openweathermap.org/data/2.5/weather` (требует API ключ)
- Open-Meteo: `https://api.open-meteo.com/v1/forecast` (без ключа, геокодирование через `https://geocoding-api.open-meteo.com/v1/search`)

---

## 3. Application Structure

```
devops-lab/
├── app/
│   ├── app.py              # Flask routes: GET /, POST /collect, GET /logs
│   ├── parser.py           # fetch_openweathermap(city), fetch_openmeteo(city)
│   ├── normalizer.py       # normalize(raw, source) → WeatherRecord dataclass
│   ├── db.py               # get_conn(), insert_record(), get_logs()
│   ├── templates/
│   │   ├── base.html       # navbar: Главная | Аналитика | Администрирование | Логи
│   │   ├── index.html      # форма ввода города + результат последнего сбора
│   │   └── logs.html       # таблица всех записей из weather_records
│   ├── tests/
│   │   ├── test_parser.py      # mock HTTP responses, проверка полей
│   │   └── test_normalizer.py  # проверка нормализации разных форматов
│   ├── requirements.txt
│   └── Dockerfile
├── nginx/
│   └── nginx.conf
├── .github/
│   └── workflows/
│       └── ci.yml
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 4. Data Model

```sql
CREATE TABLE weather_records (
    id          SERIAL PRIMARY KEY,
    city        VARCHAR(100) NOT NULL,
    source      VARCHAR(50)  NOT NULL,   -- 'openweathermap' | 'open-meteo'
    temperature NUMERIC(5,2),
    humidity    INTEGER,
    wind_speed  NUMERIC(5,2),
    wind_dir    INTEGER,
    description VARCHAR(200),
    fetched_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (city, source, fetched_at)
);
```

**Нормализованная схема `WeatherRecord`** (dataclass в `normalizer.py`):

```python
@dataclass
class WeatherRecord:
    city: str
    source: str
    temperature: float | None
    humidity: int | None
    wind_speed: float | None
    wind_dir: int | None
    description: str | None
```

**Дедупликация:** `INSERT ... ON CONFLICT DO NOTHING`.

---

## 5. Flask Routes

| Метод | Путь | Описание |
|---|---|---|
| GET | `/` | Главная страница с формой и последним результатом |
| POST | `/collect` | Запустить сбор для города из формы, сохранить результат в `session`, редирект на `/` |
| GET | `/logs` | Таблица всех записей из БД |

---

## 6. CI/CD — GitHub Actions

Файл `.github/workflows/ci.yml`, триггер: `push` и `pull_request` на `main`.

**Шаги:**
1. `actions/checkout@v4`
2. `actions/setup-python@v5` (python 3.11)
3. `pip install flake8 pytest`
4. `flake8 app/` — линтинг
5. `pytest app/tests/` — юнит-тесты с mock-ответами (без реальных API)

---

## 7. Environment Variables

```env
OWM_API_KEY=your_openweathermap_api_key
POSTGRES_DB=weather_db
POSTGRES_USER=weather_user
POSTGRES_PASSWORD=secret
PGADMIN_DEFAULT_EMAIL=admin@admin.com
PGADMIN_DEFAULT_PASSWORD=admin
```

---

## 8. Metabase Dashboards

Минимальный дашборд "Погодный мониторинг" с тремя графиками:

1. **Линейный график** — температура по времени, разбивка по `source` (два цвета)
2. **Столбчатый график** — средняя скорость ветра по городам
3. **Таблица расхождений** — разница температур между источниками для одного города и времени

---

## 9. README Structure

- Описание проекта и вариант задания
- Схема архитектуры (ASCII или изображение)
- Требования: Docker, Docker Compose, OWM API ключ
- Инструкция по запуску: `cp .env.example .env` → заполнить ключ → `docker-compose up -d`
- URL доступа: главная, аналитика, администрирование
- Скриншоты всех страниц
- Описание CI/CD

---

## 10. Success Criteria

- [ ] `docker-compose up -d` поднимает все 5 контейнеров без ошибок
- [ ] Главная страница доступна по `http://localhost`
- [ ] Форма принимает город, данные сохраняются в БД от обоих источников
- [ ] `/logs` показывает историю запросов
- [ ] pgAdmin доступен по `/admin`, видна таблица `weather_records`
- [ ] Metabase доступен по `/analytics`, настроен дашборд с 3 графиками
- [ ] GitHub Actions: flake8 и pytest проходят на `push`
- [ ] Дублирующие записи не создаются при повторном запросе
