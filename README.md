# WeatherAgg — Агрегатор погодных данных

**Контрольная работа. Вариант 8.3** — Агрегатор погодных данных из двух источников.

Система собирает, нормализует и сохраняет данные о погоде из OpenWeatherMap и Open-Meteo. Пользователь вводит город в браузере — Flask запрашивает оба API, сохраняет в PostgreSQL. Метрики доступны через Metabase, БД через pgAdmin.

---

## Архитектура

```
Браузер → Nginx :80
  ├── /           → Flask app :5000
  ├── /analytics  → redirect → Metabase :3002
  └── /admin      → redirect → pgAdmin :5050
Flask → OpenWeatherMap API, Open-Meteo API, PostgreSQL
```

**5 Docker-контейнеров:** `app`, `nginx`, `db`, `pgadmin`, `metabase`

---

## Требования

- Docker и Docker Compose v2
- OWM API ключ (бесплатно на [openweathermap.org](https://openweathermap.org/api))

---

## Запуск

```bash
cp .env.example .env
# Вставить реальный OWM_API_KEY в .env
docker-compose up -d --build
```

---

## Доступ

| Сервис | URL |
|---|---|
| Главная | http://localhost |
| Логи | http://localhost/logs |
| Metabase (аналитика) | http://localhost:3002 |
| pgAdmin (БД) | http://localhost:5050 |

---

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`):
- Триггер: `push` и `pull_request` на `main`
- Шаги: checkout → setup-python 3.11 → flake8 lint → pytest

---

## Остановка

```bash
docker-compose down          # остановить, сохранить данные
docker-compose down -v       # остановить и удалить volumes
```

---

## Скриншоты

![Главная страница](docs/screenshots/Screenshot%20from%202026-04-22%2010-04-35.png)

![Логи](docs/screenshots/Screenshot%20from%202026-04-22%2010-04-52.png)

![Metabase дашборд](docs/screenshots/Screenshot%20from%202026-04-22%2010-06-25.png)

![pgAdmin](docs/screenshots/Screenshot%20from%202026-04-22%2010-06-39.png)

