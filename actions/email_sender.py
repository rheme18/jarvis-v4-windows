# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S V4 — Email Suite (Tarayıcısız E-Posta Gönderme ve Okuma)
SMTP ile doğrudan e-posta gönderir.
IMAP ile tarayıcı açmadan son gelen e-postaları okur ve ödev/proje/üniversite içeriklerini filtreler.
"""

import os
import json
import smtplib
import imaplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, Any, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "email_config.json"

DEFAULT_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 465,
    "imap_server": "imap.gmail.com",
    "imap_port": 993,
    "email_address": "",
    "app_password": "",
    "sender_name": "Emir Aras Koç (JARVIS Assistant)"
}


def load_email_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            return {**DEFAULT_CONFIG, **data}
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_email_config(cfg: dict):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def _decode_str(header_val) -> str:
    if not header_val:
        return ""
    decoded_parts = decode_header(header_val)
    res = []
    for part, enc in decoded_parts:
        if isinstance(part, bytes):
            try:
                res.append(part.decode(enc or "utf-8", errors="ignore"))
            except Exception:
                res.append(part.decode("utf-8", errors="ignore"))
        else:
            res.append(str(part))
    return " ".join(res)


def send_email_message(to_address: str, subject: str, body: str) -> Dict[str, Any]:
    """
    Belirtilen adrese doğrudan SMTP ile e-posta gönderir.
    """
    cfg = load_email_config()
    sender_email = cfg.get("email_address", "").strip()
    app_pwd = cfg.get("app_password", "").strip()

    if not sender_email or not app_pwd:
        return {
            "status": "error",
            "message": "E-posta hesabı yapılandırılmamış Patron. Lütfen 'config/email_config.json' dosyasına Gmail adresi ve 16 haneli Uygulama Şifresi (App Password) girin."
        }

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{cfg.get('sender_name', 'Patron')} <{sender_email}>"
    msg["To"] = to_address

    # Düz metin ve HTML gövdesi
    part_text = MIMEText(body, "plain", "utf-8")
    msg.attach(part_text)

    try:
        server = smtplib.SMTP_SSL(cfg.get("smtp_server", "smtp.gmail.com"), int(cfg.get("smtp_port", 465)), timeout=15)
        server.login(sender_email, app_pwd)
        server.sendmail(sender_email, [to_address], msg.as_string())
        server.quit()
        return {
            "status": "success",
            "message": f"E-posta başarıyla '{to_address}' adresine iletildi. Konu: {subject}"
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": f"E-posta gönderilirken hata oluştu: {exc}"
        }


def read_recent_emails(count: int = 5, search_query: Optional[str] = None) -> Dict[str, Any]:
    """
    Tarayıcı açmadan son gelen e-postaları IMAP üzerinden okur.
    search_query verilirse konu ve içerikte anahtar kelime arar (örn: 'ödev', 'proje').
    """
    cfg = load_email_config()
    user_email = cfg.get("email_address", "").strip()
    app_pwd = cfg.get("app_password", "").strip()

    if not user_email or not app_pwd:
        return {
            "status": "error",
            "message": "E-posta hesabı yapılandırılmamış Patron. config/email_config.json dosyasını kontrol edin."
        }

    try:
        mail = imaplib.IMAP4_SSL(cfg.get("imap_server", "imap.gmail.com"), int(cfg.get("imap_port", 993)), timeout=15)
        mail.login(user_email, app_pwd)
        mail.select("INBOX")

        status, messages = mail.search(None, "ALL")
        if status != "OK" or not messages[0]:
            mail.close()
            mail.logout()
            return {"status": "success", "emails": [], "summary": "Gelen kutusunda e-posta bulunamadı."}

        email_ids = messages[0].split()
        recent_ids = email_ids[-max(count * 3, 10):]  # Filtreleme payı için biraz fazla al
        recent_ids.reverse()

        found_emails = []
        for msg_id in recent_ids:
            if len(found_emails) >= count:
                break
            res, data = mail.fetch(msg_id, "(RFC822)")
            if res != "OK":
                continue
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            subject = _decode_str(msg.get("Subject", "Konusuz"))
            sender = _decode_str(msg.get("From", "Bilinmeyen Gönderen"))
            date_str = msg.get("Date", "")

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    ctype = part.get_content_type()
                    if ctype == "text/plain":
                        try:
                            body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                            break
                        except Exception:
                            pass
            else:
                try:
                    body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
                except Exception:
                    pass

            body_preview = " ".join(body.split())[:200]

            if search_query:
                sq = search_query.lower()
                if sq not in subject.lower() and sq not in body.lower() and sq not in sender.lower():
                    continue

            found_emails.append({
                "subject": subject,
                "from": sender,
                "date": date_str,
                "snippet": body_preview
            })

        mail.close()
        mail.logout()

        summary_lines = [f"📧 Toplam {len(found_emails)} adet e-posta incelendi:"]
        for i, em in enumerate(found_emails, 1):
            summary_lines.append(f"{i}. Gönderen: {em['from']} | Konu: {em['subject']}")
            if em["snippet"]:
                summary_lines.append(f"   Özet: {em['snippet'][:110]}...")

        return {
            "status": "success",
            "emails": found_emails,
            "summary": "\n".join(summary_lines)
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": f"E-postalar okunurken hata oluştu: {exc}"
        }
