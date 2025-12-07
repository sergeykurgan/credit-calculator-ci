# db.py
import sqlite3
from datetime import datetime

# имя файла базы
DB_NAME = "rates.db"


def init_db() -> None:
    """Инициализация БД: создаём таблицу rates, если её нет."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS rates (
            id INTEGER PRIMARY KEY,
            currency TEXT UNIQUE,
            rate REAL NOT NULL,
            fetched_at TEXT NOT NULL
        )
        '''
    )
    conn.commit()
    conn.close()


def save_rate(id: int, target_currency: str, rate: float) -> None:
    """
    Сохранение курса валюты в БД.
    Если такая строка уже есть по id, то обновляем её.
    """
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # запрос из методички
    cur.execute(
        """
        INSERT INTO rates (id, currency, rate, fetched_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            rate = excluded.rate,
            fetched_at = excluded.fetched_at
        """,
        (id, target_currency, rate, date_str),
    )

    conn.commit()
    conn.close()


def get_saved_rate(target_currency: str) -> float:
    """
    Получить курс валюты из БД по её имени (USD, EUR и т.п.).
    Если нет записи – вернём 0.0.
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "SELECT rate FROM rates WHERE currency = ?",
        (target_currency,),
    )
    row = cur.fetchone()
    conn.close()

    if row is None:
        return 0.0
    return float(row[0])
