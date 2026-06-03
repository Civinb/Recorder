"""
Bangumi 数据索引模块
- 从 static/bangumi_data/*.zip 中提取 type=2 (动画) 条目
- 写入独立 SQLite (bangumi_index.db)，含 FTS5 全文搜索表
- 提供 search / get 接口供 Flask 路由调用
"""

import json
import re
import sqlite3
import zipfile
from pathlib import Path

BANGUMI_DATA_DIR = Path(__file__).parent / "static" / "bangumi_data"
INDEX_DB_PATH = Path(__file__).parent / "instance" / "bangumi_index.db"

# Bangumi subject type: 1=书 2=动画 3=音乐 4=游戏 6=三次元
SUBJECT_TYPE_ANIME = 2

# Bangumi platform (type=2 动画) → 我们的 type 枚举
# 1=TV 2=OVA 3=Movie 5=WEB 其它视为 TV
PLATFORM_TO_TYPE = {
    1: "TV",
    2: "OVA",
    3: "MOVIE",
    5: "TV",
}


def _latest_zip() -> Path | None:
    """返回 bangumi_data/ 中最新的 dump zip 文件"""
    if not BANGUMI_DATA_DIR.exists():
        return None
    zips = sorted(BANGUMI_DATA_DIR.glob("*.zip"))
    return zips[-1] if zips else None


def _ensure_dirs() -> None:
    INDEX_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _parse_infobox(infobox: str) -> dict:
    """从 bangumi 的 wiki infobox 文本中抽取常用字段"""
    if not infobox:
        return {}
    result = {}
    for line in infobox.splitlines():
        m = re.match(r"\s*\|([^=]+?)=\s*(.*)", line)
        if m:
            key = m.group(1).strip()
            value = m.group(2).strip()
            if value and value != "{" and value != "}":
                result[key] = value
    return result


def build_index(progress_cb=None) -> dict:
    """
    构建/覆盖 bangumi 索引数据库
    progress_cb(stage, current, total) 可选回调
    返回统计信息 dict
    """
    _ensure_dirs()
    zip_path = _latest_zip()
    if not zip_path:
        raise FileNotFoundError(
            f"未在 {BANGUMI_DATA_DIR} 找到 bangumi zip 数据"
        )

    # 删除旧索引重建
    if INDEX_DB_PATH.exists():
        INDEX_DB_PATH.unlink()

    conn = sqlite3.connect(INDEX_DB_PATH)
    conn.executescript(
        """
        CREATE TABLE subject (
            id          INTEGER PRIMARY KEY,
            name        TEXT,
            name_cn     TEXT,
            platform    INTEGER,
            summary     TEXT,
            date        TEXT,
            score       REAL,
            rank        INTEGER,
            tags        TEXT,        -- JSON array
            infobox     TEXT,
            nsfw        INTEGER
        );
        CREATE VIRTUAL TABLE subject_fts USING fts5(
            name, name_cn, aliases,
            content='', tokenize='unicode61'
        );
        """
    )

    count = 0
    with zipfile.ZipFile(zip_path) as zf:
        # 找到 subject.jsonlines
        names = [n for n in zf.namelist() if n.endswith("subject.jsonlines")]
        if not names:
            raise FileNotFoundError("zip 中未找到 subject.jsonlines")
        info = zf.getinfo(names[0])
        total_bytes = info.file_size

        with zf.open(info) as f:
            cur = conn.cursor()
            batch = []
            fts_batch = []
            bytes_read = 0
            for line in f:
                bytes_read += len(line)
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("type") != SUBJECT_TYPE_ANIME:
                    continue
                ib = _parse_infobox(obj.get("infobox") or "")
                aliases = ib.get("别名", "") or ""
                tags_json = json.dumps(
                    [t.get("name") for t in (obj.get("tags") or []) if t.get("name")],
                    ensure_ascii=False,
                )
                batch.append(
                    (
                        obj.get("id"),
                        obj.get("name") or "",
                        obj.get("name_cn") or "",
                        obj.get("platform"),
                        obj.get("summary") or "",
                        obj.get("date") or "",
                        obj.get("score"),
                        obj.get("rank"),
                        tags_json,
                        obj.get("infobox") or "",
                        1 if obj.get("nsfw") else 0,
                    )
                )
                fts_batch.append(
                    (
                        obj.get("id"),
                        obj.get("name") or "",
                        obj.get("name_cn") or "",
                        aliases,
                    )
                )
                count += 1
                if len(batch) >= 2000:
                    cur.executemany(
                        "INSERT INTO subject VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        batch,
                    )
                    cur.executemany(
                        "INSERT INTO subject_fts(rowid,name,name_cn,aliases) VALUES (?,?,?,?)",
                        fts_batch,
                    )
                    batch.clear()
                    fts_batch.clear()
                    if progress_cb:
                        progress_cb("indexing", bytes_read, total_bytes)

            if batch:
                cur.executemany(
                    "INSERT INTO subject VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    batch,
                )
                cur.executemany(
                    "INSERT INTO subject_fts(rowid,name,name_cn,aliases) VALUES (?,?,?,?)",
                    fts_batch,
                )

            conn.commit()

    conn.close()
    return {
        "count": count,
        "source": zip_path.name,
        "db_path": str(INDEX_DB_PATH),
    }


def _connect():
    if not INDEX_DB_PATH.exists():
        raise FileNotFoundError("Bangumi 索引尚未建立，请先在设置页点击 Extract")
    conn = sqlite3.connect(INDEX_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _fts_query(q: str) -> str:
    """把用户输入转成 FTS5 安全查询（每个 token 加 *）"""
    tokens = re.findall(r"\w+", q, flags=re.UNICODE)
    if not tokens:
        return ""
    return " ".join(f'"{t}"*' for t in tokens)


def search(q: str, limit: int = 20) -> list[dict]:
    q = (q or "").strip()
    if not q:
        return []
    conn = _connect()
    try:
        fts_q = _fts_query(q)
        if not fts_q:
            return []
        rows = conn.execute(
            """
            SELECT s.id, s.name, s.name_cn, s.date, s.score, s.platform
            FROM subject_fts f
            JOIN subject s ON s.id = f.rowid
            WHERE subject_fts MATCH ?
            ORDER BY (s.score IS NULL), s.score DESC
            LIMIT ?
            """,
            (fts_q, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_subject(subject_id: int) -> dict | None:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM subject WHERE id = ?", (subject_id,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["tags"] = json.loads(d.get("tags") or "[]")
        d["infobox_parsed"] = _parse_infobox(d.get("infobox") or "")
        d["mapped_type"] = PLATFORM_TO_TYPE.get(d.get("platform"), "TV")
        return d
    finally:
        conn.close()


def index_info() -> dict:
    """返回当前索引状态"""
    if not INDEX_DB_PATH.exists():
        return {"exists": False}
    conn = sqlite3.connect(INDEX_DB_PATH)
    try:
        n = conn.execute("SELECT COUNT(*) FROM subject").fetchone()[0]
    finally:
        conn.close()
    zip_path = _latest_zip()
    return {
        "exists": True,
        "count": n,
        "source": zip_path.name if zip_path else None,
    }
