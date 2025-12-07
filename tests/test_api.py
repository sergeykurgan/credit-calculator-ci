# tests/test_api.py
import pytest
import requests
import api


class DummyResponse:
    def __init__(self, data=None, http_error=None):
        self._data = data or {}
        self._http_error = http_error

    def raise_for_status(self):
        if self._http_error:
            raise self._http_error

    def json(self):
        return self._data


def test_fetch_rates_success(monkeypatch):
    dummy_data = {"Valute": {"USD": {"Value": 90.0, "Nominal": 1}}}

    def fake_get(url, timeout):
        assert url == api.API_URL
        return DummyResponse(data=dummy_data)

    monkeypatch.setattr(api.requests, "get", fake_get)

    data = api.fetch_rates()
    assert "Valute" in data
    assert data["Valute"]["USD"]["Value"] == 90.0


def test_fetch_rates_http_error(monkeypatch):
    def fake_get(url, timeout):
        return DummyResponse(http_error=requests.HTTPError("HTTP error"))

    monkeypatch.setattr(api.requests, "get", fake_get)

    with pytest.raises(requests.HTTPError):
        api.fetch_rates()


def test_fetch_rates_connection_error(monkeypatch):
    def fake_get(url, timeout):
        raise requests.ConnectionError("connection error")

    monkeypatch.setattr(api.requests, "get", fake_get)

    with pytest.raises(requests.ConnectionError):
        api.fetch_rates()
