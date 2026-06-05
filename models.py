import enum

from db import db


class status(enum.Enum):                                         #动漫状态枚举类，包含了动漫的各种状态，如正在观看、已完成、计划观看、已放弃和搁置等。
    WACHING = "Watching"
    COMPLETED = "Completed"
    PLANNING = "Planning"
    DROPPED = "Dropped"
    ON_HOLD = "On Hold"
    DEFAULT = "Default"

    
class type(enum.Enum):                                           #动漫类型枚举类，包含了动漫的各种类型，如TV、Movie和OVA等。
    TV = "TV"
    MOVIE = "Movie"
    OVA = "OVA"



class Anime(db.Model):                                           #数据库中的Anime模型，包含了动漫的各种属性，如名称、图片链接、类型、播出日期、简介、评分、评论、标签、相关链接和状态等。
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
    bangumi_id = db.Column(db.Integer, nullable=True, index=True)  # 关联的 bangumi subject id