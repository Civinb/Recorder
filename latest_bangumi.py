import requests
meta_url = "https://raw.githubusercontent.com/bangumi/Archive/master/aux/latest.json"
meta = requests.get(meta_url).json()
download_url = meta["browser_download_url"]
time = meta["updated_at"]


