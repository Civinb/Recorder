from flask import Flask, render_template, request, redirect, url_for
from pathlib import Path
import uuid
from rawg_api import rawg_bp

from db import db
from anime import anime_bp, ALLOWED_EXTENSIONS
from game import game_bp
from bangumi_api import bangumi_bp, _migrate_add_bangumi_id


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///main.db"      #Configure the Flask app to use SQLite, with main.db as the database file.
db.init_app(app)


bgpic_dir = Path("static/background_pic")
CURRENT_BG_FILE = Path("current_bg.txt")          # Stores the file name of the currently selected background
DEFAULT_BG = "6aca374e0b6f4305a15ed59cecf1ae70.jpg"


def get_current_bg():
    if CURRENT_BG_FILE.exists():
        name = CURRENT_BG_FILE.read_text(encoding="utf-8").strip()
        if name:
            return name
    return DEFAULT_BG


@app.context_processor                             # Injected into every template automatically, so base.html can use current_bg directly
def inject_bg():
    return {"current_bg": get_current_bg()}



with app.app_context():
    db.create_all()
    _migrate_add_bangumi_id()


app.register_blueprint(anime_bp)                                   #Register blueprints
app.register_blueprint(bangumi_bp)
app.register_blueprint(game_bp)
app.register_blueprint(rawg_bp)


def list_bgpic():
    if not bgpic_dir.exists():
        return []
    bgpic_list = []
    for p in bgpic_dir.iterdir():
        if p.is_file() and p.suffix.lower() in ALLOWED_EXTENSIONS:
            bgpic_list.append(p.name)
    return bgpic_list


@app.route("/home")                                                 #Home page
def home():
    return render_template("pages/home.html")


@app.route("/settings", methods = ["GET", "POST"])                  #Settings page
def settings():
    if request.method == "POST":
        bgpic_file = request.files.get("bg_pic")
        if bgpic_file and bgpic_file.filename:
            ext = Path(bgpic_file.filename).suffix.lower()
            if ext in ALLOWED_EXTENSIONS:
                bgpic_dir.mkdir(parents=True, exist_ok=True)
                safe_name = f"{uuid.uuid4().hex}{ext}"
                bgpic_file.save(bgpic_dir / safe_name)
    images = list_bgpic()
    return render_template("pages/settings.html", images = images)


@app.route("/settings/bgchange/<bg_name>")
def choose_bg(bg_name):
    if bg_name in list_bgpic():                    # Validation: must be an existing image, to block arbitrary values
        CURRENT_BG_FILE.write_text(bg_name, encoding="utf-8")
    return redirect(url_for("settings"))



    





if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)