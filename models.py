'''Holds the database tables and related definitions'''


import enum

from db import db


class animeStatus(enum.Enum):                                         #Enum of anime statuses: watching, completed, planning, dropped, on hold, etc.
    WATCHING = "Watching"
    COMPLETED = "Completed"
    PLANNING = "Planning"
    DROPPED = "Dropped"
    ON_HOLD = "On Hold"
    DEFAULT = "Default"

    
class animeType(enum.Enum):                                           #Enum of anime types: TV, Movie, OVA, etc.
    TV = "TV"
    MOVIE = "Movie"
    OVA = "OVA"


class Anime(db.Model):                                           #The Anime model in the database, holding attributes such as name, image URL, type, broadcast date, summary, score, reviews, tags, related links and status.
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    image_url = db.Column(db.String(200), nullable=True)
    type = db.Column(db.Enum(animeType), nullable=False, default=animeType.TV)
    release_date = db.Column(db.Date, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    score = db.Column(db.Float, nullable=True)
    reviews = db.Column(db.Text, nullable=True)
    tags = db.Column(db.String(200), nullable=True)
    bangumi_links = db.Column(db.String(200), nullable=True)
    official_links = db.Column(db.String(200), nullable=True)
    status = db.Column(db.Enum(animeStatus), nullable=False, default=animeStatus.DEFAULT)
    bangumi_id = db.Column(db.Integer, nullable=True, index=True)                 # The associated bangumi subject id




class gameStatus(enum.Enum):                                         #Enum of game statuses: playing, completed, planning, dropped, on hold, etc.
    PLAYING = "Playing"
    COMPLETED = "Completed"
    PLANNING = "Planning"
    DROPPED = "Dropped"
    ON_HOLD = "On Hold"


class gameType(enum.Enum):                                           #Enum of game types
    PC = "PC"
    ONLINE = "Online"
    MOBILE = "Mobile"
    CONSOLE = "Console"


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    image_url = db.Column(db.String(200), nullable=True)
    type = db.Column(db.Enum(gameType), nullable=False)
    release_date = db.Column(db.Date, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    score = db.Column(db.Float, nullable=True)
    reviews = db.Column(db.Text, nullable=True)
    tags = db.Column(db.String(200), nullable=True)
    igdb_links = db.Column(db.String(200), nullable=True)
    official_links = db.Column(db.String(200), nullable=True)
    status = db.Column(db.Enum(gameStatus), nullable=False)