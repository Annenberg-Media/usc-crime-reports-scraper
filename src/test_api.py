import requests
import json
from parse import read_and_parse
from decouple import config

url = f"https://data.mongodb-api.com/app/data-wpkwm/endpoint/data/v1/action/insertMany"
print("PARSING CSV TO JSON")
json_data = read_and_parse("./031924.pdf'")
print("JSON DATA: ")
print(json_data)

MONGO_KEY = config("MONGODB_KEY")
# print(MONGO_KEY)
headers = {
    "apiKey": MONGO_KEY,
    "Content-Type": "application/json",
    "Accept": "application/json",
}

payload = {
    "dataSource": "USC-AnnMedia-WebTeam",
    "database": "dps",
    "collection": "dps-test",
    "documents": json_data,
}

print("Sending request:")
response = requests.request("POST", url, headers=headers, json=payload)

print(response.status_code)
print(response.json())
