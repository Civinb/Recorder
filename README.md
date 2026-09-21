# Recorder

A local Flask app for tracking the anime you watch and the games you play. Search [Bangumi](https://bgm.tv/) (anime) or [RAWG](https://rawg.io/) (games) to fill in an entry and download its cover automatically.

## Getting started

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

$env:RAWG_API_KEY = "your-key"   # optional, for game search: https://rawg.io/apidocs
python app.py
```

Open <http://127.0.0.1:5000/home>. The SQLite database (`main.db`) is created on first start.

Anime search uses the public Bangumi API and needs no key.

## Project structure

```
app.py            # Entry point, settings page
db.py / models.py # SQLAlchemy models
anime.py game.py  # CRUD routes (/animes, /games)
bangumi_api.py    # Bangumi search + cover download (/api/bangumi)
rawg_api.py       # RAWG search + cover download (/api/rawg)
templates/ static/
```
