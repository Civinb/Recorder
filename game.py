from flask import Blueprint, request, redirect, render_template, url_for
from pathlib import Path
import uuid
from datetime import datetime


import anime
from models import Game
from db import db
from rawg_api import _download_rawg_cover


game_bp = Blueprint('game', __name__, url_prefix="/games")
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
gamePic_dir = Path("static/uploads/gamePic")  # Directory where game images are stored


@game_bp.route("/list")
def games():
    games = Game.query.all()
    return render_template("game/games_list.html", games=games)


@game_bp.route("/new", methods=["GET", "POST"])                 
def game_new():
    
    if request.method == "POST":

        name = request.form["name"]
        summary = request.form["summary"]
        reviews = request.form["reviews"]
        igdb_links = request.form["rawg_links"]
        official_links = request.form["official_links"]
        type = request.form["type"]
        status = request.form["status"]
        score = float(request.form["score"])
        rawg_id = request.form.get("id")

        safe_name = None
        image_file = request.files.get("image_file")
        if image_file and image_file.filename:
            ext = Path(image_file.filename).suffix.lower()
            if ext in ALLOWED_EXTENSIONS:
                upload_dir = gamePic_dir
                upload_dir.mkdir(parents=True, exist_ok=True)
                safe_name = f"{uuid.uuid4().hex}{ext}"
                image_file.save(upload_dir / safe_name)
        if not safe_name and rawg_id:
            safe_name = _download_rawg_cover(rawg_id)

        release_date_str = request.form["release_date"]
        if release_date_str:
            release_date = datetime.strptime(release_date_str, "%Y-%m-%d").date()
        else:
            release_date = None

        game_new = Game(name=name, summary=summary, reviews=reviews, igdb_links=igdb_links, official_links=official_links, release_date=release_date, type=type, status=status, score=score, image_url=safe_name)
        db.session.add(game_new)
        db.session.commit()
        return redirect(url_for('game.games'))

    return render_template(
        'game/games_new.html',
        search_api='/api/rawg/search',
        detail_api='/api/rawg/game/',
        id_field='id',
        db_link_id='rawg_links',
        db_link_prefix='https://rawg.io/games/',
        db_link_key='slug',
    )


@game_bp.route("/<int:game_id>")                                 #Handles GET requests for /games/<game_id>, showing the detail page of the game with the given ID.
def game_detail(game_id):
    game = Game.query.get_or_404(game_id)
    return render_template("game/games_detail.html", medium=game)


@game_bp.route("/<int:game_id>/edit", methods=["GET", "POST"])                                 #Edit a single game entry
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
        
        release_date_str = request.form["release_date"]
        if release_date_str:
            game.release_date = datetime.strptime(release_date_str, "%Y-%m-%d").date()
        else:
            game.release_date = None
        
        db.session.commit()
        return redirect(url_for('game.game_detail', game_id=game.id))

    return render_template("game/games_edit.html", medium=game)



@game_bp.route("/<int:game_id>/delete", methods=["POST"])                             #Delete an entry
def game_delete(game_id):
    game = Game.query.get_or_404(game_id)
    if game.image_url:
        old_path = Path(game_bp.root_path) / "static" / "uploads" / "gamePic" / game.image_url
        if old_path.exists():
            old_path.unlink()
    db.session.delete(game)
    db.session.commit()
    return redirect(url_for('game.games'))