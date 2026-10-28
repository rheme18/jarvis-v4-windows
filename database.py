import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "jarvis_memory.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Veritabanı tablolarını (Notlar, Kişiler, Günlük) otomatik oluşturur."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Günlük ve Notlar Tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL, -- 'journal', 'note', 'contact', 'project'
                title TEXT,
                content TEXT NOT NULL,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

# Veritabanını başlat
init_db()

def db_save(category: str, content: str, title: str = "", tags: str = "") -> str:
    """Veritabanına kayıt ekler (Günlük, Not, Kişi vb.)"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO records (category, title, content, tags) VALUES (?, ?, ?, ?)",
                (category.lower(), title, content, tags)
            )
            conn.commit()
            return f"[{category.upper()}] Kayıt başarıyla veritabanına eklendi Patron."
    except Exception as e:
        return f"Veritabanı kayıt hatası: {e}"

def db_search(query: str, category: str = None) -> str:
    """Veritabanında kelime veya kategoriye göre arama yapar."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute(
                    "SELECT category, title, content, created_at FROM records WHERE category = ? AND (content LIKE ? OR title LIKE ? OR tags LIKE ?) ORDER BY id DESC LIMIT 10",
                    (category.lower(), f"%{query}%", f"%{query}%", f"%{query}%")
                )
            else:
                cursor.execute(
                    "SELECT category, title, content, created_at FROM records WHERE content LIKE ? OR title LIKE ? OR tags LIKE ? ORDER BY id DESC LIMIT 10",
                    (f"%{query}%", f"%{query}%", f"%{query}%")
                )
            
            rows = cursor.fetchall()
            if not rows:
                return "İlgili kriterlere uygun kayıt bulunamadı."
            
            results = []
            for r in rows:
                results.append(f"[{r['created_at']}] ({r['category'].upper()}) {r['title']}: {r['content']}")
            return "\n".join(results)
    except Exception as e:
        return f"Veritabanı arama hatası: {e}"

def db_delete(record_id: int) -> str:
    """ID bazlı kayıt siler."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM records WHERE id = ?", (record_id,))
            conn.commit()
            return f"ID #{record_id} kayıt silindi."
    except Exception as e:
        return f"Silme hatası: {e}"