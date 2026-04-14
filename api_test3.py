import requests
import json

url = "https://irctc-insight.p.rapidapi.com/api/v1/train-details"
payload = {"trainNo": "22479"}
headers = {
    "x-rapidapi-key": "83acd5851amsh116782545d4dfd8p1a9951jsnceb680444275",
    "x-rapidapi-host": "irctc-insight.p.rapidapi.com",
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, json=payload, headers=headers)
    print("STATUS:", response.status_code)
    print("BODY:", json.dumps(response.json(), indent=2))
except Exception as e:
    print(e)
