"""一次性脚本：把本地 bangumi_index.db 上传进 PostgreSQL。
用法（PowerShell，把连接串换成你的 Neon 地址）：
    $env:DATABASE_URL="postgresql://...neon.tech/db?sslmode=require"
    python upload_index.py
"""
import os
from sqlalchemy import create_engine, text

db_url = os.environ["DATABASE_URL"]
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

data = open("instance/bangumi_index.db", "rb").read()
engine = create_engine(db_url)
with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS index_blob (
            id INTEGER PRIMARY KEY,
            data BYTEA NOT NULL,
            updated_at TIMESTAMP DEFAULT now()
        )
    """))
    conn.execute(text("DELETE FROM index_blob"))
    conn.execute(text("INSERT INTO index_blob (id, data) VALUES (1, :d)"), {"d": data})
print(f"已上传 {len(data)} 字节到 PostgreSQL")