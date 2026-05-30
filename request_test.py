import requests
data = {"username": "alice", "pwd": "123456"}
resp = requests.post("http://127.0.0.1:5000/home?pwd=123456", data=data)

url1 = "http://127.0.0.1:5000/home"
data1 = {"username": "alice", "pwd": 25}
resp1 = requests.post(url1, json=data1)