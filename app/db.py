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
