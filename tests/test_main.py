# tests/test_main.py
import types
import pytest
import main


class DummyVar:
    def __init__(self, value=None):
        self._value = value

    def get(self):
        return self._value

    def set(self, value):
        self._value = value


class DummyLabel:
    def __init__(self):
        self.text = ""

    def config(self, **kwargs):
        if "text" in kwargs:
            self.text = kwargs["text"]


class DummyCombo:
    def __init__(self):
        self.values = None

    def __setitem__(self, key, value):
        if key == "values":
            self.values = value


class DummyMessageBox:
    def __init__(self):
        self.errors = []
        self.infos = []

    def showerror(self, title, message):
        self.errors.append((title, message))

    def showinfo(self, title, message):
        self.infos.append((title, message))


def make_dummy_app():
    app = types.SimpleNamespace()
    app.loan_var = DummyVar()
    app.loan_time_var = DummyVar()
    app.annual_interest_var = DummyVar()
    app.monthly_label = DummyLabel()
    app.loan_sum_label = DummyLabel()
    app.interest_label = DummyLabel()
    app.base_var = DummyVar("RUB")
    app.target_var = DummyVar("USD")
    app.result_label = DummyLabel()
    app.target_entry = DummyCombo()
    app.last_monthly_payment = 0.0
    app.logs = []

    def log(message: str):
        app.logs.append(message)

    app.log = log
    app.is_loan_invalid = lambda value, message: False
    return app


def test_calculate_loan_success(monkeypatch):
    dummy_messagebox = DummyMessageBox()
    monkeypatch.setattr(main, "messagebox", dummy_messagebox)

    app = make_dummy_app()
    app.loan_var.set(100000.0)
    app.loan_time_var.set(12)
    app.annual_interest_var.set(12.0)

    main.CurrencyConverterApp.calculate_loan(app)

    assert app.last_monthly_payment == pytest.approx(8884.88, rel=1e-3)

    assert "Ежемесячный платёж" in app.monthly_label.text
    parts = app.monthly_label.text.split()
    value = float(parts[2])
    assert value == pytest.approx(8884.88, rel=1e-3)


def test_calculate_loan_invalid_loan_amount(monkeypatch):
    dummy_messagebox = DummyMessageBox()
    monkeypatch.setattr(main, "messagebox", dummy_messagebox)

    app = make_dummy_app()
    app.loan_var.set(0)
    app.loan_time_var.set(12)
    app.annual_interest_var.set(12.0)

    app.is_loan_invalid = lambda value, message: True

    main.CurrencyConverterApp.calculate_loan(app)

    assert app.last_monthly_payment == 0.0


def test_convert_success(monkeypatch):
    dummy_messagebox = DummyMessageBox()
    monkeypatch.setattr(main, "messagebox", dummy_messagebox)

    app = make_dummy_app()
    app.last_monthly_payment = 10000.0
    app.target_var.set("USD")
    app.base_var.set("RUB")

    monkeypatch.setattr(main, "get_saved_rate", lambda currency: 100.0)

    main.CurrencyConverterApp.convert(app)

    assert "100.00 USD" in app.result_label.text
    assert dummy_messagebox.errors == []


def test_update_db_success(monkeypatch):
    dummy_messagebox = DummyMessageBox()
    monkeypatch.setattr(main, "messagebox", dummy_messagebox)

    app = make_dummy_app()
    app.target_var.set("USD")

    fake_rates = {
        "Valute": {
            "USD": {"Value": 90.0, "Nominal": 1},
            "EUR": {"Value": 100.0, "Nominal": 1},
        }
    }

    monkeypatch.setattr(main, "fetch_rates", lambda: fake_rates)

    save_calls = []

    def fake_save_rate(id_, code, rate):
        save_calls.append((id_, code, rate))

    monkeypatch.setattr(main, "save_rate", fake_save_rate)

    main.CurrencyConverterApp.update_db(app)

    currencies = {code for _, code, _ in save_calls}
    assert "RUB" in currencies
    assert "USD" in currencies
    assert "EUR" in currencies

    assert sorted(app.target_entry.values) == sorted(["RUB", "USD", "EUR"])
    assert any("Курсы валют обновлены" in msg for msg in app.logs)
