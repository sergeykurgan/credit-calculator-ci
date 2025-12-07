# tests/test_db.py
import sqlite3
import re
import pytest
import db


@pytest.fixture
def test_db_path(tmp_path, monkeypatch):
    # переназначаем путь к БД на временный файл
    db_file = tmp_path / "test_rates.db"
    monkeypatch.setattr(db, "DB_NAME", str(db_file))
    return db_file


@pytest.fixture
def setup_db(test_db_path):
    # инициализация таблицы в тестовой БД
    db.init_db()
    return test_db_path


def test_init_db_creates_table(setup_db):
    conn = sqlite3.connect(db.DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rates'")
    row = cur.fetchone()
    conn.close()
    assert row is not None
    assert row[0] == "rates"


def test_save_rate_new_record(setup_db):
    db.save_rate(1, "USD", 90.5)

    conn = sqlite3.connect(db.DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, currency, rate, fetched_at FROM rates WHERE id = 1")
    row = cur.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == 1
    assert row[1] == "USD"
    assert row[2] == pytest.approx(90.5)


def test_save_rate_update_existing(setup_db):
    db.save_rate(1, "USD", 90.5)
    db.save_rate(1, "USD", 91.0)

    conn = sqlite3.connect(db.DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM rates")
    count = cur.fetchone()[0]
    cur.execute("SELECT rate FROM rates WHERE id = 1")
    rate = cur.fetchone()[0]
    conn.close()

    assert count == 1
    assert rate == pytest.approx(91.0)


def test_save_rate_date_format(setup_db):
    db.save_rate(1, "USD", 90.5)

    conn = sqlite3.connect(db.DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT fetched_at FROM rates WHERE id = 1")
    fetched_at = cur.fetchone()[0]
    conn.close()

    # формат "YYYY-MM-DD HH:MM:SS"
    assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", fetched_at)


def test_get_saved_rate_success(setup_db):
    db.save_rate(1, "USD", 90.5)
    rate = db.get_saved_rate("USD")
    assert rate == pytest.approx(90.5)


def test_get_saved_rate_nonexistent_currency(setup_db):
    rate = db.get_saved_rate("XXX")
    assert rate == 0.0
