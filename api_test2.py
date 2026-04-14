import requests
import json

url = "https://irctc-insight.p.rapidapi.com/api/v1/train-details"
payload = {"trainNo": "22480"}
headers = {
    "x-rapidapi-key": "a26f2545ddmsh885a99bc9eef333p137471jsn8bf922def494",
    "x-rapidapi-host": "irctc-insight.p.rapidapi.com",
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, json=payload, headers=headers)
    print("STATUS:", response.status_code)
    print("BODY:", json.dumps(response.json(), indent=2))
except Exception as e:
    print(e)
