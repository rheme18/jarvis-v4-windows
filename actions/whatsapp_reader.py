# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S V4 — WhatsApp Message & Notification Intelligence
Windows Notification veritabanından (%LOCALAPPDATA%/Microsoft/Windows/Notifications/wpndatabase.db)
WhatsApp ve mesajlaşma bildirimlerini arka planda, tarayıcı veya pencere açmadan okur.
Grup sohbetlerinde veya doğrudan mesajlarda 'ödev', 'proje', 'sınav', 'link' gibi içerikleri bulup özetler.
"""

import os
import re
import shutil
import sqlite3
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List, Optional


def read_whatsapp_messages(count: int = 15, filter_keyword: Optional[str] = None) -> Dict[str, Any]:
    """
    Windows Bildirim Merkezi'nden WhatsApp mesajlarını yakalar ve analiz eder.
    """
    src_db = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Notifications\wpndatabase.db")
    if not os.path.exists(src_db):
        return {
            "status": "error",
            "message": "Windows Bildirim veritabanı bulunamadı."
        }

    tmp_dir = tempfile.gettempdir()
    tmp_db = os.path.join(tmp_dir, "jarvis_wpn.db")

    try:
        shutil.copy2(src_db, tmp_db)
        if os.path.exists(src_db + "-wal"):
            shutil.copy2(src_db + "-wal", tmp_db + "-wal")
        if os.path.exists(src_db + "-shm"):
            shutil.copy2(src_db + "-shm", tmp_db + "-shm")

        conn = sqlite3.connect(tmp_db)
        cur = conn.cursor()

        # WhatsApp bildirimlerini sorgula
        query = """
            SELECT h.PrimaryId, n.Payload, n.ArrivalTime
            FROM Notification n
            JOIN NotificationHandler h ON n.HandlerId = h.RecordId
            WHERE LOWER(h.PrimaryId) LIKE '%whatsapp%'
               OR LOWER(n.Payload) LIKE '%whatsapp%'
               OR LOWER(h.PrimaryId) LIKE '%chrome%'
               OR LOWER(h.PrimaryId) LIKE '%edge%'
            ORDER BY n.ArrivalTime DESC
            LIMIT 60;
        """
        cur.execute(query)
        rows = cur.fetchall()
        conn.close()

    except Exception as exc:
        return {
            "status": "error",
            "message": f"Bildirim veritabanı okunamadı: {exc}"
        }

    messages = []
    seen = set()

    for h_id, payload, arrival_time in rows:
        payload_str = ""
        if isinstance(payload, bytes):
            try:
                payload_str = payload.decode("utf-8", errors="ignore")
            except Exception:
                payload_str = str(payload)
        else:
            payload_str = str(payload)

        # XML Toast ayrıştırma
        sender = ""
        body = ""
        try:
            root = ET.fromstring(payload_str)
            texts = [elem.text for elem in root.iter("text") if elem.text]
            if len(texts) >= 2:
                sender = texts[0].strip()
                body = " ".join(texts[1:]).strip()
            elif len(texts) == 1:
                body = texts[0].strip()
        except Exception:
            # Düz metin regex
            matches = re.findall(r"<text[^>]*>(.*?)</text>", payload_str, re.DOTALL)
            if len(matches) >= 2:
                sender = matches[0].strip()
                body = " ".join(matches[1:]).strip()
            elif len(matches) == 1:
                body = matches[0].strip()

        if not body or len(body) < 3:
            continue

        # Yinelenenleri temizle
        msg_key = f"{sender}:{body}"
        if msg_key in seen:
            continue
        seen.add(msg_key)

        # Anahtar kelime filtresi (ödev, proje vb.)
        if filter_keyword:
            kw = filter_keyword.lower()
            if kw not in sender.lower() and kw not in body.lower():
                continue

        messages.append({
            "sender": sender or "WhatsApp",
            "message": body,
            "handler": h_id
        })

        if len(messages) >= count:
            break

    if not messages:
        kw_note = f" '{filter_keyword}' içeren" if filter_keyword else ""
        return {
            "status": "success",
            "messages": [],
            "summary": f"Son WhatsApp bildirimlerinde{kw_note} yeni bir mesaj veya duyuru bulunamadı Patron."
        }

    # AI Özet Formatı
    summary_lines = [f"📱 WhatsApp Gelen Mesaj Özeti (Toplam {len(messages)} mesaj):"]
    for i, m in enumerate(messages, 1):
        summary_lines.append(f"{i}. [{m['sender']}]: {m['message']}")

    return {
        "status": "success",
        "messages": messages,
        "summary": "\n".join(summary_lines)
    }
