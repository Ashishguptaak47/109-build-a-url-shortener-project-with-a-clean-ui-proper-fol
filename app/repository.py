from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from app.database import get_db

def create_link(target_url: str, code: str, expires_in_hours: Optional[int] = None) -> Dict[str, Any]:
    expires_at = None
    if expires_in_hours and expires_in_hours > 0:
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)).strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO links (code, target_url, expires_at) VALUES (?, ?, ?)",
            (code, target_url, expires_at)
        )
        link_id = cursor.lastrowid
        row = conn.execute("SELECT * FROM links WHERE id = ?", (link_id,)).fetchone()
        return dict(row)

def get_link_by_code(code: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM links WHERE code = ?", (code,)).fetchone()
        if not row:
            return None
        return dict(row)

def is_code_taken(code: str) -> bool:
    with get_db() as conn:
        row = conn.execute("SELECT 1 FROM links WHERE code = ?", (code,)).fetchone()
        return bool(row)

def record_click(link_id: int, referrer: Optional[str], user_agent: Optional[str]):
    with get_db() as conn:
        conn.execute("UPDATE links SET clicks = clicks + 1 WHERE id = ?", (link_id,))
        conn.execute(
            "INSERT INTO clicks (link_id, referrer, user_agent) VALUES (?, ?, ?)",
            (link_id, referrer or "Direct", user_agent or "Unknown")
        )

def get_recent_links(limit: int = 10) -> List[Dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM links ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

def get_link_stats(code: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        link = conn.execute("SELECT * FROM links WHERE code = ?", (code,)).fetchone()
        if not link:
            return None
        
        clicks = conn.execute(
            """
            SELECT clicked_at, referrer, user_agent 
            FROM clicks 
            WHERE link_id = ? 
            ORDER BY clicked_at DESC LIMIT 20
            """,
            (link["id"],)
        ).fetchall()

        referrers = conn.execute(
            """
            SELECT referrer, COUNT(*) as count 
            FROM clicks 
            WHERE link_id = ? 
            GROUP BY referrer 
            ORDER BY count DESC LIMIT 5
            """,
            (link["id"],)
        ).fetchall()

        return {
            "link": dict(link),
            "recent_clicks": [dict(c) for c in clicks],
            "top_referrers": [dict(r) for r in referrers]
        }
