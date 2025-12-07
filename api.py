# api.py
import requests

API_URL = "https://www.cbr-xml-daily.ru/daily_json.js"


def fetch_rates() -> dict:
    """
    Получить данные о курсах валют через API-запрос.
    Возвращает dict с данными, как отдаёт ЦБ.
    """
    response = requests.get(API_URL, timeout=10)
    response.raise_for_status()
    return response.json()
