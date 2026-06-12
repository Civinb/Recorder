from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from pathlib import Path
from db import db
from anime import anime_bp, ALLOWED_EXTENSIONS
from bangumi_api import bangumi_bp, _migrate_add_bangumi_id
import os
from sqlalchemy import text
from bangumi_index import INDEX_DB_PATH
import uuid

app = Flask(__name__)  
db_url = os.environ.get("DATABASE_URL", "sqlite:///main.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)                                      
app.config['SQLALCHEMY_DATABASE_URI'] = db_url      #配置Flask应用程序使用SQLite数据库，并指定数据库文件为main.db。
db.init_app(app)
bgpic_dir = Path("static/background_pic")
CURRENT_BG_FILE = Path("current_bg.txt")          # 记录当前选中的背景文件名
DEFAULT_BG = "6aca374e0b6f4305a15ed59cecf1ae70.jpg"


def get_current_bg():
    if CURRENT_BG_FILE.exists():
        name = CURRENT_BG_FILE.read_text(encoding="utf-8").strip()
        if name:
            return name
    return DEFAULT_BG


@app.context_processor                             # 自动注入到所有模板，base.html 即可直接用 current_bg
def inject_bg():
    return {"current_bg": get_current_bg()}



def _restore_index_from_db():
    # 只有用 PostgreSQL 时才需要（本地 SQLite 索引文件本就持久存在）
    if not db_url.startswith("postgresql"):
        return
    if INDEX_DB_PATH.exists():
        return
    try:
        with db.engine.connect() as conn:
            row = conn.execute(
                text("SELECT data FROM index_blob WHERE id = 1")
            ).fetchone()
        if row:
            INDEX_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            INDEX_DB_PATH.write_bytes(row[0])
            app.logger.info("已从数据库恢复 bangumi 索引")
    except Exception as e:
        app.logger.warning(f"恢复 bangumi 索引失败（不影响其他功能）: {e}")


with app.app_context():
    db.create_all()
    _migrate_add_bangumi_id()
    _restore_index_from_db()

app.register_blueprint(anime_bp)                                   #引入blueprint
app.register_blueprint(bangumi_bp)

def list_bgpic():
    if not bgpic_dir.exists():
        return []
    bgpic_list = []
    for p in bgpic_dir.iterdir():
        if p.is_file() and p.suffix.lower() in ALLOWED_EXTENSIONS:
            bgpic_list.append(p.name)
    return bgpic_list


@app.route("/home")                                                 #主页面
def home():
    return render_template("home.html")


@app.route("/settings", methods = ["GET", "POST"])                                             #设置页面
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
    return render_template("settings.html", images = images)


@app.route("/settings/bgchange/<bg_name>")
def choose_bg(bg_name):
    if bg_name in list_bgpic():                    # 校验：必须是已存在的图片，防止乱传
        CURRENT_BG_FILE.write_text(bg_name, encoding="utf-8")
    return redirect(url_for("settings"))



    





if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)