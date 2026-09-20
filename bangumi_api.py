from flask import Blueprint, request, jsonify, current_app
import requests
from pathlib import Path
import uuid
from db import db
from sqlalchemy import inspect


BANGUMI_API_BASE = "https://api.bgm.tv/v0"
BANGUMI_UA = "Recorder/0.1 (https://github.com/Civinb/Recorder.git)"
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
bangumi_bp = Blueprint('bangumi', __name__, url_prefix="/api/bangumi")

@bangumi_bp.route("/search", methods=["POST", "GET"])
def anime_search():
    """Search for anime through the Bangumi API"""
    keyword = request.args.get("query", "")
    try:
        response = requests.post(
            f"{BANGUMI_API_BASE}/search/subjects",
            params={
                "limit": 20, "offset": 0
            },
            json={
                "keyword": keyword,
                "filter": {
                    "type": [2]
                },
            },
            headers={"User-Agent": BANGUMI_UA},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return jsonify({"count": data["total"], "results": data["data"]})
    except requests.exceptions.RequestException as e:
        print(f"Bangumi API request failed: {e}")   # <- switched to print so it also runs outside Flask
        return jsonify({"count": 0, "results": []}), 502
    

@bangumi_bp.route("/anime/<int:anime_id>", methods=["GET"])
def get_anime_details(anime_id: int):
    try:
        response = requests.get(
            f"{BANGUMI_API_BASE}/subjects/{anime_id}",
            headers={"User-Agent": BANGUMI_UA},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Bangumi API request failed: {e}")
        return None

    
def _download_bangumi_cover(subject_id: int) -> str | None:
    """Call the Bangumi API for the cover URL, download it to static/uploads/animePic/ and return the file name"""
    try:
        r = requests.get(
            f"{BANGUMI_API_BASE}/subjects/{subject_id}",
            headers={"User-Agent": BANGUMI_UA},
            timeout=10,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        img_url = (data.get("images") or {}).get("large")
        if not img_url:
            return None
        img_resp = requests.get(img_url, headers={"User-Agent": BANGUMI_UA}, timeout=15)
        if img_resp.status_code != 200:
            return None
        ext = Path(img_url).suffix.lower() or ".jpg"
        if ext not in ALLOWED_EXTENSIONS:
            ext = ".jpg"
        upload_dir = Path(bangumi_bp.root_path) / "static" / "uploads" / "animePic"
        upload_dir.mkdir(parents=True, exist_ok=True)
        safe_name = f"{uuid.uuid4().hex}{ext}"
        (upload_dir / safe_name).write_bytes(img_resp.content)
        return safe_name
    except Exception as e:
        current_app.logger.warning(f"Failed to download the bangumi cover (id={subject_id}): {e}")
        return None
    

def _migrate_add_bangumi_id():
    # Use SQLAlchemy's inspector to check the columns.
    inspector = inspect(db.engine)
    if "anime" not in inspector.get_table_names():
        return
    cols = [c["name"] for c in inspector.get_columns("anime")]
    if "bangumi_id" not in cols:
        with db.engine.connect() as conn:
            conn.exec_driver_sql("ALTER TABLE anime ADD COLUMN bangumi_id INTEGER")
            conn.commit()