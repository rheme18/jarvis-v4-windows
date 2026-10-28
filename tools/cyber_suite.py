from __future__ import annotations

import hashlib
import json
import socket
import ssl
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

from core.settings_store import get_setting


BASE_DIR = Path(__file__).resolve().parents[1]
WIFI_HISTORY = BASE_DIR / "memory" / "wifi_history.jsonl"


def _decl(name: str, description: str, props: dict | None = None, required: list[str] | None = None) -> dict:
    return {"name": name, "description": description, "parameters": {"type": "OBJECT", "properties": props or {}, "required": required or []}}


TOOL_DECLARATIONS = [
    _decl("subdomain_finder", "Yaygin subdomain adlarini DNS ile kontrol eder.", {"domain": {"type": "STRING"}, "limit": {"type": "NUMBER"}}, ["domain"]),
    _decl("http_security_headers_audit", "HTTP guvenlik header denetimi yapar.", {"url": {"type": "STRING"}}, ["url"]),
    _decl("ssl_tls_deep_audit", "SSL/TLS sertifika ve protokol detay raporu verir.", {"hostname": {"type": "STRING"}, "port": {"type": "NUMBER"}}, ["hostname"]),
    _decl("dns_propagation_check", "Bir domaini farkli DNS resolverlari uzerinden cozer.", {"domain": {"type": "STRING"}, "record_type": {"type": "STRING"}}, ["domain"]),
    _decl("domain_reputation_check", "Domain icin basit risk ve itibar sinyalleri uretir.", {"domain": {"type": "STRING"}}, ["domain"]),
    _decl("local_network_inventory", "Yerel ag ve ARP tablosundan cihaz envanteri cikarir.", {}),
    _decl("process_reputation_score", "Calisan surecler icin yerel risk/reputation skoru verir.", {"limit": {"type": "NUMBER"}}),
    _decl("hash_reputation_lookup", "Hash degeri icin yerel format/risk kontrolu yapar.", {"hash_value": {"type": "STRING"}}, ["hash_value"]),
    _decl("url_screenshot_analyzer", "URL icin sayfa basligi, durum ve screenshot oncesi metadata raporu verir.", {"url": {"type": "STRING"}}, ["url"]),
    _decl("open_port_risk_report", "Hedefteki yaygin portlar icin acik port risk raporu verir.", {"host": {"type": "STRING"}, "ports": {"type": "STRING"}}),
    _decl("wifi_signal_history", "Wi-Fi sinyal bilgisini kaydeder ve gecmis ozetini verir.", {"action": {"type": "STRING"}, "limit": {"type": "NUMBER"}}),
]

PLUGIN_META = {"category": "cyber", "danger": "safe", "ui_visible": True}


def _normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def _fetch(url: str, timeout: int = 0):
    timeout = int(timeout or get_setting("cyber", "http_timeout", 8) or 8)
    req = urllib.request.Request(_normalize_url(url), headers={"User-Agent": "JarvisAudit/1.0"})
    return urllib.request.urlopen(req, timeout=timeout)


def subdomain_finder(domain: str, limit: int = 40) -> str:
    common = "www api app dev test staging beta admin mail smtp blog docs cdn static assets portal vpn remote git status shop".split()
    found = []
    for sub in common[: int(limit or 40)]:
        host = f"{sub}.{domain}".strip(".")
        try:
            ips = sorted({item[4][0] for item in socket.getaddrinfo(host, None)})
            found.append(f"{host} -> {', '.join(ips[:4])}")
        except Exception:
            pass
    return "\n".join(found) if found else "Subdomain bulunamadi."


def http_security_headers_audit(url: str) -> str:
    required = ["strict-transport-security", "content-security-policy", "x-frame-options", "x-content-type-options", "referrer-policy", "permissions-policy"]
    try:
        with _fetch(url) as resp:
            headers = {k.lower(): v for k, v in resp.headers.items()}
            lines = [f"HTTP {resp.status} - {resp.url}"]
            for h in required:
                lines.append(f"{h}: {'OK' if h in headers else 'MISSING'}")
            server = headers.get("server")
            if server:
                lines.append(f"server header exposed: {server}")
            return "\n".join(lines)
    except Exception as exc:
        return f"Header audit hatasi: {exc}"


def ssl_tls_deep_audit(hostname: str, port: int = 443) -> str:
    try:
        ctx = ssl.create_default_context()
        timeout = int(get_setting("cyber", "ssl_timeout", 8) or 8)
        with socket.create_connection((hostname, int(port or 443)), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                return "\n".join([
                    f"Host: {hostname}:{port}",
                    f"TLS: {ssock.version()}",
                    f"Cipher: {ssock.cipher()}",
                    f"Issuer: {cert.get('issuer')}",
                    f"Subject: {cert.get('subject')}",
                    f"Not before: {cert.get('notBefore')}",
                    f"Not after: {cert.get('notAfter')}",
                    f"SAN: {cert.get('subjectAltName', [])[:8]}",
                ])
    except Exception as exc:
        return f"SSL/TLS audit hatasi: {exc}"


def dns_propagation_check(domain: str, record_type: str = "A") -> str:
    resolvers = ["1.1.1.1", "8.8.8.8", "9.9.9.9"]
    lines = []
    timeout = int(get_setting("cyber", "dns_timeout", 5) or 5)
    for resolver in resolvers:
        try:
            cp = subprocess.run(["nslookup", "-type=" + (record_type or "A"), domain, resolver], capture_output=True, text=True, timeout=timeout)
            tail = "\n".join(cp.stdout.splitlines()[-8:])
            lines.append(f"Resolver {resolver}:\n{tail}")
        except Exception as exc:
            lines.append(f"Resolver {resolver}: {exc}")
    return "\n\n".join(lines)


def domain_reputation_check(domain: str) -> str:
    parsed = domain.lower().strip().replace("http://", "").replace("https://", "").split("/")[0]
    score = 100
    flags = []
    if parsed.count("-") >= 3:
        score -= 20; flags.append("cok fazla tire")
    if any(ch.isdigit() for ch in parsed.split(".")[0]):
        score -= 10; flags.append("rakamli ad")
    if len(parsed) > 45:
        score -= 15; flags.append("uzun domain")
    try:
        socket.gethostbyname(parsed)
        flags.append("DNS cozuluyor")
    except Exception:
        score -= 25; flags.append("DNS cozulmedi")
    return f"Domain reputation score: {max(0, score)}/100\n" + "\n".join(f"- {f}" for f in flags)


def local_network_inventory() -> str:
    try:
        ipconfig = subprocess.run(["ipconfig"], capture_output=True, text=True, timeout=8).stdout
        arp = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=8).stdout
        return "IPCONFIG OZETI\n" + "\n".join(ipconfig.splitlines()[:80]) + "\n\nARP TABLOSU\n" + "\n".join(arp.splitlines()[:80])
    except Exception as exc:
        return f"Network inventory hatasi: {exc}"


def process_reputation_score(limit: int = 30) -> str:
    try:
        import psutil
        rows = []
        suspicious = ("temp", "appdata", "unknown", "miner", "inject", "rat")
        for proc in psutil.process_iter(["pid", "name", "exe"]):
            info = proc.info
            exe = (info.get("exe") or "").lower()
            score = 100
            flags = []
            if any(s in exe for s in suspicious):
                score -= 35; flags.append("suspicious path/name")
            if not exe:
                score -= 15; flags.append("missing exe path")
            if score < 100:
                rows.append(f"{info.get('pid')} {info.get('name')} score={score} {'; '.join(flags)}")
            if len(rows) >= int(limit or 30):
                break
        return "\n".join(rows) if rows else "Belirgin surec riski yok."
    except Exception as exc:
        return f"Process reputation hatasi: {exc}"


def hash_reputation_lookup(hash_value: str) -> str:
    hv = (hash_value or "").strip().lower()
    algo = {32: "MD5", 40: "SHA1", 64: "SHA256"}.get(len(hv), "UNKNOWN")
    valid = all(c in "0123456789abcdef" for c in hv)
    score = 100 if valid and algo != "UNKNOWN" else 40
    return f"Hash format: {algo}\nValid hex: {valid}\nLocal reputation score: {score}/100\nNot: Dis kaynak sorgusu yapilmadi."


def url_screenshot_analyzer(url: str) -> str:
    try:
        with _fetch(url) as resp:
            raw = resp.read(200_000).decode("utf-8", errors="ignore")
            title = ""
            low = raw.lower()
            if "<title" in low:
                start = low.find("<title")
                start = raw.find(">", start) + 1
                end = low.find("</title>", start)
                title = raw[start:end].strip()[:160]
            return f"URL: {resp.url}\nHTTP: {resp.status}\nTitle: {title or '-'}\nHTML bytes sampled: {len(raw)}\nScreenshot: Playwright entegrasyonu icin hazir metadata."
    except Exception as exc:
        return f"URL analyzer hatasi: {exc}"


def open_port_risk_report(host: str = "127.0.0.1", ports: str = "") -> str:
    port_list = [int(p) for p in (ports or "21,22,23,25,53,80,135,139,443,445,3389,5900,8080").split(",") if p.strip().isdigit()]
    risky = {21: "FTP", 23: "Telnet", 445: "SMB", 3389: "RDP", 5900: "VNC"}
    lines = []
    for port in port_list:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                risk = "HIGH" if port in risky else "INFO"
                lines.append(f"{port}/tcp OPEN {risk} {risky.get(port, '')}")
        except Exception:
            pass
    return "\n".join(lines) if lines else "Yaygin portlarda acik servis bulunamadi."


def wifi_signal_history(action: str = "record", limit: int = 20) -> str:
    if not get_setting("cyber", "wifi_history_enabled", True):
        return "Wi-Fi sinyal gecmisi settings uzerinden kapali."
    action = (action or "record").lower()
    if action in {"record", "snapshot"}:
        try:
            out = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True, timeout=8).stdout
        except Exception as exc:
            return f"Wi-Fi okunamadi: {exc}"
        row = {"ts": int(time.time()), "raw": "\n".join(out.splitlines()[:60])}
        WIFI_HISTORY.parent.mkdir(parents=True, exist_ok=True)
        with WIFI_HISTORY.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        return "Wi-Fi snapshot kaydedildi.\n" + row["raw"]
    if not WIFI_HISTORY.exists():
        return "Wi-Fi gecmisi yok."
    rows = WIFI_HISTORY.read_text(encoding="utf-8").splitlines()[-int(limit or 20):]
    return "\n\n".join(rows)
