import uuid
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import enum
from datetime import datetime
from werkzeug.utils import secure_filename
from pathlib import Path


ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}  #允许上传的图片文件扩展名集合，包含了常见的图片格式，如JPG、JPEG、PNG、GIF和WEBP等。


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

with app.app_context():
    db.create_all()


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
        
        image_file = request.files["image_file"]
        if image_file and image_file.filename:
            ext = Path(image_file.filename).suffix.lower()
            if ext in ALLOWED_EXTENSIONS:
                upload_dir = Path("static/uploads")
                upload_dir.mkdir(parents=True, exist_ok=True)
                safe_name = f"{uuid.uuid4().hex}{ext}"
                image_file.save(upload_dir / safe_name)
        
        broadcast_date_str = request.form["broadcast_date"]
        if broadcast_date_str:
            broadcast_date = datetime.strptime(broadcast_date_str, "%Y-%m-%d").date()
        else:
            broadcast_date = None

        anime_new = Anime(name=name, summary=summary, reviews=reviews, bangumi_links=bangumi_links, official_links=official_links, broadcast_date=broadcast_date, type=type, status=status, score=score, image_url=safe_name)
        db.session.add(anime_new)
        db.session.commit()
        return redirect(url_for('animes'))
    
    return render_template('animes_new.html')



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


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)