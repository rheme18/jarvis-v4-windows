from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
SKILLS_DIR = BASE_DIR / "skills"


@dataclass(frozen=True)
class SkillEntry:
    name: str
    description: str
    path: Path
    license: str = ""

    def as_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "description": self.description,
            "path": str(self.path),
            "license": self.license,
        }


def _frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    raw = text[3:end].strip("\r\n")
    body = text[end + 4 :].lstrip("\r\n")
    data: dict[str, str] = {}
    lines = raw.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if ":" not in line:
            i += 1
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value in {"|-", "|", ">-", ">"}:
            block: list[str] = []
            i += 1
            while i < len(lines) and (lines[i].startswith(" ") or not lines[i].strip()):
                block.append(lines[i].strip())
                i += 1
            data[key] = " ".join(part for part in block if part).strip()
            continue
        data[key] = value.strip("\"'")
        i += 1
    return data, body


def _read_skill(path: Path) -> SkillEntry | None:
    skill_md = path / "SKILL.md"
    if not skill_md.exists():
        return None
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None
    meta, body = _frontmatter(text)
    name = (meta.get("name") or path.name).strip()
    description = (meta.get("description") or "").strip()
    if not description:
        first = next((line.strip("# ").strip() for line in body.splitlines() if line.strip()), "")
        description = first[:400]
    return SkillEntry(
        name=name,
        description=re.sub(r"\s+", " ", description).strip(),
        path=skill_md,
        license=(meta.get("license") or "").strip(),
    )


def list_skills(limit: int = 80) -> list[SkillEntry]:
    if not SKILLS_DIR.exists():
        return []
    rows: list[SkillEntry] = []
    for child in sorted(SKILLS_DIR.iterdir(), key=lambda item: item.name.lower()):
        if not child.is_dir():
            continue
        entry = _read_skill(child)
        if entry:
            rows.append(entry)
            if len(rows) >= max(1, int(limit or 80)):
                break
    return rows


def _score(query: str, entry: SkillEntry) -> int:
    query = re.sub(r"\s+", " ", (query or "").casefold()).strip()
    if not query:
        return 1
    haystack = f"{entry.name} {entry.description}".casefold()
    score = 0
    for token in query.split():
        if token == entry.name.casefold():
            score += 80
        elif token in entry.name.casefold():
            score += 40
        elif token in haystack:
            score += 12
    if query in haystack:
        score += 50
    return score


def search_skills(query: str = "", limit: int = 8) -> list[SkillEntry]:
    rows = list_skills()
    ranked = [(entry, _score(query, entry)) for entry in rows]
    ranked = [item for item in ranked if item[1] > 0]
    ranked.sort(key=lambda item: (-item[1], item[0].name))
    return [entry for entry, _ in ranked[: max(1, int(limit or 8))]]


def get_skill(name: str, include_body: bool = False, max_chars: int = 9000) -> dict[str, str]:
    needle = (name or "").casefold().strip()
    entries = list_skills()
    selected = next((entry for entry in entries if entry.name.casefold() == needle), None)
    if selected is None:
        selected = next((entry for entry in entries if needle and needle in entry.name.casefold()), None)
    if selected is None:
        hits = search_skills(name, 1)
        selected = hits[0] if hits else None
    if selected is None:
        return {"error": f"Skill bulunamadi: {name}"}

    data = selected.as_dict()
    if include_body:
        try:
            body = selected.path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            body = f"Skill okunamadi: {exc}"
        data["body"] = body[: max(1000, int(max_chars or 9000))]
    return data


def format_skill_context(query: str = "", limit: int = 8) -> str:
    rows = search_skills(query, limit)
    if not rows:
        return ""
    lines = [
        "[JARVIS SKILL LIBRARY]",
        "Kullanici gorevi uygun oldugunda skill_library araciyla ilgili SKILL.md detayini oku.",
    ]
    for entry in rows:
        desc = entry.description[:420]
        lines.append(f"- {entry.name}: {desc}")
    return "\n".join(lines)
