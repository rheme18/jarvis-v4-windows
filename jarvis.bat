@echo off
chcp 65001 > nul
title J.A.R.V.I.S V4 Launcher
cd /d "%~dp0"

echo [JARVIS] Sanal ortam aktifleştiriliyor...
call venv\Scripts\activate.bat

echo [JARVIS] Core başlatılıyor...
python main.py

pause
