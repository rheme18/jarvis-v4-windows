#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os
import re
import threading
import time
from pathlib import Path

import requests
import uvicorn
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel


app = FastAPI(title="JARVIS Command Center", version="2.7.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RemoteCommand(BaseModel):
    command: str
    chat_id: int | None = None


class PanelNote(BaseModel):
    message: str


class PluginUpdate(BaseModel):
    action: str
    danger: str | None = None


class SettingUpdate(BaseModel):
    section: str
    key: str
    value: object


class FileRequest(BaseModel):
    path: str = ""


jarvis_core_instance = None
last_telegram_chat_id = None
server_started_at = time.time()
web_loop: asyncio.AbstractEventLoop | None = None
web_server_started = False
message_history: list[str] = []
MAX_HISTORY = 100
BASE_DIR = Path(__file__).resolve().parents[1]
MEMORY_DIR = BASE_DIR / "memory"
UPLOAD_DIR = MEMORY_DIR / "uploads"
MAX_UPLOAD_BYTES = 20 * 1024 * 1024


def _safe_path(raw_path: str = "", base: Path = BASE_DIR) -> Path:
    candidate = Path(raw_path or ".")
    if not candidate.is_absolute():
        candidate = base / candidate
    resolved = candidate.resolve()
    root = base.resolve()
    if resolved != root and root not in resolved.parents:
        raise HTTPException(status_code=403, detail="Bu yol proje disinda.")
    return resolved


def _safe_filename(filename: str) -> str:
    name = Path(filename or "upload.bin").name
    name = re.sub(r"[^A-Za-z0-9._ -]+", "_", name).strip(" .")
    return name or "upload.bin"


HTML_INTERFACE = r"""
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JARVIS Command Center</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #f5f8ff;
            --surface: rgba(255,255,255,.82);
            --solid: #ffffff;
            --line: rgba(30,41,59,.11);
            --text: #172033;
            --muted: #64748b;
            --blue: #2563eb;
            --cyan: #0891b2;
            --green: #16a34a;
            --red: #dc2626;
            --amber: #d97706;
            --shadow: 0 26px 80px rgba(15,23,42,.14);
            --soft: 0 10px 30px rgba(15,23,42,.08);
            --radius: 8px;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
        body {
            min-height: 100vh;
            color: var(--text);
            background:
                radial-gradient(circle at 12% 14%, rgba(37,99,235,.13), transparent 29%),
                radial-gradient(circle at 88% 8%, rgba(8,145,178,.10), transparent 28%),
                linear-gradient(135deg, #f8fafc 0%, #eef4ff 48%, #fbfdff 100%);
            overflow: hidden;
        }
        body::before {
            content: "";
            position: fixed;
            inset: 0;
            background-image:
                linear-gradient(rgba(37,99,235,.045) 1px, transparent 1px),
                linear-gradient(90deg, rgba(37,99,235,.045) 1px, transparent 1px);
            background-size: 42px 42px;
            mask-image: linear-gradient(to bottom, rgba(0,0,0,.95), transparent 92%);
            animation: gridDrift 20s linear infinite;
            pointer-events: none;
        }
        .shell {
            width: min(1240px, calc(100vw - 28px));
            height: min(890px, calc(100vh - 28px));
            margin: 14px auto;
            display: grid;
            grid-template-columns: 286px minmax(0, 1fr);
            gap: 14px;
            position: relative;
            z-index: 1;
        }
        .sidebar, .workspace {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            backdrop-filter: blur(24px);
            overflow: hidden;
        }
        .sidebar {
            display: flex;
            flex-direction: column;
            padding: 16px;
            gap: 16px;
        }
        .brand { display: flex; align-items: center; gap: 12px; min-width: 0; }
        .brand-mark {
            width: 46px;
            height: 46px;
            display: grid;
            place-items: center;
            border-radius: 8px;
            color: #fff;
            font-weight: 800;
            background: linear-gradient(135deg, var(--blue), var(--cyan));
            box-shadow: 0 16px 32px rgba(37,99,235,.24);
            animation: markFloat 3s ease-in-out infinite;
        }
        .brand-title { font-size: 1.05rem; font-weight: 800; letter-spacing: 0; }
        .brand-sub { margin-top: 2px; color: var(--muted); font-size: .78rem; }
        .status-card, .panel-card {
            background: var(--solid);
            border: 1px solid var(--line);
            border-radius: var(--radius);
            box-shadow: var(--soft);
        }
        .status-card { padding: 14px; }
        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            height: 30px;
            padding: 0 10px;
            border-radius: 999px;
            color: #065f46;
            background: #ecfdf5;
            border: 1px solid #bbf7d0;
            font-size: .8rem;
            font-weight: 800;
        }
        .status-pill.offline { color: #991b1b; background: #fef2f2; border-color: #fecaca; }
        .pulse-dot {
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: var(--green);
            box-shadow: 0 0 0 0 rgba(22,163,74,.42);
            animation: dotPulse 1.7s infinite;
        }
        .offline .pulse-dot { background: var(--red); animation: none; }
        .status-row { display: flex; justify-content: space-between; gap: 10px; margin-top: 10px; color: var(--muted); font-size: .82rem; }
        .status-row strong { color: var(--text); font-weight: 800; text-align: right; }
        .menu-title {
            color: var(--muted);
            font-size: .72rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: .09em;
            margin-bottom: 8px;
        }
        .nav { display: grid; gap: 7px; }
        .nav-btn, .quick-btn, .icon-btn, .send-btn {
            border: 1px solid var(--line);
            background: var(--solid);
            color: var(--text);
            border-radius: var(--radius);
            cursor: pointer;
            transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease, background .18s ease;
        }
        .nav-btn {
            height: 42px;
            padding: 0 11px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: .88rem;
            font-weight: 800;
            text-align: left;
        }
        .nav-btn span:first-child { display: flex; align-items: center; gap: 9px; min-width: 0; }
        .nav-btn.active {
            color: #fff;
            background: linear-gradient(135deg, var(--blue), var(--cyan));
            border-color: transparent;
            box-shadow: 0 16px 36px rgba(37,99,235,.20);
        }
        .nav-btn:not(.active):hover, .quick-btn:hover, .icon-btn:hover {
            transform: translateY(-1px);
            border-color: rgba(37,99,235,.28);
            box-shadow: var(--soft);
        }
        .mini-dot { width: 7px; height: 7px; border-radius: 999px; background: currentColor; opacity: .55; }
        .sidebar-foot { margin-top: auto; color: var(--muted); font-size: .78rem; line-height: 1.45; }
        .workspace {
            display: grid;
            grid-template-rows: auto minmax(0, 1fr) auto;
        }
        .topbar {
            min-height: 78px;
            padding: 18px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            border-bottom: 1px solid var(--line);
            background: rgba(255,255,255,.70);
        }
        h1 { font-size: clamp(1.18rem, 2vw, 1.7rem); line-height: 1.1; letter-spacing: 0; }
        .subtitle { color: var(--muted); margin-top: 5px; font-size: .88rem; }
        .toolbar { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; justify-content: flex-end; }
        .icon-btn {
            width: 40px;
            height: 40px;
            display: grid;
            place-items: center;
            font-size: 1rem;
        }
        .view-stack { min-height: 0; position: relative; }
        .view {
            position: absolute;
            inset: 0;
            display: none;
            padding: 20px;
            overflow: auto;
            animation: viewIn .28s ease both;
        }
        .view.active { display: block; }
        .chat-view.active { display: flex; flex-direction: column; gap: 12px; }
        .msg {
            max-width: min(780px, 84%);
            padding: 13px 15px;
            border-radius: var(--radius);
            line-height: 1.55;
            font-size: .94rem;
            white-space: pre-wrap;
            word-break: break-word;
            animation: messageIn .24s ease both;
            box-shadow: var(--soft);
        }
        .msg.user {
            align-self: flex-end;
            color: #fff;
            background: linear-gradient(135deg, var(--blue), #0f766e);
        }
        .msg.jarvis {
            align-self: flex-start;
            background: var(--solid);
            border: 1px solid var(--line);
        }
        .msg.system {
            align-self: center;
            max-width: 92%;
            color: var(--muted);
            background: rgba(255,255,255,.68);
            border: 1px dashed rgba(100,116,139,.24);
            box-shadow: none;
            font-size: .82rem;
        }
        .cards {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 12px;
        }
        .panel-card { padding: 16px; }
        .panel-card h2 { font-size: 1rem; margin-bottom: 6px; }
        .panel-card p { color: var(--muted); font-size: .88rem; line-height: 1.5; }
        .quick-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-top: 12px; }
        .quick-btn {
            min-height: 50px;
            padding: 12px;
            text-align: left;
            font-weight: 800;
            font-size: .88rem;
        }
        .metric-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
        .metric { padding: 14px; border-radius: var(--radius); background: var(--solid); border: 1px solid var(--line); box-shadow: var(--soft); }
        .metric label { color: var(--muted); font-size: .78rem; font-weight: 800; text-transform: uppercase; letter-spacing: .05em; }
        .metric strong { display: block; margin-top: 8px; font-size: 1.2rem; }
        .data-table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: .84rem; }
        .data-table th, .data-table td { padding: 9px 10px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
        .data-table th { color: var(--muted); text-transform: uppercase; letter-spacing: .05em; font-size: .72rem; }
        .mini-form { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin-top: 12px; }
        .mini-form .send-btn { min-height: 42px; }
        .scroll-box { max-height: 430px; overflow: auto; border: 1px solid var(--line); border-radius: var(--radius); background: rgba(255,255,255,.62); }
        .theme-cyber { --bg:#031111; --surface:rgba(2,18,22,.88); --solid:#06191f; --line:rgba(0,212,192,.24); --text:#dffefa; --muted:#7fd8d0; --blue:#00d4c0; --cyan:#38bdf8; }
        .theme-dark { --bg:#0f172a; --surface:rgba(15,23,42,.88); --solid:#111827; --line:rgba(148,163,184,.18); --text:#e5e7eb; --muted:#94a3b8; --blue:#60a5fa; --cyan:#22d3ee; }
        .theme-white { --bg:#f5f8ff; --surface:rgba(255,255,255,.82); --solid:#ffffff; --line:rgba(30,41,59,.11); --text:#172033; --muted:#64748b; --blue:#2563eb; --cyan:#0891b2; }
        .composer {
            padding: 16px;
            border-top: 1px solid var(--line);
            background: rgba(255,255,255,.74);
        }
        .input-wrap { display: grid; grid-template-columns: 48px minmax(0, 1fr) 112px; gap: 10px; align-items: center; }
        .attach-btn {
            width: 48px;
            min-height: 48px;
            display: grid;
            place-items: center;
            border: 1px solid var(--line);
            border-radius: var(--radius);
            background: var(--solid);
            color: var(--blue);
            font-size: 1.15rem;
            cursor: pointer;
            transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
        }
        .attach-btn:hover { transform: translateY(-1px); border-color: rgba(37,99,235,.32); box-shadow: var(--soft); }
        .drop-active .workspace { outline: 2px dashed rgba(37,99,235,.42); outline-offset: -10px; }
        .upload-chip {
            margin-bottom: 8px;
            display: none;
            width: fit-content;
            max-width: 100%;
            padding: 8px 10px;
            border-radius: var(--radius);
            background: rgba(37,99,235,.08);
            border: 1px solid rgba(37,99,235,.18);
            color: var(--muted);
            font-size: .82rem;
            font-weight: 800;
        }
        input {
            width: 100%;
            min-height: 48px;
            border-radius: var(--radius);
            border: 1px solid var(--line);
            background: var(--solid);
            color: var(--text);
            padding: 0 14px;
            font-size: .96rem;
            outline: none;
            transition: box-shadow .18s ease, border-color .18s ease;
        }
        input:focus { border-color: rgba(37,99,235,.55); box-shadow: 0 0 0 4px rgba(37,99,235,.10); }
        .send-btn {
            min-height: 48px;
            color: #fff;
            background: linear-gradient(135deg, var(--blue), var(--cyan));
            border-color: transparent;
            font-weight: 800;
        }
        .send-btn:hover { transform: translateY(-1px); box-shadow: 0 14px 32px rgba(37,99,235,.22); }
        .toast {
            position: fixed;
            right: 24px;
            bottom: 24px;
            max-width: 320px;
            padding: 12px 14px;
            border-radius: var(--radius);
            background: #0f172a;
            color: white;
            box-shadow: var(--shadow);
            transform: translateY(18px);
            opacity: 0;
            pointer-events: none;
            transition: .22s ease;
            z-index: 5;
            font-size: .88rem;
        }
        .toast.show { opacity: 1; transform: translateY(0); }
        @keyframes gridDrift { to { background-position: 42px 42px; } }
        @keyframes dotPulse { 70% { box-shadow: 0 0 0 10px rgba(22,163,74,0); } 100% { box-shadow: 0 0 0 0 rgba(22,163,74,0); } }
        @keyframes markFloat { 50% { transform: translateY(-1px); box-shadow: 0 18px 38px rgba(8,145,178,.30); } }
        @keyframes viewIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes messageIn { from { opacity: 0; transform: translateY(8px) scale(.985); } to { opacity: 1; transform: translateY(0) scale(1); } }
        @media (max-width: 900px) {
            body { overflow: auto; }
            .shell { height: auto; min-height: calc(100vh - 24px); width: calc(100vw - 24px); margin: 12px; grid-template-columns: 1fr; }
            .workspace { min-height: 74vh; }
            .view { position: relative; min-height: 560px; }
            .cards, .quick-grid, .metric-grid { grid-template-columns: 1fr; }
            .mini-form { grid-template-columns: 1fr; }
            .input-wrap { grid-template-columns: 48px 1fr; }
            .send-btn { grid-column: 1 / -1; }
            .msg { max-width: 94%; }
        }
    </style>
</head>
<body>
    <div class="shell">
        <aside class="sidebar">
            <div class="brand">
                <div class="brand-mark">J</div>
                <div>
                    <div class="brand-title">JARVIS</div>
                    <div class="brand-sub">Remote Command Center</div>
                </div>
            </div>

            <div class="status-card">
                <div id="socketState" class="status-pill"><span class="pulse-dot"></span><span>Bağlı</span></div>
                <div class="status-row"><span>Çekirdek</span><strong id="coreState">kontrol</strong></div>
                <div class="status-row"><span>İstemci</span><strong id="clientCount">1</strong></div>
                <div class="status-row"><span>Mesaj</span><strong id="historyCount">0</strong></div>
                <div class="status-row"><span>Çalışma</span><strong id="uptime">0 dk</strong></div>
            </div>

            <nav>
                <div class="menu-title">Menüler</div>
                <div class="nav">
                    <button class="nav-btn active" data-view="chat"><span><span class="mini-dot"></span>Sohbet</span><span>01</span></button>
                    <button class="nav-btn" data-view="remote"><span><span class="mini-dot"></span>Uzaktan Yönetim</span><span>02</span></button>
                    <button class="nav-btn" data-view="system"><span><span class="mini-dot"></span>Sistem</span><span>03</span></button>
                    <button class="nav-btn" data-view="project"><span><span class="mini-dot"></span>Proje</span><span>04</span></button>
                    <button class="nav-btn" data-view="tools"><span><span class="mini-dot"></span>Araçlar</span><span>05</span></button>
                    <button class="nav-btn" data-view="plugins"><span><span class="mini-dot"></span>Pluginler</span><span>06</span></button>
                    <button class="nav-btn" data-view="settings"><span><span class="mini-dot"></span>Ayarlar</span><span>07</span></button>
                    <button class="nav-btn" data-view="ops"><span><span class="mini-dot"></span>Operasyon</span><span>08</span></button>
                    <button class="nav-btn" data-view="palette"><span><span class="mini-dot"></span>Komut Paleti</span><span>09</span></button>
                </div>
            </nav>

            <div class="sidebar-foot">
                Panel, yerel FastAPI sunucusuna bağlıdır. Aynı ağdan erişim için router/firewall ayarı gerekebilir.
            </div>
        </aside>

        <main class="workspace">
            <header class="topbar">
                <div>
                    <h1 id="viewTitle">Sohbet</h1>
                    <div class="subtitle" id="clockLine">Panel hazırlanıyor</div>
                </div>
                <div class="toolbar">
                    <button class="icon-btn" id="historyBtn" title="Geçmişi yükle" aria-label="Geçmişi yükle">⌘</button>
                    <button class="icon-btn" id="copyBtn" title="Sohbeti kopyala" aria-label="Sohbeti kopyala">⧉</button>
                    <button class="icon-btn" id="clearBtn" title="Ekranı temizle" aria-label="Ekranı temizle">⌫</button>
                    <button class="icon-btn" id="reconnectBtn" title="Yeniden bağlan" aria-label="Yeniden bağlan">↻</button>
                </div>
            </header>

            <section class="view-stack">
                <div class="view chat-view active" id="view-chat">
                    <div class="msg jarvis">Sistem aktif, emirlerinizi bekliyorum patron.</div>
                </div>

                <div class="view" id="view-remote">
                    <div class="cards">
                        <div class="panel-card">
                            <h2>Uzaktan Yönetim</h2>
                            <div class="quick-grid">
                                <button class="quick-btn" data-command="Günlük brifing hazırla">Günlük brifing</button>
                                <button class="quick-btn" data-command="Web panelini aç">Paneli aç</button>
                                <button class="quick-btn" data-command="Mikrofonu kapat">Mikrofonu kapat</button>
                                <button class="quick-btn" data-command="Mikrofonu aç">Mikrofonu aç</button>
                            </div>
                        </div>
                        <div class="panel-card">
                            <h2>Hızlı Aksiyonlar</h2>
                            <div class="quick-grid">
                                <button class="quick-btn" data-command="Hava durumu nasıl">Hava durumu</button>
                                <button class="quick-btn" data-command="Bugün takvimimde ne var">Takvim</button>
                                <button class="quick-btn" data-command="Hatırlatıcılarımı göster">Hatırlatıcı</button>
                                <button class="quick-btn" data-command="Neler diyebilirim komutlarını göster">Komut rehberi</button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="view" id="view-system">
                    <div class="metric-grid">
                        <div class="metric"><label>Çekirdek</label><strong id="metricCore">-</strong></div>
                        <div class="metric"><label>Bağlı istemci</label><strong id="metricClients">-</strong></div>
                        <div class="metric"><label>Geçmiş</label><strong id="metricHistory">-</strong></div>
                    </div>
                    <div class="cards" style="margin-top:12px">
                        <div class="panel-card">
                            <h2>Sistem Komutları</h2>
                            <div class="quick-grid">
                                <button class="quick-btn" data-command="Genel sistem sağlık raporu ver">Sağlık raporu</button>
                                <button class="quick-btn" data-command="Pil durumu nedir">Pil durumu</button>
                                <button class="quick-btn" data-command="Ağ durumunu analiz et">Ağ analizi</button>
                                <button class="quick-btn" data-command="Sesi yüzde 30 yap">Sesi yüzde 30</button>
                            </div>
                        </div>
                        <div class="panel-card">
                            <h2>Odak</h2>
                            <div class="quick-grid">
                                <button class="quick-btn" data-command="Odak modu için dikkat dağıtıcıları raporla">Odak raporu</button>
                                <button class="quick-btn" data-command="25 dakikalık odak seansı başlat">25 dk odak</button>
                                <button class="quick-btn" data-command="Ne kadar sürem kaldı">Sayaç durumu</button>
                                <button class="quick-btn" data-command="Masaüstünü göster">Masaüstü</button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="view" id="view-project">
                    <div class="cards">
                        <div class="panel-card">
                            <h2>Proje Kontrolü</h2> 
                            <div class="quick-grid">
                                <button class="quick-btn" data-command="Proje anlık görüntüsü al">Anlık görüntü</button>
                                <button class="quick-btn" data-command="Kod haritasını çıkar">Kod haritası</button>
                                <button class="quick-btn" data-command="Projedeki büyük dosyaları göster">Büyük dosyalar</button>
                                <button class="quick-btn" data-command="Güvenli temizlik taraması yap">Temizlik taraması</button>
                            </div>
                        </div>
                        <div class="panel-card">
                            <h2>Geliştirme</h2>
                            <div class="quick-grid">
                                <button class="quick-btn" data-command="Jarvis geçmişini raporla">Araç geçmişi</button>
                                <button class="quick-btn" data-command="Proje yedek planı hazırla">Yedek planı</button>
                                <button class="quick-btn" data-command="GitHub bildirimlerimi kontrol et">GitHub</button>
                                <button class="quick-btn" data-command="Vercel projelerim ne durumda">Vercel</button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="view" id="view-tools">
                    <div class="cards">
                        <div class="panel-card">
                            <h2>Siber ve Ağ Araçları</h2>
                            <div class="quick-grid">
                                <button class="quick-btn" data-command="Yerel portları tara">Port tarama</button>
                                <button class="quick-btn" data-command="Wi-Fi ağımı analiz et">Wi-Fi analiz</button>
                                <button class="quick-btn" data-command="8.8.8.8 IP adresini sorgula">IP lookup</button>
                                <button class="quick-btn" data-command="Borsa ve piyasa raporu ver">Piyasa</button>
                            </div>
                        </div>
                        <div class="panel-card">
                            <h2>Not ve Üretkenlik</h2>
                            <div class="quick-grid">
                                <button class="quick-btn" data-command="Notlarımı göster">Notlar</button>
                                <button class="quick-btn" data-command="Panodaki metni özetle">Pano özeti</button>
                                <button class="quick-btn" data-command="Bugünkü görevlerimi göster">Görevler</button>
                                <button class="quick-btn" data-command="Aktif uygulama kullanımını kaydet">Uygulama kaydı</button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="view" id="view-plugins">
                    <div class="panel-card">
                        <h2>Plugin Manager</h2>
                        <p>Yüklü pluginleri gerçek tablo üzerinden izle, risk seviyesini gör ve hızlıca aç/kapat.</p>
                        <div class="scroll-box"><table class="data-table" id="pluginsTable"></table></div>
                    </div>
                </div>

                <div class="view" id="view-settings">
                    <div class="cards">
                        <div class="panel-card">
                            <h2>Settings Web</h2>
                            <p>Sesli komutla değişen aynı ayar deposunu buradan da yönetebilirsin.</p>
                            <div class="mini-form">
                                <input id="settingSection" placeholder="section">
                                <input id="settingKey" placeholder="key">
                                <input id="settingValue" placeholder="value">
                                <button class="send-btn" id="saveSettingBtn">Kaydet</button>
                            </div>
                            <div class="scroll-box" style="margin-top:12px"><table class="data-table" id="settingsTable"></table></div>
                        </div>
                        <div class="panel-card">
                            <h2>Tema</h2>
                            <div class="quick-grid">
                                <button class="quick-btn" data-theme="cyber">Cyber</button>
                                <button class="quick-btn" data-theme="dark">Dark</button>
                                <button class="quick-btn" data-theme="white">White</button>
                                <button class="quick-btn" data-command="Ayarlar panelini aç">Desktop settings</button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="view" id="view-ops">
                    <div class="cards">
                        <div class="panel-card">
                            <h2>Canlı Log & Onaylar</h2>
                            <div class="scroll-box"><table class="data-table" id="opsTable"></table></div>
                        </div>
                        <div class="panel-card">
                            <h2>Workflow, Memory, Files</h2>
                            <div class="quick-grid">
                                <button class="quick-btn" id="loadWorkflowsBtn">Workflow builder verisi</button>
                                <button class="quick-btn" id="loadMemoryBtn">Hafıza ekranı</button>
                                <button class="quick-btn" id="loadFilesBtn">Dosya yöneticisi</button>
                                <button class="quick-btn" data-command="Workflow builder aç">Workflow UI aç</button>
                            </div>
                            <div class="scroll-box" style="margin-top:12px"><table class="data-table" id="opsDataTable"></table></div>
                        </div>
                    </div>
                </div>

                <div class="view" id="view-palette">
                    <div class="panel-card">
                        <h2>Komut Paleti</h2>
                        <p>Komut ara, seç ve JARVIS'e gönder. Yazdıkça liste filtrelenir.</p>
                        <div style="margin-top:12px">
                            <input type="text" id="paletteSearch" placeholder="Komut ara..." autocomplete="off">
                        </div>
                        <div class="quick-grid" id="paletteList">
                            <button class="quick-btn" data-command="Araçlar menüsünü aç">Araçlar menüsü</button>
                            <button class="quick-btn" data-command="Domain DNS sağlık kontrolü yap">DNS kontrol</button>
                            <button class="quick-btn" data-command="SSL sertifika denetimi yap">SSL denetim</button>
                            <button class="quick-btn" data-command="URL risk kontrolü yap">URL risk</button>
                            <button class="quick-btn" data-command="Dosya hash hesapla">Dosya hash</button>
                            <button class="quick-btn" data-command="Süreç risk taraması yap">Süreç riski</button>
                            <button class="quick-btn" data-command="İnternet hız testi yap">Hız testi</button>
                            <button class="quick-btn" data-command="Parola gücü denetimi yap">Parola gücü</button>
                            <button class="quick-btn" data-command="Proje anlık görüntüsü al">Proje görüntüsü</button>
                            <button class="quick-btn" data-command="Kod haritasını çıkar">Kod haritası</button>
                        </div>
                    </div>
                </div>
            </section>

            <footer class="composer">
                <div class="upload-chip" id="uploadChip">Dosya bekleniyor...</div>
                <div class="input-wrap">
                    <button class="attach-btn" id="attachBtn" title="Dosya ekle" aria-label="Dosya ekle">📎</button>
                    <input type="file" id="fileInput" hidden accept="image/*,.pdf,.txt,.md,.py,.json,.csv,.log,.html,.css,.js,.xml,.yaml,.yml">
                    <input type="text" id="cmdInput" placeholder="Komut yazın..." autocomplete="off">
                    <button class="send-btn" id="sendBtn">Gönder</button>
                </div>
            </footer>
        </main>
    </div>
    <div class="toast" id="toast"></div>

    <script>
        const chatArea = document.getElementById('view-chat');
        const cmdInput = document.getElementById('cmdInput');
        const socketState = document.getElementById('socketState');
        const coreState = document.getElementById('coreState');
        const clientCount = document.getElementById('clientCount');
        const historyCount = document.getElementById('historyCount');
        const uptime = document.getElementById('uptime');
        const clockLine = document.getElementById('clockLine');
        const toast = document.getElementById('toast');
        const viewTitle = document.getElementById('viewTitle');
        const attachBtn = document.getElementById('attachBtn');
        const fileInput = document.getElementById('fileInput');
        const uploadChip = document.getElementById('uploadChip');
        let ws;
        let reconnectTimer;

        const titles = {
            chat: 'Sohbet',
            remote: 'Uzaktan Yönetim',
            system: 'Sistem',
            project: 'Proje',
            tools: 'Araçlar',
            plugins: 'Plugin Manager',
            settings: 'Settings Web',
            ops: 'Operasyon',
            palette: 'Komut Paleti'
        };

        function connectSocket() {
            clearTimeout(reconnectTimer);
            const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
            ws = new WebSocket(`${protocol}://${window.location.host}/ws/chat`);
            ws.onopen = () => setSocketState(true);
            ws.onclose = () => {
                setSocketState(false);
                reconnectTimer = setTimeout(connectSocket, 1800);
            };
            ws.onerror = () => setSocketState(false);
            ws.onmessage = (event) => appendMessage(event.data, classifyMessage(event.data));
        }

        function setSocketState(online) {
            socketState.classList.toggle('offline', !online);
            socketState.querySelector('span:last-child').innerText = online ? 'Bağlı' : 'Bağlantı bekliyor';
        }

        function classifyMessage(text) {
            return String(text).startsWith('SYS:') ? 'system' : 'jarvis';
        }

        function sendCmd() {
            const val = cmdInput.value.trim();
            if (!val) return;
            switchView('chat');
            appendMessage(val, 'user');
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(val);
            } else {
                appendMessage('SYS: WebSocket bağlı değil, yeniden bağlanılıyor.', 'system');
                connectSocket();
            }
            cmdInput.value = '';
            cmdInput.focus();
        }

        async function uploadAndAnalyze(file) {
            if (!file) return;
            switchView('chat');
            const prompt = cmdInput.value.trim();
            uploadChip.style.display = 'inline-flex';
            uploadChip.innerText = `Yükleniyor: ${file.name}`;
            appendMessage(`${file.name} dosyasını analiz et${prompt ? ': ' + prompt : ''}`, 'user');
            try {
                const params = new URLSearchParams({
                    filename: file.name || 'upload.bin',
                    prompt: prompt || 'Bu dosyayı analiz et ve önemli noktaları özetle.'
                });
                const response = await fetch(`/api/uploads/analyze?${params.toString()}`, {
                    method: 'POST',
                    headers: {'Content-Type': file.type || 'application/octet-stream'},
                    body: file
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.detail || 'Upload başarısız');
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    appendMessage(data.analysis || 'Dosya analizi tamamlandı.', 'jarvis');
                }
                showToast('Dosya analiz edildi.');
            } catch (error) {
                appendMessage(`SYS: Dosya analizi başarısız: ${error.message || error}`, 'system');
            } finally {
                uploadChip.style.display = 'none';
                fileInput.value = '';
                cmdInput.value = '';
                cmdInput.focus();
            }
        }

        function appendMessage(text, sender) {
            const node = document.createElement('div');
            node.className = `msg ${sender}`;
            node.innerText = text;
            chatArea.appendChild(node);
            chatArea.scrollTop = chatArea.scrollHeight;
        }

        function switchView(name) {
            document.querySelectorAll('.view').forEach((view) => view.classList.remove('active'));
            document.querySelectorAll('.nav-btn').forEach((btn) => btn.classList.toggle('active', btn.dataset.view === name));
            document.getElementById(`view-${name}`).classList.add('active');
            viewTitle.innerText = titles[name] || 'Panel';
        }

        function showToast(text) {
            toast.innerText = text;
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 1800);
        }

        async function refreshStatus() {
            try {
                const response = await fetch('/api/status', { cache: 'no-store' });
                const data = await response.json();
                const coreText = data.core_ready ? 'hazır' : 'beklemede';
                coreState.innerText = coreText;
                clientCount.innerText = data.clients;
                historyCount.innerText = data.history_count;
                document.getElementById('metricCore').innerText = coreText;
                document.getElementById('metricClients').innerText = data.clients;
                document.getElementById('metricHistory').innerText = data.history_count;
                const minutes = Math.floor(data.uptime_seconds / 60);
                uptime.innerText = minutes < 60 ? `${minutes} dk` : `${Math.floor(minutes / 60)} sa ${minutes % 60} dk`;
            } catch (error) {
                coreState.innerText = 'bilinmiyor';
            }
        }

        function fillTable(tableId, headers, rows) {
            const table = document.getElementById(tableId);
            if (!table) return;
            const head = `<tr>${headers.map((h) => `<th>${h}</th>`).join('')}</tr>`;
            const body = rows.map((row) => `<tr>${row.map((cell) => `<td>${String(cell ?? '').replace(/[<>&]/g, (c) => ({'<':'&lt;','>':'&gt;','&':'&amp;'}[c]))}</td>`).join('')}</tr>`).join('');
            table.innerHTML = head + body;
        }

        async function refreshPlugins() {
            try {
                const data = await (await fetch('/api/plugins', { cache: 'no-store' })).json();
                const rows = (data.plugins || []).map((p) => [p.name, p.enabled === false ? 'kapalı' : 'aktif', p.category || '-', p.danger || '-', p.source || '-']);
                fillTable('pluginsTable', ['Plugin', 'Durum', 'Kategori', 'Risk', 'Kaynak'], rows);
            } catch (error) {
                fillTable('pluginsTable', ['Hata'], [['Plugin listesi okunamadı']]);
            }
        }

        async function refreshSettings() {
            try {
                const data = await (await fetch('/api/settings', { cache: 'no-store' })).json();
                const rows = [];
                Object.entries(data.settings || {}).forEach(([section, values]) => {
                    Object.entries(values || {}).forEach(([key, value]) => rows.push([section, key, JSON.stringify(value)]));
                });
                const theme = data.settings?.web_panel?.theme;
                if (theme) {
                    document.body.classList.remove('theme-cyber', 'theme-dark', 'theme-white');
                    document.body.classList.add(`theme-${theme}`);
                }
                fillTable('settingsTable', ['Section', 'Key', 'Value'], rows);
            } catch (error) {
                fillTable('settingsTable', ['Hata'], [['Ayarlar okunamadı']]);
            }
        }

        async function refreshOps() {
            try {
                const [logs, approvals, metrics] = await Promise.all([
                    fetch('/api/logs?limit=20', { cache: 'no-store' }).then((r) => r.json()),
                    fetch('/api/approvals', { cache: 'no-store' }).then((r) => r.json()),
                    fetch('/api/system-metrics', { cache: 'no-store' }).then((r) => r.json()),
                ]);
                const rows = [
                    ['METRIC', 'CPU', `${metrics.cpu ?? '-'}%`],
                    ['METRIC', 'RAM', `${metrics.ram ?? '-'}%`],
                    ['METRIC', 'DISK', `${metrics.disk ?? '-'}%`],
                    ...((approvals.approvals || []).map((a) => ['APPROVAL', a.tool, a.reason || a.id])),
                    ...((logs.logs || []).map((l) => [l.level || '-', l.category || '-', l.message || '-'])),
                ];
                fillTable('opsTable', ['Tip', 'Alan', 'Detay'], rows);
            } catch (error) {
                fillTable('opsTable', ['Hata'], [['Operasyon verisi okunamadı']]);
            }
        }

        async function loadOpsData(kind) {
            const url = kind === 'workflows' ? '/api/workflows' : kind === 'memory' ? '/api/memory' : '/api/files';
            try {
                const data = await (await fetch(url, { cache: 'no-store' })).json();
                const rows = [];
                if (kind === 'workflows') (data.workflows || []).forEach((w, i) => rows.push([i + 1, w.name || w.title || 'workflow', JSON.stringify(w).slice(0, 500)]));
                if (kind === 'memory') (data.items || []).forEach((m) => rows.push([m.name, `${m.size} byte`, (m.preview || '').slice(0, 500)]));
                if (kind === 'files') (data.items || []).forEach((f) => rows.push([f.type, f.path, f.size]));
                fillTable('opsDataTable', ['Tip', 'Ad', 'Detay'], rows);
            } catch (error) {
                fillTable('opsDataTable', ['Hata'], [[`${kind} okunamadı`]]);
            }
        }

        function tickClock() {
            const now = new Date();
            clockLine.innerText = now.toLocaleDateString('tr-TR', { weekday: 'long', day: '2-digit', month: 'long' }) + ' · ' + now.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
        }

        document.getElementById('sendBtn').addEventListener('click', sendCmd);
        attachBtn?.addEventListener('click', () => fileInput.click());
        fileInput?.addEventListener('change', () => uploadAndAnalyze(fileInput.files?.[0]));
        cmdInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') sendCmd();
        });
        window.addEventListener('paste', (event) => {
            const files = [...(event.clipboardData?.files || [])];
            if (files.length) {
                event.preventDefault();
                uploadAndAnalyze(files[0]);
            }
        });
        window.addEventListener('dragover', (event) => {
            event.preventDefault();
            document.body.classList.add('drop-active');
        });
        window.addEventListener('dragleave', () => document.body.classList.remove('drop-active'));
        window.addEventListener('drop', (event) => {
            event.preventDefault();
            document.body.classList.remove('drop-active');
            const file = event.dataTransfer?.files?.[0];
            if (file) uploadAndAnalyze(file);
        });
        document.querySelectorAll('[data-command]').forEach((button) => {
            button.addEventListener('click', () => {
                cmdInput.value = button.dataset.command;
                sendCmd();
            });
        });
        document.querySelectorAll('.nav-btn').forEach((button) => {
            button.addEventListener('click', () => {
                switchView(button.dataset.view);
                if (button.dataset.view === 'plugins') refreshPlugins();
                if (button.dataset.view === 'settings') refreshSettings();
                if (button.dataset.view === 'ops') refreshOps();
            });
        });
        document.querySelectorAll('[data-theme]').forEach((button) => {
            button.addEventListener('click', async () => {
                const theme = button.dataset.theme;
                document.body.classList.remove('theme-cyber', 'theme-dark', 'theme-white');
                document.body.classList.add(`theme-${theme}`);
                try {
                    await fetch('/api/settings', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({section: 'web_panel', key: 'theme', value: theme})
                    });
                    refreshSettings();
                } catch (error) {}
                showToast(`Tema: ${theme}`);
            });
        });
        document.getElementById('saveSettingBtn')?.addEventListener('click', async () => {
            const section = document.getElementById('settingSection').value.trim();
            const key = document.getElementById('settingKey').value.trim();
            let value = document.getElementById('settingValue').value.trim();
            if (value === 'true') value = true;
            else if (value === 'false') value = false;
            else if (!Number.isNaN(Number(value)) && value !== '') value = Number(value);
            await fetch('/api/settings', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({section, key, value}) });
            refreshSettings();
            showToast('Ayar kaydedildi.');
        });
        document.getElementById('loadWorkflowsBtn')?.addEventListener('click', () => loadOpsData('workflows'));
        document.getElementById('loadMemoryBtn')?.addEventListener('click', () => loadOpsData('memory'));
        document.getElementById('loadFilesBtn')?.addEventListener('click', () => loadOpsData('files'));
        document.getElementById('clearBtn').addEventListener('click', () => {
            chatArea.innerHTML = '';
            appendMessage('SYS: Panel ekranı temizlendi.', 'system');
        });
        document.getElementById('historyBtn').addEventListener('click', async () => {
            try {
                const response = await fetch('/api/history', { cache: 'no-store' });
                const data = await response.json();
                chatArea.innerHTML = '';
                (data.messages || []).forEach((item) => appendMessage(item, classifyMessage(item)));
                switchView('chat');
                showToast('Geçmiş yüklendi.');
            } catch (error) {
                showToast('Geçmiş yüklenemedi.');
            }
        });
        document.getElementById('copyBtn').addEventListener('click', async () => {
            const text = [...chatArea.querySelectorAll('.msg')].map((node) => node.innerText).join('\n\n');
            try {
                await navigator.clipboard.writeText(text);
                showToast('Sohbet kopyalandı.');
            } catch (error) {
                showToast('Kopyalama başarısız.');
            }
        });
        document.getElementById('reconnectBtn').addEventListener('click', () => {
            if (ws) ws.close();
            connectSocket();
            showToast('Bağlantı yenileniyor.');
        });
        const paletteSearch = document.getElementById('paletteSearch');
        if (paletteSearch) {
            paletteSearch.addEventListener('input', () => {
                const needle = paletteSearch.value.toLocaleLowerCase('tr-TR');
                document.querySelectorAll('#paletteList .quick-btn').forEach((button) => {
                    const text = (button.innerText + ' ' + button.dataset.command).toLocaleLowerCase('tr-TR');
                    button.style.display = text.includes(needle) ? '' : 'none';
                });
            });
        }

        connectSocket();
        tickClock();
        refreshStatus();
        refreshPlugins();
        refreshSettings();
        refreshOps();
        setInterval(tickClock, 1000);
        setInterval(refreshStatus, 5000);
        setInterval(refreshOps, 7000);
        window.addEventListener('load', () => cmdInput.focus());
    </script>
</body>
</html>
"""


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        for item in message_history[-25:]:
            try:
                await websocket.send_text(item)
            except Exception:
                pass

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_message(self, message: str):
        message_history.append(message)
        del message_history[:-MAX_HISTORY]
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()


@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    return HTML_INTERFACE


@app.get("/api/status")
async def panel_status():
    return {
        "core_ready": bool(jarvis_core_instance),
        "clients": len(manager.active_connections),
        "history_count": len(message_history),
        "uptime_seconds": int(time.time() - server_started_at),
    }


@app.get("/api/history")
async def panel_history():
    return {"messages": message_history[-MAX_HISTORY:]}


@app.get("/api/events")
async def panel_events(limit: int = 80):
    from core.event_bus import recent_events

    return {"events": recent_events(limit)}


@app.get("/api/logs")
async def panel_logs(limit: int = 120, level: str = "", category: str = ""):
    from core.jarvis_logger import read_logs

    return {"logs": read_logs(limit, level, category)}


@app.get("/api/system-metrics")
async def panel_system_metrics():
    try:
        import psutil

        battery = psutil.sensors_battery()
        return {
            "cpu": psutil.cpu_percent(interval=0.05),
            "ram": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage(str(BASE_DIR)).percent,
            "battery": None if battery is None else battery.percent,
            "plugged": None if battery is None else battery.power_plugged,
            "processes": len(psutil.pids()),
        }
    except Exception as exc:
        return {"error": str(exc)}


@app.get("/api/settings")
async def panel_settings():
    from core.settings_store import load_settings

    return {"settings": load_settings()}


@app.post("/api/settings")
async def panel_update_setting(payload: SettingUpdate):
    from core.settings_store import set_setting

    if not payload.section or not payload.key:
        raise HTTPException(status_code=400, detail="section ve key gerekli.")
    return {"settings": set_setting(payload.section, payload.key, payload.value)}


@app.get("/api/workflows")
async def panel_workflows():
    path = MEMORY_DIR / "workflows.json"
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
        else:
            data = []
    except Exception:
        data = []
    return {"workflows": data}


@app.get("/api/memory")
async def panel_memory():
    from core.settings_store import get_setting

    if not get_setting("memory", "editable", True):
        raise HTTPException(status_code=403, detail="Memory editor kapali.")
    items = []
    max_chars = int(get_setting("memory", "max_preview_chars", 20000) or 20000)
    MEMORY_DIR.mkdir(exist_ok=True)
    for path in sorted(MEMORY_DIR.glob("*"))[:80]:
        if path.is_file():
            preview = ""
            try:
                preview = path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
            except Exception:
                preview = "<binary/unreadable>"
            items.append({"name": path.name, "size": path.stat().st_size, "preview": preview})
    return {"items": items}


@app.get("/api/files")
async def panel_files(path: str = "."):
    from core.settings_store import get_setting

    if not get_setting("web_panel", "file_manager_enabled", True):
        raise HTTPException(status_code=403, detail="File manager kapali.")
    root = _safe_path(path)
    if not root.exists():
        raise HTTPException(status_code=404, detail="Yol bulunamadi.")
    if root.is_file():
        return {"path": str(root.relative_to(BASE_DIR)), "type": "file", "size": root.stat().st_size}
    rows = []
    for item in sorted(root.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))[:200]:
        try:
            rows.append({
                "name": item.name,
                "path": str(item.relative_to(BASE_DIR)),
                "type": "dir" if item.is_dir() else "file",
                "size": 0 if item.is_dir() else item.stat().st_size,
            })
        except Exception:
            pass
    return {"path": str(root.relative_to(BASE_DIR)) if root != BASE_DIR else ".", "items": rows}


@app.get("/api/approvals")
async def panel_approvals():
    from core.approval_center import pending

    return {"approvals": pending(100)}


@app.post("/api/approvals/{approval_id}/{decision}")
async def panel_approval_decision(approval_id: str, decision: str):
    from core.approval_center import decide

    if decision not in {"approve", "reject"}:
        raise HTTPException(status_code=400, detail="Gecersiz onay karari.")
    return {"status": decide(approval_id, decision == "approve")}


@app.get("/api/plugins")
async def panel_plugins():
    from actions.plugin_manager import run as plugin_manager

    payload = plugin_manager(action="list", detail="json")
    try:
        return json.loads(payload)
    except Exception:
        return {"count": 0, "plugins": [], "raw": payload}


@app.post("/api/plugins/{plugin_name}")
async def panel_plugin_update(plugin_name: str, payload: PluginUpdate):
    from actions.plugin_manager import run as plugin_manager

    action = payload.action.strip().lower()
    if action not in {"enable", "disable", "set_danger"}:
        raise HTTPException(status_code=400, detail="Gecersiz plugin islemi.")
    result = plugin_manager(action=action, name=plugin_name, danger=payload.danger or "")
    return {"status": "ok", "result": result}


@app.post("/api/panel-note")
async def panel_note(payload: PanelNote):
    await manager.broadcast_message("SYS: " + payload.message)
    return {"status": "ok"}


@app.post("/api/remote")
async def remote_exec(payload: RemoteCommand):
    global jarvis_core_instance, last_telegram_chat_id
    from core.settings_store import get_setting

    if not get_setting("web_panel", "remote_enabled", True):
        raise HTTPException(status_code=403, detail="Remote komutlar kapali.")
    if payload.chat_id:
        last_telegram_chat_id = payload.chat_id
    if jarvis_core_instance:
        asyncio.run_coroutine_threadsafe(
            jarvis_core_instance.process_message(payload.command),
            jarvis_core_instance._loop,
        )
        return {"status": "ok"}
    raise HTTPException(status_code=503, detail="Cekirdek hazir degil.")


@app.post("/api/uploads/analyze")
async def upload_and_analyze(request: Request, filename: str = "upload.bin", prompt: str = ""):
    from actions.upload_analyzer import uploaded_file_analyzer

    content_length = int(request.headers.get("content-length") or 0)
    if content_length > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Dosya cok buyuk. Maksimum 20 MB.")

    data = await request.body()
    if not data:
        raise HTTPException(status_code=400, detail="Dosya bos veya okunamadi.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Dosya cok buyuk. Maksimum 20 MB.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    safe_name = _safe_filename(filename)
    path = UPLOAD_DIR / f"{stamp}-{safe_name}"
    path.write_bytes(data)

    await manager.broadcast_message(f"SYS: Dosya yuklendi: {path.name}")
    analysis = await asyncio.to_thread(uploaded_file_analyzer, str(path), prompt)
    await manager.broadcast_message("JARVIS: " + analysis)
    return {
        "status": "ok",
        "filename": path.name,
        "path": str(path.relative_to(BASE_DIR)),
        "analysis": analysis,
    }


@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if jarvis_core_instance:
                asyncio.run_coroutine_threadsafe(
                    jarvis_core_instance.process_message(data),
                    jarvis_core_instance._loop,
                )
            else:
                await manager.broadcast_message("SYS: JARVIS cekirdegi henuz hazir degil.")
    except WebSocketDisconnect:
        manager.disconnect(websocket)


def send_to_web_chat(message: str):
    if not message:
        return
    if web_loop and web_loop.is_running():
        asyncio.run_coroutine_threadsafe(manager.broadcast_message(message), web_loop)
        return
    message_history.append(message)
    del message_history[:-MAX_HISTORY]


def send_to_telegram(message: str):
    global last_telegram_chat_id
    if not last_telegram_chat_id:
        return
    from services.telegram_bot import BOT_TOKEN

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": last_telegram_chat_id, "text": message}, timeout=5)
    except Exception as e:
        print(f"[JARVIS-TELEGRAM] Hata: {e}")


def send_photo_to_telegram(photo_path: str, caption: str | None = None):
    """JARVIS'in cektigi fotografi Telegram chatine alt yazisiyla gonderir."""
    global last_telegram_chat_id
    if not last_telegram_chat_id:
        print("[WEB SERVER] Telegram chat_id bulunamadigi icin fotograf gonderilemedi.")
        return
    if not os.path.exists(photo_path):
        print(f"[WEB SERVER] Fotograf dosyasi bulunamadi: {photo_path}")
        return

    from services.telegram_bot import BOT_TOKEN

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    try:
        with open(photo_path, "rb") as photo_file:
            files = {"photo": photo_file}
            data = {"chat_id": last_telegram_chat_id}
            if caption:
                data["caption"] = caption
            requests.post(url, data=data, files=files, timeout=15)
            print("[JARVIS-TELEGRAM] Fotograf basariyla Telegram'a iletildi.")
    except Exception as e:
        print(f"[JARVIS-TELEGRAM] Fotograf gonderilirken hata: {e}")


def start_jarvis_web_server(jarvis_instance=None):
    global jarvis_core_instance, web_server_started
    if jarvis_instance:
        jarvis_core_instance = jarvis_instance
    if web_server_started:
        return
    web_server_started = True

    def _run():
        global web_loop
        web_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(web_loop)
        config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="warning")
        server = uvicorn.Server(config)
        web_loop.run_until_complete(server.serve())

    threading.Thread(target=_run, daemon=True).start()
