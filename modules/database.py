import sqlite3
import os
import json

DB_DIR = "database"
DB_PATH = os.path.join(DB_DIR, "history.db")


def init_db():
    """Initializes the SQLite database and creates the history table if it doesn't exist."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            query TEXT NOT NULL,
            content_type TEXT NOT NULL,
            tone TEXT NOT NULL,
            length INTEGER NOT NULL,
            response TEXT NOT NULL,
            sources TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_generation(query, content_type, tone, length, response, sources):
    """Saves a new content generation record to the database."""
    init_db()  # Ensure DB and table exist
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Serialize sources list to JSON string
    sources_json = json.dumps(sources)
    
    cursor.execute("""
        INSERT INTO history (query, content_type, tone, length, response, sources)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (query, content_type, tone, length, response, sources_json))
    
    conn.commit()
    conn.close()


def get_history():
    """Retrieves all generation history items from the database sorted by timestamp descending."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    # Configure row_factory to return dicts instead of tuples
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM history ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    
    history_list = []
    for row in rows:
        item = dict(row)
        # Deserialize sources JSON string back to list
        try:
            item["sources"] = json.loads(item["sources"])
        except Exception:
            item["sources"] = []
        history_list.append(item)
        
    conn.close()
    return history_list


def delete_history_item(item_id):
    """Deletes a specific history record by its ID."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM history WHERE id = ?", (item_id,))
    
    conn.commit()
    conn.close()


def clear_history():
    """Clears all records in the history table."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM history")
    
    conn.commit()
    conn.close()
