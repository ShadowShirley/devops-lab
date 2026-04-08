# Отчёт по лабораторным работам 1–3. DevOps / Git / CI-CD

**Студент:** _(ФИО)_  
**Группа:** _(группа)_  
**Дата:** 2026-04-09

---

## Лабораторная работа № 1. Основы Git

**Цель:** Создать локальный репозиторий, настроить Git, сделать первый коммит.

### Выполненные шаги

**1. Инициализация репозитория**
```bash
mkdir devops-lab
cd devops-lab
git init
```
Результат: создана папка `.git`, репозиторий инициализирован.

**2. Настройка пользователя**
```bash
git config user.name "Developer"
git config user.email "dev@example.com"
```

**3. Создание файлов**
```bash
echo "Hello Git" > hello.txt
```
Также создан файл `script.py` — конвертер температур между шкалами Цельсия, Фаренгейта и Кельвина с графическим интерфейсом (tkinter).

**4. Создание .gitignore**
```
__pycache__/
*.pyc
.env
venv/
*.log
```

**5. Коммит**
```bash
git add hello.txt script.py .gitignore
git commit -m "Example commit"
```
Результат: зафиксировано 3 файла.

**6. Перенос на GitHub**
```bash
git remote add origin git@github.com:ShadowShirley/devops-lab.git
git branch -M main
git push -u origin main
```

### Результат
Репозиторий создан и загружен на GitHub. Файлы `hello.txt`, `script.py`, `.gitignore` присутствуют в удалённом репозитории.

---

## Лабораторная работа № 2. Удалённый репозиторий

**Цель:** Клонировать репозиторий, создать Flask-приложение, освоить ветвление.

### 2.1 Клонирование и README

```bash
git clone git@github.com:ShadowShirley/devops-lab.git
```
Создан файл `README.md` с описанием проекта, добавлен коммит:
```bash
git add README.md
git commit -m "README was added"
git push
```

### 2.2 Создание Flask-приложения

Создана папка `weather-flask-app/` со следующей структурой:
```
weather-flask-app/
├── app.py
├── requirements.txt
└── templates/
    ├── index.html
    ├── weather.html
    └── error.html
```

`requirements.txt`:
```
Flask
requests
python-dotenv
```

Приложение получает текущую погоду по координатам через API `open-meteo.com`.  
Запуск: `python app.py` → `http://127.0.0.1:5000`

```bash
git add .
git commit -m "Initial commit"
git push
```

### 2.3 Ветвление — feature/forecast

```bash
git checkout -b feature/forecast
```
Добавлена функция прогноза на 7 дней (`/forecast`) и шаблон `forecast.html`.

```bash
git add .
git commit -m "Added weather forecast"
git push -u origin feature/forecast
```

Слияние с основной веткой:
```bash
git checkout main
git pull origin main
git merge feature/forecast
git push origin main
```

### 2.4 Индивидуальные задания

**Задание 1 — ветка для домашней страницы:**
```bash
git checkout -b feature/homepage
```
Создана `templates/home.html` с навигацией по всем страницам приложения. Добавлен маршрут `/home` в `app.py`.

**Задание 2 — конфликт веток:**
```bash
git checkout -b feature/branch-a   # изменён заголовок в index.html
git checkout main
git checkout -b feature/branch-b   # то же изменение — другой текст
git checkout main
git merge feature/branch-a         # успешно
git merge feature/branch-b         # CONFLICT
```
Конфликт в файле `weather-flask-app/templates/index.html` разрешён вручную — оставлен оригинальный заголовок.
```bash
git add .
git commit -m "Resolved merge conflict between branch-a and branch-b"
```

**Задание 3 — клонирование по другому пути:**
```bash
git clone /home/niko/code/devops-lab /home/niko/code/devops-lab-clone
cd devops-lab-clone
git checkout -b feature/dynamic-coords
```
Внесены изменения в `app.py` (поддержка динамических координат для `/forecast`). Ветка слита и изменения отправлены в основной репозиторий.

**Задание 4 — тег версии:**
```bash
git tag -a v1.0.0 -m "Release version 1.0.0: basic weather functionality"
git push origin --tags
```
Тег `v1.0.0` отображается в разделе **Releases** на GitHub.

### Результат
На GitHub присутствуют ветки: `main`, `feature/forecast`, `feature/homepage`, `feature/branch-a`, `feature/branch-b`. Тег `v1.0.0` создан.

---

## Лабораторная работа № 3. CI/CD

**Цель:** Настроить автоматическое тестирование проекта через GitHub Actions.

### 3.1 Обновление зависимостей

`weather-flask-app/requirements.txt`:
```
Flask
requests
python-dotenv
pytest
flake8
flask
```

### 3.2 Тесты

Создан файл `weather-flask-app/tests/test_basic.py` с тремя тестами:
- `test_import_app` — проверяет, что приложение импортируется без ошибок
- `test_weather_codes` — проверяет корректность функции `get_weather_description`
- `test_files_exist` — проверяет наличие всех необходимых файлов проекта

Локальный запуск:
```bash
cd weather-flask-app
pytest tests/ -v
```
Результат: **3 passed**.

### 3.3 Файл setup.py

```python
from setuptools import setup, find_packages
setup(
    name="weather-flask-app",
    version="1.0.0",
    packages=find_packages(),
    install_requires=["Flask", "requests"],
)
```

### 3.4 Файл .flake8

```ini
[flake8]
max-line-length = 120
exclude = .git, __pycache__, venv, .github, .pytest_cache, *.pyc
ignore = E501, W503, E203
```

### 3.5 GitHub Actions — ci.yml

Создан файл `.github/workflows/ci.yml`:
```yaml
name: CI
on:
  push:
    branches: [ master, main ]
  pull_request:
    branches: [ master, main ]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r weather-flask-app/requirements.txt
      - name: Lint with flake8
        run: flake8 weather-flask-app/ --config=.flake8
      - name: Run tests
        run: cd weather-flask-app && pytest tests/ -v
```

```bash
git add .
git commit -m "Added CI/CD actions"
git push
```

### Результат
После `git push` во вкладке **Actions** на GitHub отображается статус `success` — все тесты пройдены, линтер не нашёл ошибок.

---

## Вывод

В ходе выполнения лабораторных работ были освоены:
- инициализация и настройка локального Git-репозитория;
- работа с удалённым репозиторием GitHub (push, pull, clone);
- ветвление, слияние веток и разрешение конфликтов;
- создание Flask-приложения с несколькими маршрутами и HTML-шаблонами;
- написание автоматических тестов с использованием pytest;
- настройка CI-пайплайна через GitHub Actions (линтинг + тесты при каждом push).
