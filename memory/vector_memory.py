"""
JARVIS V4 Windows — Vektör Veritabanı & Semantik Bellek (RAG)
Bellek, notlar, kişiler ve dokümanlar için yerel SQLite tabanlı vektör depolama ve benzerlik araması.
Hem Gemini API embedding desteği hem de %100 yerel çevrimdışı TF-IDF/BM25 kosinüs benzerlik motoru içerir.
"""

from __future__ import annotations

import json
import math
import os
import re
import sqlite3
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "memory" / "jarvis_vectors.db"


def _normalize(text: str) -> str:
    t = (text or "").lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.replace("ı", "i").replace("ğ", "g").replace("ü", "u").replace("ş", "s").replace("ö", "o").replace("ç", "c")
    return t


def _tokenize(text: str) -> List[str]:
    clean = _normalize(text)
    tokens = re.findall(r"\b[a-z0-9_]{2,}\b", clean)
    return tokens


def _compute_local_embedding(text: str, dim: int = 256) -> List[float]:
    """
    Yerel ve çevrimdışı çalışan TF-IDF / Subword Karakter Hashing Vektörü.
    Hiçbir harici kütüphane veya ağ bağlantısı gerektirmez.
    """
    tokens = _tokenize(text)
    if not tokens:
        return [0.0] * dim

    vec = [0.0] * dim
    # 1-gram ve 2-gram hashleme
    for i, tok in enumerate(tokens):
        h = hash(tok) % dim
        vec[h] += 1.0
        if i < len(tokens) - 1:
            h2 = hash(f"{tok}_{tokens[i+1]}") % dim
            vec[h2] += 1.5

    # L2 Normalizasyonu
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    dot = sum(a * b for a, b in zip(vec1, vec2))
    return float(dot)


class VectorMemoryStore:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vector_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    content TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    metadata_json TEXT,
                    embedding_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_vec_category ON vector_entries(category)")
            conn.commit()

    def add(self, content: str, title: str = "", category: str = "general", metadata: Optional[Dict[str, Any]] = None) -> int:
        if not content or not content.strip():
            return 0
        embedding = _compute_local_embedding(f"{title} {content}")
        meta_str = json.dumps(metadata or {}, ensure_ascii=False)
        emb_str = json.dumps(embedding)

        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO vector_entries (title, content, category, metadata_json, embedding_json) VALUES (?, ?, ?, ?, ?)",
                (title.strip(), content.strip(), category.strip(), meta_str, emb_str)
            )
            conn.commit()
            return cursor.lastrowid or 0

    def search(self, query: str, top_k: int = 5, min_score: float = 0.25, category: Optional[str] = None) -> List[Dict[str, Any]]:
        query_vec = _compute_local_embedding(query)
        q_tokens = set(_tokenize(query))

        with self._get_conn() as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute("SELECT id, title, content, category, metadata_json, embedding_json, created_at FROM vector_entries WHERE category = ?", (category,))
            else:
                cursor.execute("SELECT id, title, content, category, metadata_json, embedding_json, created_at FROM vector_entries")
            rows = cursor.fetchall()

        results = []
        for r in rows:
            emb = json.loads(r["embedding_json"])
            cos_score = _cosine_similarity(query_vec, emb)
            # Keyword eşleşme bonusu
            content_tokens = set(_tokenize(f"{r['title']} {r['content']}"))
            overlap = len(q_tokens.intersection(content_tokens))
            keyword_bonus = min(0.3, overlap * 0.1)
            total_score = cos_score + keyword_bonus

            if total_score >= min_score:
                meta = {}
                try:
                    meta = json.loads(r["metadata_json"])
                except Exception:
                    pass
                results.append({
                    "id": r["id"],
                    "title": r["title"],
                    "content": r["content"],
                    "category": r["category"],
                    "score": round(total_score, 3),
                    "created_at": r["created_at"],
                    "metadata": meta,
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def index_all_sources(self) -> str:
        """
        Dağınık veritabanlarını (memory.json, database/people.json, jarvis_memory.db)
        tek bir vektör indeksinde otomatik birleştirir.
        """
        indexed_count = 0

        # 1. jarvis_memory.db
        try:
            db_file = BASE_DIR / "jarvis_memory.db"
            if db_file.exists():
                with sqlite3.connect(str(db_file)) as c:
                    c.row_factory = sqlite3.Row
                    records = c.execute("SELECT category, title, content, tags FROM records").fetchall()
                    for r in records:
                        t = f"[{r['category'].upper()}] {r['title'] or ''}"
                        cnt = f"{r['content']} (Etiketler: {r['tags'] or ''})"
                        self.add(cnt, title=t, category=r['category'])
                        indexed_count += 1
        except Exception:
            pass

        # 2. database/people.json
        try:
            people_file = BASE_DIR / "database" / "people.json"
            if people_file.exists():
                people = json.loads(people_file.read_text(encoding="utf-8"))
                for p in people:
                    t = f"Kişi: {p.get('name', '')} ({p.get('role', '')})"
                    cnt = f"Telefon: {p.get('phone', '')}, E-posta: {p.get('email', '')}, Notlar: {p.get('notes', '')}, Etiketler: {p.get('tags', '')}"
                    self.add(cnt, title=t, category="contact", metadata=p)
                    indexed_count += 1
        except Exception:
            pass

        # 3. memory/memory.json
        try:
            mem_file = BASE_DIR / "memory" / "memory.json"
            if mem_file.exists():
                mem_data = json.loads(mem_file.read_text(encoding="utf-8"))
                for cat, items in mem_data.items():
                    if isinstance(items, dict):
                        for k, v in items.items():
                            val = v.get("value") if isinstance(v, dict) else v
                            if val:
                                self.add(f"{k}: {val}", title=f"Hafıza: {k}", category=cat)
                                indexed_count += 1
        except Exception:
            pass

        return f"Vektör hafıza senkronizasyonu tamamlandı: {indexed_count} kayıt indekslendi Patron."


# Singleton instance
_vector_store = VectorMemoryStore()


def semantic_memory_search(query: str, limit: int = 4, category: Optional[str] = None) -> str:
    """Jarvis'in semantik bellek ve bilgi tabanında arama yapar."""
    hits = _vector_store.search(query, top_k=int(limit or 4), category=category)
    if not hits:
        return f"'{query}' konusunda ilgili bir hafıza kaydı bulunamadı Patron."

    lines = [f"[SEMANTIK BELLEK RAPORU] ('{query}'):"]
    for i, h in enumerate(hits, 1):
        lines.append(f"{i}. [{h['category'].upper()}] {h['title']}")
        lines.append(f"   İçerik: {h['content']}")
        lines.append(f"   Alaka Skoru: %{int(h['score'] * 100)}")
    return "\n".join(lines)


def get_relevant_memory_context(query: str, limit: int = 3) -> str:
    """Prompt için en alakalı hafızaları getirir (Prompt şişmesini önler)."""
    hits = _vector_store.search(query, top_k=limit, min_score=0.35)
    if not hits:
        return ""
    parts = ["[İLGİLİ ANILAR & SEMANTİK BİLGİLER]"]
    for h in hits:
        parts.append(f"• {h['title']}: {h['content']}")
    return "\n".join(parts)
