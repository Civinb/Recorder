from flask import Blueprint, request, redirect, render_template, url_for
from pathlib import Path
import uuid
from models import Game
from db import db
from datetime import datetime


game_bp = Blueprint('game', __name__, url_prefix="/games")
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}


@game_bp.route("/list")
def games():
    games = Game.query.all()
    return render_template("games_list.html", games=games)