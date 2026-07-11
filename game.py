from flask import Blueprint, request, redirect, render_template, url_for
from pathlib import Path
import uuid
from datetime import datetime

import anime
from models import Game
from db import db



game_bp = Blueprint('game', __name__, url_prefix="/games")
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
gamePic_dir = Path("static/uploads/gamePic")  # 游戏图片存放目录


@game_bp.route("/list")
def games():
    games = Game.query.all()
    return render_template("games_list.html", games=games)


@game_bp.route("/new", methods=["GET", "POST"])                 
def game_new():
    
    if request.method == "POST":

        name = request.form["name"]
        summary = request.form["summary"]
        reviews = request.form["reviews"]
        igdb_links = request.form["igdb_links"]
        official_links = request.form["official_links"]
        type = request.form["type"]
        status = request.form["status"]
        score = float(request.form["score"])


        safe_name = None
        image_file = request.files.get("image_file")
        if image_file and image_file.filename:
            ext = Path(image_file.filename).suffix.lower()
            if ext in ALLOWED_EXTENSIONS:
                upload_dir = gamePic_dir
                upload_dir.mkdir(parents=True, exist_ok=True)
                safe_name = f"{uuid.uuid4().hex}{ext}"
                image_file.save(upload_dir / safe_name)

        release_date_str = request.form["release_date"]
        if release_date_str:
            release_date = datetime.strptime(release_date_str, "%Y-%m-%d").date()
        else:
            release_date = None

        game_new = Game(name=name, summary=summary, reviews=reviews, igdb_links=igdb_links, official_links=official_links, release_date=release_date, type=type, status=status, score=score, image_url=safe_name)
        db.session.add(game_new)
        db.session.commit()
        return redirect(url_for('game.games'))

    return render_template('games_new.html')


@game_bp.route("/<int:game_id>")                                 #处理/games/<game_id>路径的GET请求，用于显示指定ID的游戏详情页面。
def game_detail(game_id):
    game = Game.query.get_or_404(game_id)
    return render_template("games_detail.html", game=game)


@game_bp.route("/<int:game_id>/edit", methods=["GET", "POST"])                                 #单个game条目编辑
def game_edit(game_id):
    game = Game.query.get_or_404(game_id)
    if request.method == "POST":
        game.name = request.form["name"]
        game.summary = request.form["summary"]
        game.reviews = request.form["reviews"]
        game.igdb_links = request.form["igdb_links"]
        game.official_links = request.form["official_links"]
        game.type = request.form["type"]
        game.status = request.form["status"]
        game.score = float(request.form["score"])

        image_file = request.files["image_file"]
        if image_file and image_file.filename:
            ext = Path(image_file.filename).suffix.lower()
            if ext in ALLOWED_EXTENSIONS:
                upload_dir = gamePic_dir
                upload_dir.mkdir(parents=True, exist_ok=True)
                safe_name = f"{uuid.uuid4().hex}{ext}"
                image_file.save(upload_dir / safe_name)
                if game.image_url:
                    old_path = upload_dir / game.image_url
                    if old_path.exists():
                        old_path.unlink()
                game.image_url = safe_name
        
        broadcast_date_str = request.form["broadcast_date"]
        if broadcast_date_str:
            game.broadcast_date = datetime.strptime(broadcast_date_str, "%Y-%m-%d").date()
        else:
            game.broadcast_date = None
        
        db.session.commit()
        return redirect(url_for('game.game_detail', game_id=game.id))

    return render_template("games_edit.html", game=game)



@game_bp.route("/<int:game_id>/delete", methods=["POST"])                             #条目删除
def game_delete(game_id):
    game = Game.query.get_or_404(game_id)
    if game.image_url:
        old_path = Path(game_bp.root_path) / "static" / "uploads" / "gamePic" / game.image_url
        if old_path.exists():
            old_path.unlink()
    db.session.delete(game)
    db.session.commit()
    return redirect(url_for('game.games'))