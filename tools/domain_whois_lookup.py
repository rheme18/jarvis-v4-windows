from __future__ import annotations

import socket
import ssl
from datetime import datetime


def domain_whois_lookup(domain: str) -> str:
    target = (domain or "").strip().lower().replace("https://", "").replace("http://", "").split("/")[0]
    if not target:
        return "Domain sorgusu icin domain gerekli."

    lines = [f"DOMAIN RAPORU - {target}"]
    try:
        ip_list = sorted({item[4][0] for item in socket.getaddrinfo(target, 443, proto=socket.IPPROTO_TCP)})
        lines.append("IP adresleri: " + (", ".join(ip_list[:8]) if ip_list else "bulunamadi"))
    except Exception as exc:
        lines.append(f"DNS cozumu alinamadi: {exc}")

    try:
        context = ssl.create_default_context()
        with socket.create_connection((target, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=target) as ssock:
                cert = ssock.getpeercert()
        subject = dict(x[0] for x in cert.get("subject", []))
        issuer = dict(x[0] for x in cert.get("issuer", []))
        expires_raw = cert.get("notAfter", "")
        expires = datetime.strptime(expires_raw, "%b %d %H:%M:%S %Y %Z") if expires_raw else None
        lines.append(f"SSL konu: {subject.get('commonName', target)}")
        lines.append(f"SSL veren: {issuer.get('commonName', 'bilinmiyor')}")
        if expires:
            days_left = (expires - datetime.utcnow()).days
            lines.append(f"SSL bitis: {expires.date()} ({days_left} gun)")
    except Exception as exc:
        lines.append(f"SSL bilgisi alinamadi: {exc}")

    return "\n".join(lines)
