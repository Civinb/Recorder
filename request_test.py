import requests
url = "http://127.0.0.1:5000/power"
data = {"base": "我", "exponent": 41}
resp = requests.post(url, json=data)