from __future__ import annotations

import socket
import subprocess


def _nslookup(domain: str, record_type: str) -> list[str]:
    try:
        result = subprocess.run(
            ["nslookup", "-type=" + record_type, domain],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=8,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if result.returncode != 0:
            return []
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except Exception:
        return []


def dns_health_check(domain: str) -> str:
    target = (domain or "").strip().lower().replace("https://", "").replace("http://", "").split("/")[0]
    if not target:
        return "DNS kontrolu icin domain gerekli."

    lines = [f"DNS SAGLIK RAPORU - {target}"]
    try:
        addresses = sorted({item[4][0] for item in socket.getaddrinfo(target, None)})
        lines.append("A/AAAA cozumu: " + (", ".join(addresses[:10]) if addresses else "bulunamadi"))
    except Exception as exc:
        lines.append(f"A/AAAA cozumu hatasi: {exc}")

    for record_type in ("MX", "NS", "TXT"):
        rows = _nslookup(target, record_type)
        if rows:
            compact = [row for row in rows if target in row or "mail exchanger" in row.lower() or "nameserver" in row.lower()][:6]
            lines.append(f"{record_type} kayitlari:")
            lines.extend(f"- {row}" for row in (compact or rows[:6]))
        else:
            lines.append(f"{record_type} kaydi okunamadi veya yok.")

    return "\n".join(lines)
