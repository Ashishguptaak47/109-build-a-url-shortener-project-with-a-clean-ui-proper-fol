import sqlite3
from contextlib import contextmanager
from app.config import DATABASE_PATH

def init_db():
    with get_db() as conn:
        conn.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                target_url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NULL,
                clicks INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS clicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                link_id INTEGER NOT NULL,
                clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                referrer TEXT DEFAULT 'Direct',
                user_agent TEXT DEFAULT 'Unknown',
                FOREIGN KEY (link_id) REFERENCES links(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_links_code ON links(code);
            CREATE INDEX IF NOT EXISTS idx_clicks_link_id ON clicks(link_id);
        """)

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
