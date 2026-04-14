import http.client
import json

conn = http.client.HTTPSConnection("irctc-insight.p.rapidapi.com")

payload = "{\"trainNo\":\"22924\"}"

headers = {
    'x-rapidapi-key': "a26f2545ddmsh885a99bc9eef333p137471jsn8bf922def494",
    'x-rapidapi-host': "irctc-insight.p.rapidapi.com",
    'Content-Type': "application/json"
}

conn.request("POST", "/api/v1/train-details", payload, headers)

res = conn.getresponse()
data = res.read()
print(json.dumps(json.loads(data.decode("utf-8")), indent=2))
