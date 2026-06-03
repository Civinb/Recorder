import uuid
import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import enum
from datetime import datetime
from werkzeug.utils import secure_filename
from pathlib import Path

import bangumi_index


ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}  #允许上传的图片文件扩展名集合，包含了常见的图片格式，如JPG、JPEG、PNG、GIF和WEBP等。
BANGUMI_API_BASE = "https://api.bgm.tv/v0"
BANGUMI_UA = "Recorder/0.1 (https://github.com/Civinb/Recorder.git)"  # bgm API 要求设置 UA


app = Flask(__name__)                                          
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'      #配置Flask应用程序使用SQLite数据库，并指定数据库文件为main.db。
db = SQLAlchemy(app)


class status(enum.Enum):                                         #动漫状态枚举类，包含了动漫的各种状态，如正在观看、已完成、计划观看、已放弃和搁置等。
    WACHING = "Watching"
    COMPLETED = "Completed"
    PLANNING = "Planning"
    DROPPED = "Dropped"
    ON_HOLD = "On Hold"
    DEFAULT = "Default"


class type(enum.Enum):                                           #动漫类型枚举类，包含了动漫的各种类型，如TV、Movie和OVA等。
    TV = "TV"
    MOVIE = "Movie"
    OVA = "OVA"



class Anime(db.Model):                                           #数据库中的Anime模型，包含了动漫的各种属性，如名称、图片链接、类型、播出日期、简介、评分、评论、标签、相关链接和状态等。
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    image_url = db.Column(db.String(200), nullable=True)
    type = db.Column(db.Enum(type), nullable=False, default=type.TV)
    broadcast_date = db.Column(db.Date, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    score = db.Column(db.Float, nullable=True)
    reviews = db.Column(db.Text, nullable=True)
    tags = db.Column(db.String(200), nullable=True)
    bangumi_links = db.Column(db.String(200), nullable=True)
    official_links = db.Column(db.String(200), nullable=True)
    status = db.Column(db.Enum(status), nullable=False, default=status.DEFAULT)
    bangumi_id = db.Column(db.Integer, nullable=True, index=True)  # 关联的 bangumi subject id

def _migrate_add_bangumi_id():
    """对已存在的 anime 表补 bangumi_id 列（轻量迁移）"""
    with db.engine.connect() as conn:
        cols = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(anime)").fetchall()]
        if cols and "bangumi_id" not in cols:
            conn.exec_driver_sql("ALTER TABLE anime ADD COLUMN bangumi_id INTEGER")
            conn.commit()


with app.app_context():
    db.create_all()
    _migrate_add_bangumi_id()


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
        upload_dir = Path(app.root_path) / "static" / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        safe_name = f"{uuid.uuid4().hex}{ext}"
        (upload_dir / safe_name).write_bytes(img_resp.content)
        return safe_name
    except Exception as e:
        app.logger.warning(f"下载 bangumi 封面失败 (id={subject_id}): {e}")
        return None


@app.route("/animes")                                   
def animes():
    animes = Anime.query.all()
    return render_template("animes.html", animes=animes)


@app.route("/animes/new", methods=["GET", "POST"])                 #处理/animes/new路径的GET和POST请求，GET请求用于显示添加新动漫的表单页面，POST请求用于处理表单提交的数据并将新动漫添加到数据库中。
def anime_new():
    
    if request.method == "POST":

        name = request.form["name"]
        summary = request.form["summary"]
        reviews = request.form["reviews"]
        bangumi_links = request.form["bangumi_links"]
        official_links = request.form["official_links"]
        type = request.form["type"]
        status = request.form["status"]
        score = float(request.form["score"])
        bangumi_id_raw = request.form.get("bangumi_id", "").strip()
        bangumi_id = int(bangumi_id_raw) if bangumi_id_raw.isdigit() else None

        safe_name = None
        image_file = request.files.get("image_file")
        if image_file and image_file.filename:
            ext = Path(image_file.filename).suffix.lower()
            if ext in ALLOWED_EXTENSIONS:
                upload_dir = Path("static/uploads")
                upload_dir.mkdir(parents=True, exist_ok=True)
                safe_name = f"{uuid.uuid4().hex}{ext}"
                image_file.save(upload_dir / safe_name)

        # 用户未手动上传图片但有 bangumi_id → 自动抓封面
        if not safe_name and bangumi_id:
            safe_name = _download_bangumi_cover(bangumi_id)

        broadcast_date_str = request.form["broadcast_date"]
        if broadcast_date_str:
            broadcast_date = datetime.strptime(broadcast_date_str, "%Y-%m-%d").date()
        else:
            broadcast_date = None

        anime_new = Anime(name=name, summary=summary, reviews=reviews, bangumi_links=bangumi_links, official_links=official_links, broadcast_date=broadcast_date, type=type, status=status, score=score, image_url=safe_name, bangumi_id=bangumi_id)
        db.session.add(anime_new)
        db.session.commit()
        return redirect(url_for('animes'))

    return render_template('animes_new.html')


# ---------------- Bangumi 索引相关 API ----------------

@app.route("/api/bangumi/index/info")
def bangumi_index_info():
    return jsonify(bangumi_index.index_info())


@app.route("/api/bangumi/index/build", methods=["POST"])
def bangumi_index_build():
    try:
        result = bangumi_index.build_index()
        return jsonify({"ok": True, **result})
    except FileNotFoundError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        app.logger.exception("构建 bangumi 索引失败")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/bangumi/search")
def bangumi_search():
    q = request.args.get("q", "")
    try:
        results = bangumi_index.search(q, limit=15)
        return jsonify({"ok": True, "results": results})
    except FileNotFoundError as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/bangumi/subject/<int:subject_id>")
def bangumi_subject(subject_id):
    data = bangumi_index.get_subject(subject_id)
    if not data:
        return jsonify({"ok": False, "error": "未找到该条目"}), 404
    return jsonify({"ok": True, "subject": data})



@app.route("/animes/<int:anime_id>")                                 #处理/animes/<anime_id>路径的GET请求，用于显示指定ID的动漫详情页面。
def anime_detail(anime_id):
    anime = Anime.query.get_or_404(anime_id)
    return render_template("animes_detail.html", anime=anime)


@app.route("/animes/<int:anime_id>/edit", methods=["GET", "POST"])
def anime_edit(anime_id):
    anime = Anime.query.get_or_404(anime_id)
    if request.method == "POST":
        anime.name = request.form["name"]
        anime.summary = request.form["summary"]
        anime.reviews = request.form["reviews"]
        anime.bangumi_links = request.form["bangumi_links"]
        anime.official_links = request.form["official_links"]
        anime.type = request.form["type"]
        anime.status = request.form["status"]
        anime.score = float(request.form["score"])
        
        image_file = request.files["image_file"]
        if image_file and image_file.filename:
            ext = Path(image_file.filename).suffix.lower()
            if ext in ALLOWED_EXTENSIONS:
                upload_dir = Path("static/uploads")
                upload_dir.mkdir(parents=True, exist_ok=True)
                safe_name = f"{uuid.uuid4().hex}{ext}"
                image_file.save(upload_dir / safe_name)
                if anime.image_url:
                    old_path = upload_dir / anime.image_url
                    if old_path.exists():
                        old_path.unlink()
                anime.image_url = safe_name
        
        broadcast_date_str = request.form["broadcast_date"]
        if broadcast_date_str:
            anime.broadcast_date = datetime.strptime(broadcast_date_str, "%Y-%m-%d").date()
        else:
            anime.broadcast_date = None
        
        db.session.commit()
        return redirect(url_for('anime_detail', anime_id=anime.id))

    return render_template("animes_edit.html", anime=anime)

@app.route("/animes/<int:anime_id>/delete", methods=["POST"])
def anime_delete(anime_id):
    anime = Anime.query.get_or_404(anime_id)
    if anime.image_url:
        old_path = Path(app.root_path) / "static" / "uploads" / anime.image_url
        if old_path.exists():
            old_path.unlink()
    db.session.delete(anime)
    db.session.commit()
    return redirect(url_for('animes'))


@app.route("/settings")
def settings():
    return render_template("settings.html")





if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)