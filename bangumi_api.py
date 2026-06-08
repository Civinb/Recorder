from anime import anime_bp
from flask import Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path
from models import Anime
from datetime import datetime
import bangumi_index



@anime_bp.route("/api/bangumi/index/info")
def bangumi_index_info():
    return jsonify(bangumi_index.index_info())


@anime_bp.route("/api/bangumi/index/build", methods=["POST"])
def bangumi_index_build():
    try:
        result = bangumi_index.build_index()
        return jsonify({"ok": True, **result})
    except FileNotFoundError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        anime_bp.logger.exception("构建 bangumi 索引失败")
        return jsonify({"ok": False, "error": str(e)}), 500


@anime_bp.route("/api/bangumi/search")
def bangumi_search():
    q = request.args.get("q", "")
    try:
        results = bangumi_index.search(q, limit=15)
        return jsonify({"ok": True, "results": results})
    except FileNotFoundError as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@anime_bp.route("/api/bangumi/subject/<int:subject_id>")
def bangumi_subject(subject_id):
    data = bangumi_index.get_subject(subject_id)
    if not data:
        return jsonify({"ok": False, "error": "未找到该条目"}), 404
    return jsonify({"ok": True, "subject": data})