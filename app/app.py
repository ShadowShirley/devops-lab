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
