from flask import Blueprint, request, jsonify, current_app
import requests
from pathlib import Path
import bangumi_index
import uuid
from db import db


BANGUMI_API_BASE = "https://api.bgm.tv/v0"
BANGUMI_UA = "Recorder/0.1 (https://github.com/Civinb/Recorder.git)"
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
bangumi_bp = Blueprint('bangumi', __name__, url_prefix="/api/bangumi")



@bangumi_bp.route("/index/info")
def bangumi_index_info():
    return jsonify(bangumi_index.index_info())



@bangumi_bp.route("/index/build", methods=["POST"])
def bangumi_index_build():
    try:
        result = bangumi_index.build_index()
        return jsonify({"ok": True, **result})
    except FileNotFoundError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        current_app.logger.exception("构建 bangumi 索引失败")
        return jsonify({"ok": False, "error": str(e)}), 500


@bangumi_bp.route("/search")
def bangumi_search():
    q = request.args.get("q", "")
    try:
        results = bangumi_index.search(q, limit=15)
        return jsonify({"ok": True, "results": results})
    except FileNotFoundError as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@bangumi_bp.route("/subject/<int:subject_id>")
def bangumi_subject(subject_id):
    data = bangumi_index.get_subject(subject_id)
    if not data:
        return jsonify({"ok": False, "error": "未找到该条目"}), 404
    return jsonify({"ok": True, "subject": data})


def _download_bangumi_cover(subject_id: int) -> str | None:
    """调 Bangumi API 拿封面 URL 并下载到 static/uploads/，返回文件名"""
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
        upload_dir = Path(bangumi_bp.root_path) / "static" / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        safe_name = f"{uuid.uuid4().hex}{ext}"
        (upload_dir / safe_name).write_bytes(img_resp.content)
        return safe_name
    except Exception as e:
        current_app.logger.warning(f"下载 bangumi 封面失败 (id={subject_id}): {e}")
        return None
    


    
def _migrate_add_bangumi_id():
    with db.engine.connect() as conn:
        cols = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(anime)").fetchall()]
        if cols and "bangumi_id" not in cols:
            conn.exec_driver_sql("ALTER TABLE anime ADD COLUMN bangumi_id INTEGER")
            conn.commit()