from flask import Blueprint, request, redirect, render_template, url_for
from pathlib import Path
import uuid
from models import Anime
from db import db
from datetime import datetime
from bangumi_api import _download_bangumi_cover


anime_bp = Blueprint('anime', __name__, url_prefix="/animes")
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}  #允许上传的图片文件扩展名集合，包含了常见的图片格式，如JPG、JPEG、PNG、GIF和WEBP等。




@anime_bp.route("/list")                                         #animeslist页面
def animes():
    animes = Anime.query.all()
    return render_template("animes_list.html", animes=animes)


@anime_bp.route("/new", methods=["GET", "POST"])                 #处理/animes/new路径的GET和POST请求，GET请求用于显示添加新动漫的表单页面，POST请求用于处理表单提交的数据并将新动漫添加到数据库中。
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
        return redirect(url_for('anime.animes'))

    return render_template('animes_new.html')




@anime_bp.route("/<int:anime_id>")                                 #处理/animes/<anime_id>路径的GET请求，用于显示指定ID的动漫详情页面。
def anime_detail(anime_id):
    anime = Anime.query.get_or_404(anime_id)
    return render_template("animes_detail.html", anime=anime)



@anime_bp.route("/<int:anime_id>/edit", methods=["GET", "POST"])                                 #单个anime条目编辑
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
        return redirect(url_for('anime.anime_detail', anime_id=anime.id))

    return render_template("animes_edit.html", anime=anime)



@anime_bp.route("/<int:anime_id>/delete", methods=["POST"])                             #条目删除
def anime_delete(anime_id):
    anime = Anime.query.get_or_404(anime_id)
    if anime.image_url:
        old_path = Path(anime_bp.root_path) / "static" / "uploads" / anime.image_url
        if old_path.exists():
            old_path.unlink()
    db.session.delete(anime)
    db.session.commit()
    return redirect(url_for('anime.animes'))