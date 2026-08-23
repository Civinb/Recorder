"""
Bangumi data index module
- Extracts type=2 (anime) subjects from static/bangumi_data/*.zip
- Writes them into a standalone SQLite file (bangumi_index.db) with an FTS5 full-text search table
- Exposes search / get helpers for the Flask routes to call
"""

import json
import re
import sqlite3
import zipfile
from pathlib import Path

BANGUMI_DATA_DIR = Path(__file__).parent / "static" / "bangumi_data"                        #Location of the .zip files
INDEX_DB_PATH = Path(__file__).parent / "instance" / "bangumi_index.db"                     #Location of the local bangumi database

# Bangumi subject type: 1=book 2=anime 3=music 4=game 6=real life
SUBJECT_TYPE_ANIME = 2

# Bangumi platform (type=2 anime) -> our own type enum
# 1=TV 2=OVA 3=Movie 5=WEB, anything else is treated as TV
PLATFORM_TO_TYPE = {
    1: "TV",
    2: "OVA",
    3: "MOVIE",
    5: "TV",
}


def _latest_zip() -> Path | None:
    """Return the newest dump zip file in bangumi_data/"""
    if not BANGUMI_DATA_DIR.exists():
        return None
    zips = sorted(BANGUMI_DATA_DIR.glob("*.zip"))
    return zips[-1] if zips else None


def _ensure_dirs() -> None:                                             #Create the database folder
    INDEX_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _parse_infobox(infobox: str) -> dict:
    """Extract the commonly used fields from bangumi's wiki infobox text"""
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
    Build/overwrite the bangumi index database
    progress_cb(stage, current, total) is an optional callback
    Returns a dict of statistics
    """
    _ensure_dirs()
    zip_path = _latest_zip()
    if not zip_path:
        raise FileNotFoundError(
            f"No bangumi zip data found in {BANGUMI_DATA_DIR}"
        )

    # Delete the old index and rebuild it
    if INDEX_DB_PATH.exists():
        INDEX_DB_PATH.unlink()

    conn = sqlite3.connect(INDEX_DB_PATH)
    conn.executescript(                                     #Create the schema
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
        # Locate subject.jsonlines
        names = [n for n in zf.namelist() if n.endswith("subject.jsonlines")]
        if not names:
            raise FileNotFoundError("subject.jsonlines not found in the zip")
        info = zf.getinfo(names[0])
        total_bytes = info.file_size

        with zf.open(info) as f:
            cur = conn.cursor()
            batch = []          #Buffer for the main table
            fts_batch = []      #Buffer for the fts search table
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
                aliases = ib.get("别名", "") or ""            # "别名" is the literal infobox key used by Bangumi's data (aliases)
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
                
                #Write into the .db
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

#Try to connect to the database
def _connect():
    if not INDEX_DB_PATH.exists():
        raise FileNotFoundError("The Bangumi index has not been built yet, please click Extract on the settings page first")
    conn = sqlite3.connect(INDEX_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _fts_query(q: str) -> str:
    """Turn the user input into a safe FTS5 query (append * to every token)"""
    tokens = re.findall(r"\w+", q, flags=re.UNICODE)
    if not tokens:
        return ""
    return " ".join(f'"{t}"*' for t in tokens)


def search(q: str, limit: int = 20) -> list[dict]:                          #Search for matching entries
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


def get_subject(subject_id: int) -> dict | None:                            #Take a subject id, return the data for that id
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
    """Return the current index status"""
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
