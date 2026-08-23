import os
import requests
from flask import Blueprint, request, jsonify, current_app
import uuid
from db import db
from sqlalchemy import inspect
from pathlib import Path

rawg_bp = Blueprint('rawg', __name__, url_prefix="/api/rawg")
RAWG_API_KEY = os.environ.get("RAWG_API_KEY")  # Set this to your own RAWG API key
RAWG_base_url = "https://api.rawg.io/api"
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}

@rawg_bp.route("/search", methods=["GET"])
def game_search():
    """Search for games through the RAWG API"""
    try:
        response = requests.get(
            f"{RAWG_base_url}/games",
            params={
                "key": RAWG_API_KEY,
                "search": request.args.get("query", ""),
                "page": request.args.get("page", 1, type=int),
                "page_size": request.args.get("page_size", 10, type=int)
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return jsonify({"count": data["count"], "results": data["results"]})
    except requests.exceptions.RequestException as e:
        print(f"RAWG API request failed: {e}")   # <- switched to print so it also runs outside Flask
        return jsonify({"count": 0, "results": []}), 502

@rawg_bp.route("/game/<int:game_id>", methods=["GET"])
def get_game_details(game_id: int):
    """Fetch the game details from the RAWG API"""
    try:
        response = requests.get(
            f"{RAWG_base_url}/games/{game_id}",
            params={"key": RAWG_API_KEY},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"RAWG API request failed: {e}")
        return None


def _download_rawg_cover(game_id: int) -> str | None:
    """Call the RAWG API for the cover URL, download it to static/uploads/gamePic/ and return the file name"""
    try:
        r = requests.get(
            f"{RAWG_base_url}/games/{game_id}",
            params={"key": RAWG_API_KEY},
            timeout=10,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        img_url = data.get("background_image")
        if not img_url:
            return None
        img_resp = requests.get(img_url, timeout=15)
        if img_resp.status_code != 200:
            return None
        ext = Path(img_url).suffix.lower() or ".jpg"
        if ext not in ALLOWED_EXTENSIONS:
            ext = ".jpg"
        upload_dir = Path(rawg_bp.root_path) / "static" / "uploads" / "gamePic"
        upload_dir.mkdir(parents=True, exist_ok=True)
        safe_name = f"{uuid.uuid4().hex}{ext}"
        (upload_dir / safe_name).write_bytes(img_resp.content)
        return safe_name
    except Exception as e:
        current_app.logger.warning(f"Failed to download the RAWG cover (id={game_id}): {e}")
        return None