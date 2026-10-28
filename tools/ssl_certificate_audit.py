from __future__ import annotations

import socket
import ssl
from datetime import datetime


def ssl_certificate_audit(hostname: str, port: int = 443) -> str:
    host = (hostname or "").strip().lower().replace("https://", "").replace("http://", "").split("/")[0]
    port = int(port or 443)
    if not host:
        return "SSL denetimi icin hostname gerekli."

    try:
        context = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=7) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                cipher = ssock.cipher()
                tls_version = ssock.version()
        subject = dict(x[0] for x in cert.get("subject", []))
        issuer = dict(x[0] for x in cert.get("issuer", []))
        expires = datetime.strptime(cert.get("notAfter"), "%b %d %H:%M:%S %Y %Z")
        starts = datetime.strptime(cert.get("notBefore"), "%b %d %H:%M:%S %Y %Z")
        days_left = (expires - datetime.utcnow()).days
        status = "iyi" if days_left > 30 else "yakinda bitecek" if days_left >= 0 else "suresi dolmus"
        return "\n".join([
            f"SSL SERTIFIKA DENETIMI - {host}:{port}",
            f"Durum: {status}",
            f"Konu: {subject.get('commonName', host)}",
            f"Veren: {issuer.get('commonName', 'bilinmiyor')}",
            f"Baslangic: {starts.date()}",
            f"Bitis: {expires.date()} ({days_left} gun)",
            f"TLS: {tls_version}",
            f"Cipher: {cipher[0] if cipher else 'bilinmiyor'}",
        ])
    except Exception as exc:
        return f"SSL denetimi basarisiz: {exc}"
