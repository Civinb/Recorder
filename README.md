# Recorder

A local Flask app for tracking the anime you watch and the games you play. Each entry stores a name, cover, type, release date, your score, review and links.

Instead of typing everything by hand, you can search [Bangumi](https://bgm.tv/) for anime (through a locally built full-text index) and [RAWG](https://rawg.io/) for games (through their API) — picking a result fills in the form and downloads the cover.

## Features

- Full CRUD for anime and game entries, with local cover upload
- List view with name search, year/type/status filters, sortable columns and pagination (10/25/50)
- Bangumi: build a local SQLite + FTS5 index from the official data dump, search it offline, auto-fetch covers
- RAWG: live game search and cover download
- Switchable background images on the Settings page

## Tech stack

Python 3, Flask 3.1 (blueprints + Jinja2), Flask-SQLAlchemy over SQLite, `sqlite3` FTS5 for the Bangumi index, `requests` for the external APIs, vanilla JS on the front end.

## Project structure

```
app.py            # Entry point: config, blueprints, background image
db.py / models.py # SQLAlchemy instance; Anime & Game models
anime.py game.py  # CRUD routes (/animes, /games)
bangumi_api.py    # Bangumi routes + cover download (/api/bangumi)
bangumi_index.py  # Dump parsing and FTS5 index building
rawg_api.py       # RAWG routes + cover download (/api/rawg)
templates/        # base.html, shared/, anime/, game/, pages/
static/           # css, js, icons, background_pic, uploads, bangumi_data
```

## Getting started

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

$env:RAWG_API_KEY = "your-key"   # optional, for game search: https://rawg.io/apidocs
python app.py
```

Then open <http://127.0.0.1:5000/home>. The database is created automatically on first start — no manual schema step.

## Bangumi index

Anime search runs offline against a local index that has to be built once:

1. On **Settings**, click **Sync** to download the latest Bangumi data dump.
2. Move the zip into `static/bangumi_data/`.
3. Click **Extract / Rebuild Index** and wait 1–3 minutes with the page open.

Repeat to refresh the data; the index is rebuilt from scratch each time.
