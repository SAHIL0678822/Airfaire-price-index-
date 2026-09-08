import requests

API_KEY = "653af926b5a0d294fd61909d07e0f8e5234bce15cec9ee04e7411f5b8128dacd"

params = {
    "engine": "google_flights",
    "departure_id": "DEL",
    "arrival_id": "BOM",
    "outbound_date": "2026-09-10",
    "type": "2",
    "api_key": API_KEY,
}

response = requests.get("https://serpapi.com/search", params=params)
print(response.json())
