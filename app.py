import uuid
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import enum
from datetime import datetime
from werkzeug.utils import secure_filename
from pathlib import Path


ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
db = SQLAlchemy(app)


class status(enum.Enum):
    WACHING = "Watching"
    COMPLETED = "Completed"
    PLANNING = "Planning"
    DROPPED = "Dropped"
    ON_HOLD = "On Hold"
    DEFAULT = "Default"


class type(enum.Enum):
    TV = "TV"
    MOVIE = "Movie"
    OVA = "OVA"



class Anime(db.Model):
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


@app.route("/animes/new", methods=["GET", "POST"])
def anime_new():
    
    if request.method == "POST":
        
        name = request.form["name"]
        summary = request.form["summary"]
        reviews = request.form["reviews"]
        bangumi_links = request.form["bangumi_links"]
        official_links = request.form["official_links"]
        type = request.form["type"]
        status = request.form["status"]
        score = request.form["score"]
        broadcast_date_str = request.form["broadcast_date"]
        
        image_file = request.files["image_file"]
        image_filename = None
        if image_file and image_file.filename:
            ext = Path(image_file.filename).suffix.lower()
            if ext in ALLOWED_EXTENSIONS:
                upload_dir = Path("static/uploads")
                upload_dir.mkdir(parents=True, exist_ok=True)
                safe_name = f"{uuid.uuid4().hex}{ext}"
                image_file.save(upload_dir / safe_name)
        
        if broadcast_date_str:
            broadcast_date = datetime.strptime(broadcast_date_str, "%Y-%m-%d").date()
        else:
            broadcast_date = None

        anime_new = Anime(name=name, summary=summary, reviews=reviews, bangumi_links=bangumi_links, official_links=official_links, broadcast_date=broadcast_date, type=type, status=status, score=score, image_url=safe_name)
        db.session.add(anime_new)
        db.session.commit()
        return redirect(url_for('animes'))
    
    return render_template('animes_new.html')





if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)