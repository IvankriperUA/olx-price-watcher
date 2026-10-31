import os
import sqlite3
from datetime import datetime, timezone


DB_NAME = os.getenv("DB_PATH", "price_watcher.db")


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                price INTEGER,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL
            )
        """)


def save_listing(title, price, url):
    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        old = conn.execute(
            "SELECT price FROM listings WHERE url = ?",
            (url,)
        ).fetchone()

        if old is None:
            conn.execute("""
                INSERT INTO listings
                (url, title, price, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?)
            """, (url, title, price, now, now))

            return {
                "status": "new",
                "old_price": None,
                "new_price": price
            }

        old_price = old["price"]

        status = "unchanged"
        if price is not None and old_price is not None:
            if price < old_price:
                status = "price_drop"
            elif price != old_price:
                status = "price_increased"
        elif price is not None and old_price is None:
            status = "price_discovered"

        conn.execute("""
            UPDATE listings
            SET title = ?,
                price = COALESCE(?, price),
                last_seen = ?
            WHERE url = ?
        """, (title, price, now, url))

        return {
            "status": status,
            "old_price": old_price,
            "new_price": price if price is not None else old_price
        }

if __name__ == "__main__":
    init_db()
    print("Database initialized.")