"""
TTS (Text-to-Speech) — Windows için yüksek performanslı SAPI motoru.
comtypes / win32com bellek içi COM nesnesi kullanır; sıfır gecikmeli okuma sağlar.
PowerShell alt süreci yalnızca yedek fallback olarak tutulur.
"""

from __future__ import annotations

import subprocess
import threading
from typing import Callable, List, Optional

_sapi_voice = None
_sapi_lock = threading.Lock()


def _get_in_memory_voice():
    """Hafıza içi SAPI SpVoice nesnesini başlatır veya döner."""
    global _sapi_voice
    if _sapi_voice is not None:
        return _sapi_voice
    with _sapi_lock:
        if _sapi_voice is not None:
            return _sapi_voice
        try:
            import comtypes.client
            _sapi_voice = comtypes.client.CreateObject("SAPI.SpVoice")
            return _sapi_voice
        except Exception:
            pass
        try:
            import win32com.client
            _sapi_voice = win32com.client.Dispatch("SAPI.SpVoice")
            return _sapi_voice
        except Exception:
            pass
    return None


def speak_text(text: str, on_done: Optional[Callable[[], None]] = None, blocking: bool = False):
    """
    Metni sesli olarak okur.
    Öncelikle bellek-içi hızlı SAPI (comtypes/win32com) kullanılır,
    başarısız olursa PowerShell SAPI yedeğine düşer.
    """
    if not text or not str(text).strip():
        if on_done:
            on_done()
        return

    clean_text = str(text).strip()
    if len(clean_text) > 600:
        clean_text = clean_text[:600] + "..."

    def _worker():
        # 1. Hızlı bellek-içi COM denemesi
        voice = _get_in_memory_voice()
        spoken = False
        if voice:
            try:
                # 1 = SVSFlagsAsync (comtypes/win32com için)
                voice.Speak(clean_text, 0 if blocking else 1)
                spoken = True
            except Exception:
                spoken = False

        # 2. Yedek: PowerShell SAPI
        if not spoken:
            try:
                safe_text = clean_text.replace("'", "''").replace('"', '`"')
                script = (
                    "Add-Type -AssemblyName System.Speech; "
                    f"$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                    f"$s.Speak('{safe_text}')"
                )
                subprocess.run(
                    ["powershell", "-WindowStyle", "Hidden", "-Command", script],
                    check=False,
                    timeout=30,
                )
            except Exception:
                pass

        if on_done:
            try:
                on_done()
            except Exception:
                pass

    if blocking:
        _worker()
    else:
        threading.Thread(target=_worker, daemon=True).start()


def get_available_voices() -> List[str]:
    """Windows'taki mevcut SAPI seslerini listeler."""
    try:
        voice = _get_in_memory_voice()
        if voice and hasattr(voice, "GetVoices"):
            voices = voice.GetVoices()
            names = []
            for i in range(voices.Count):
                names.append(voices.Item(i).GetDescription())
            if names:
                return names
    except Exception:
        pass

    try:
        script = (
            "Add-Type -AssemblyName System.Speech; "
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            "$s.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name }"
        )
        result = subprocess.run(
            ["powershell", "-Command", script],
            capture_output=True, text=True, timeout=8,
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except Exception:
        return []
