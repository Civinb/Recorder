from flask import Blueprint, request, redirect, render_template, url_for
from pathlib import Path
import uuid
from datetime import datetime


from models import Anime
from db import db
from bangumi_api import _download_bangumi_cover


anime_bp = Blueprint('anime', __name__, url_prefix="/animes")
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}  #Set of image file extensions allowed for upload, covering the common formats: JPG, JPEG, PNG, GIF and WEBP.




@anime_bp.route("/list")                                         #animes list page
def animes():
    animes = Anime.query.all()
    return render_template("anime/animes_list.html", animes=animes)


@anime_bp.route("/new", methods=["GET", "POST"])                 #Handles GET and POST requests for /animes/new: GET renders the form page for adding a new anime, POST processes the submitted data and stores the new anime in the database.
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
                upload_dir = Path("static/uploads/animePic")
                upload_dir.mkdir(parents=True, exist_ok=True)
                safe_name = f"{uuid.uuid4().hex}{ext}"
                image_file.save(upload_dir / safe_name)

        # No image uploaded manually but a bangumi_id is present -> fetch the cover automatically
        if not safe_name and bangumi_id:
            safe_name = _download_bangumi_cover(bangumi_id)

        release_date_str = request.form["release_date"]
        if release_date_str:
            release_date = datetime.strptime(release_date_str, "%Y-%m-%d").date()
        else:
            release_date = None

        anime_new = Anime(name=name, summary=summary, reviews=reviews, bangumi_links=bangumi_links, official_links=official_links, release_date=release_date, type=type, status=status, score=score, image_url=safe_name, bangumi_id=bangumi_id)
        db.session.add(anime_new)
        db.session.commit()
        return redirect(url_for('anime.animes'))

    return render_template('anime/animes_new.html')




@anime_bp.route("/<int:anime_id>")                                 #Handles GET requests for /animes/<anime_id>, showing the detail page of the anime with the given ID.
def anime_detail(anime_id):
    anime = Anime.query.get_or_404(anime_id)
    return render_template("anime/animes_detail.html", medium=anime)



@anime_bp.route("/<int:anime_id>/edit", methods=["GET", "POST"])                                 #Edit a single anime entry
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
                upload_dir = Path("static/uploads/animePic")
                upload_dir.mkdir(parents=True, exist_ok=True)
                safe_name = f"{uuid.uuid4().hex}{ext}"
                image_file.save(upload_dir / safe_name)
                if anime.image_url:
                    old_path = upload_dir / anime.image_url
                    if old_path.exists():
                        old_path.unlink()
                anime.image_url = safe_name
        
        release_date_str = request.form["release_date"]
        if release_date_str:
            anime.release_date = datetime.strptime(release_date_str, "%Y-%m-%d").date()
        else:
            anime.release_date = None
        
        db.session.commit()
        return redirect(url_for('anime.anime_detail', anime_id=anime.id))

    return render_template("anime/animes_edit.html", medium=anime)



@anime_bp.route("/<int:anime_id>/delete", methods=["POST"])                             #Delete an entry
def anime_delete(anime_id):
    anime = Anime.query.get_or_404(anime_id)
    if anime.image_url:
        old_path = Path(anime_bp.root_path) / "static" / "uploads" / "animePic" / anime.image_url
        if old_path.exists():
            old_path.unlink()
    db.session.delete(anime)
    db.session.commit()
    return redirect(url_for('anime.animes'))