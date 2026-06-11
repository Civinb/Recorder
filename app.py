from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from pathlib import Path
from db import db
from anime import anime_bp
from bangumi_api import bangumi_bp, _migrate_add_bangumi_id
import os


app = Flask(__name__)  
db_url = os.environ.get("DATABASE_URL", "sqlite:///main.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)                                      
app.config['SQLALCHEMY_DATABASE_URI'] = db_url      #配置Flask应用程序使用SQLite数据库，并指定数据库文件为main.db。
db.init_app(app)


with app.app_context():
    db.create_all()
    _migrate_add_bangumi_id()


app.register_blueprint(anime_bp)                                   #引入blueprint
app.register_blueprint(bangumi_bp)


@app.route("/home")                                                 #主页面
def home():
    return render_template("home.html")


@app.route("/settings")                                             #设置页面
def settings():
    return render_template("settings.html")





if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)