from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "database"
JSON_FILE = DB_DIR / "people.json"
PNGS_DIR = DB_DIR / "pngs"


def _ensure_paths() -> None:
    """Veritabanı klasörü ve JSON dosyasının varlığından emin olur."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    PNGS_DIR.mkdir(parents=True, exist_ok=True)

    if not JSON_FILE.exists():
        JSON_FILE.write_text("[]", encoding="utf-8")


def load_people() -> List[Dict[str, Any]]:
    """JSON dosyasındaki tüm kişileri okur."""
    _ensure_paths()
    try:
        data = json.loads(JSON_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Kişi veritabanı bozuk JSON içeriyor: {JSON_FILE}") from exc
    if not isinstance(data, list) or any(not isinstance(person, dict) for person in data):
        raise ValueError(f"Kişi veritabanı bir kişi nesnesi listesi olmalı: {JSON_FILE}")
    return data


def save_people(people: List[Dict[str, Any]]) -> None:
    """Kişi listesini JSON dosyasına yazar."""
    _ensure_paths()
    if not isinstance(people, list) or any(not isinstance(person, dict) for person in people):
        raise ValueError("Kişi kayıtları sözlüklerden oluşan bir liste olmalı.")
    temporary = JSON_FILE.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(people, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(JSON_FILE)


def find_photo_path(person_name: str, photo_name: str = "") -> str:
    """Kişi adına göre database/pngs/ içindeki fotoğrafı bulur."""
    _ensure_paths()

    # 1. Özel fotoğraf ismi belirtildiyse
    if photo_name:
        custom_path = PNGS_DIR / photo_name
        if custom_path.exists():
            return str(custom_path)

    # 2. İsimden otomatik eşleştirme (örn: "Emir Aras Koç" -> "emir_aras_koc.png" veya "Emir Aras Koç.png")
    clean_name = person_name.strip().lower()
    slug_name = clean_name.replace(" ", "_")

    possible_names = [
        f"{slug_name}.png",
        f"{slug_name}.jpg",
        f"{person_name}.png",
        f"{person_name}.jpg",
    ]

    for filename in possible_names:
        p = PNGS_DIR / filename
        if p.exists():
            return str(p)

    # Klasör içindeki benzer isimleri de tara
    for file in PNGS_DIR.glob("*"):
        if file.stem.lower() in [clean_name, slug_name]:
            return str(file)

    return ""


def add_person(
    name: str,
    role: str = "Kayıtlı Kişi",
    phone: str = "",
    email: str = "",
    tags: str = "Genel",
    notes: str = "",
    photo_name: str = "",
) -> Dict[str, Any]:
    """Sisteme yeni kişi ekler veya mevcut kişiyi günceller."""
    people = load_people()

    # Mevcut kişi var mı kontrol et
    existing = next((p for p in people if str(p.get("name", "")).casefold() == name.casefold()), None)

    if existing:
        if role: existing["role"] = role
        if phone: existing["phone"] = phone
        if email: existing["email"] = email
        if tags: existing["tags"] = tags
        if notes: existing["notes"] = notes
        if photo_name: existing["photo"] = photo_name
        save_people(people)
        return existing

    valid_ids = []
    for person in people:
        try:
            valid_ids.append(int(person.get("id", 0) or 0))
        except (TypeError, ValueError):
            continue
    new_id = max(valid_ids, default=0) + 1
    new_person = {
        "id": new_id,
        "name": name,
        "role": role or "Kayıtlı Kişi",
        "phone": phone,
        "email": email,
        "tags": tags or "Genel",
        "notes": notes,
        "photo": photo_name,
    }

    people.append(new_person)
    save_people(people)
    return new_person


def get_person(query: str) -> Optional[Dict[str, Any]]:
    """İsme veya etikete göre kişi arar."""
    people = load_people()
    query_clean = query.strip().lower()

    # Tam isim eşleşmesi veya arama
    for person in people:
        if (query_clean in str(person.get("name", "")).casefold()
                or query_clean in str(person.get("tags", "")).casefold()):
            p_copy = dict(person)
            p_copy["photo_path"] = find_photo_path(str(person.get("name", "")), str(person.get("photo", "")))
            return p_copy

    return None
