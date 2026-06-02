from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import enum
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
    broadcast_date = db.Column(db.String(50), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    score = db.Column(db.Float, nullable=True)
    reviews = db.Column(db.Text, nullable=True)
    tags = db.Column(db.String(200), nullable=True)
    bangumi_links = db.Column(db.String(200), nullable=True)
    official_links = db.Column(db.String(200), nullable=True)
    status = db.Column(db.Enum(status), nullable=False, default=status.DEFAULT)

with app.app_context():
    db.create_all()

'''@app.route("/power", methods=["POST"])
def power():
    base = request.json.get("base")
    exponent = request.json.get("exponent")
    print(f"Received base: {base}, exponent: {exponent}")
    if base is None or exponent is None:
        return jsonify({"error": "Missing 'base' or 'exponent' in request body"})
    try:
        result = base ** exponent
        print(f"Calculated result: {result}")
        return jsonify({"result": result})
    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({"error": str(e), "message": "Please try again"})'''



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
        anime_new = Anime(name=name, summary=summary, reviews=reviews, bangumi_links=bangumi_links, official_links=official_links)
        db.session.add(anime_new)
        db.session.commit()
        return redirect(url_for('animes'))
    
    return render_template('animes_new.html')





if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)