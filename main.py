#!/usr/bin/env python3
"""
J.A.R.V.I.S V4 Windows — Gercek zamanli sesli yardimci cekirdegi
Windows ortamina uyarlanmis calisma akisi
macOS surumunden tam ozellik paritesiyle portlanmistir.
"""

import asyncio
import datetime
import threading
import traceback
import os
import time
import re
from pathlib import Path

import pyaudio  # type: ignore[reportMissingModuleSource]
from google import genai  # type: ignore[reportMissingImports]
from google.genai import types  # type: ignore[reportMissingImports]

from app_config import get_app_config_value
from ui import JarvisUI
from memory.memory_manager import load_memory, update_memory, delete_memory, format_memory_for_prompt
from actions.open_app import open_app
from actions.sys_info  import sys_info
from actions.calendar import get_calendar_events, add_calendar_event, delete_calendar_event
from actions.reminders import get_reminders, add_reminder
from actions.browser   import browser_control
from actions.shell     import shell_run
from actions.whatsapp  import send_whatsapp_message, save_whatsapp_contact
from actions.media     import play_media
from actions.weather   import get_weather_summary
from actions.screen_vision import analyze_screen
from actions.youtube_stats import get_youtube_channel_report
from core.context_engine import DynamicContextManager, load_base_prompt
from core.tool_orchestrator import ToolContext, ToolOrchestrator

try:
    from wakeup_listener import WakeGestureListener
except Exception:  # pyaudio yoksa veya mikrofon erisimi yoksa uygulama yine acilsin
    WakeGestureListener = None

# ── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR        = Path(__file__).resolve().parent
PROMPT_PATH     = BASE_DIR / "core" / "prompt.txt"


# ── WebcamStreamer ──────────────────────────────────────────────────────────
class WebcamStreamer:
    """
    Webcam'dan sürekli kare çeker ve en güncel JPEG'i bellekte tutar.
    Queue yerine tek bir 'latest frame' yaklaşımı — eski kare birikimi olmaz.
    """

    JPEG_QUALITY = 72
    MAX_DIM      = 640
    WARMUP       = 2

    def __init__(self):
        self._latest: bytes | None = None
        self._lock   = threading.Lock()
        self._active = False
        self._thread: threading.Thread | None = None
        self._last_error = ""

    @property
    def is_active(self) -> bool:
        return self._active

    def get_latest_frame(self) -> bytes | None:
        """Thread-safe, her zaman en güncel kareyi döner."""
        with self._lock:
            return self._latest

    def consume_error(self) -> str:
        with self._lock:
            error = self._last_error
            self._last_error = ""
            return error

    def start(self) -> str:
        with self._lock:
            if self._active:
                return "already_active"
            self._active = True
            self._latest = None
            self._last_error = ""
        t = threading.Thread(target=self._run, daemon=True)
        self._thread = t
        t.start()
        return "ok"

    def stop(self):
        with self._lock:
            self._active = False
            self._latest = None

    def _run(self):
        try:
            import cv2
        except ImportError:
            print("[Webcam] opencv-python yüklü değil.")
            with self._lock:
                self._active = False
                self._last_error = "opencv-python yuklu degil."
            return

        backend = getattr(cv2, "CAP_DSHOW", 0) if os.name == "nt" else 0
        cap = cv2.VideoCapture(0, backend) if backend else cv2.VideoCapture(0)
        try:
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
            cap.set(cv2.CAP_PROP_FPS, 30)
        except Exception:
            pass
        if not cap.isOpened():
            print("[Webcam] Kamera açılamadı.")
            with self._lock:
                self._active = False
                self._last_error = "Kamera acilamadi. Windows kamera iznini veya baska uygulama kullanimini kontrol et."
            return

        # Isınma — sensörün otomatik pozlaması oturuncaya kadar bekle
        first_frame = None
        for _ in range(self.WARMUP):
            ok, frame = cap.read()
            if ok:
                first_frame = frame

        enc_params = [cv2.IMWRITE_JPEG_QUALITY, self.JPEG_QUALITY]

        try:
            while True:
                with self._lock:
                    if not self._active:
                        break

                if first_frame is not None:
                    ret, frame = True, first_frame
                    first_frame = None
                else:
                    ret, frame = cap.read()
                if not ret:
                    with self._lock:
                        self._last_error = "Webcam'dan goruntu alinamadi."
                    break

                h, w = frame.shape[:2]
                if max(h, w) > self.MAX_DIM:
                    s = self.MAX_DIM / max(h, w)
                    frame = cv2.resize(frame, (int(w * s), int(h * s)))

                frame = cv2.flip(frame, 1)  # yatay ayna — hem UI hem AI tutarlı
                ok, buf = cv2.imencode(".jpg", frame, enc_params)
                if ok:
                    with self._lock:
                        self._latest = buf.tobytes()

                # ~33 FPS yakala → 24 FPS UI her zaman taze kare bulur
                time.sleep(0.03)
        finally:
            cap.release()
            with self._lock:
                self._active = False
                self._latest = None
            print("[Webcam] Kamera serbest bırakıldı.")


CONTROL_TOKEN_RE = re.compile(r"<ctrl\d+>", re.IGNORECASE)

# ── Model ───────────────────────────────────────────────────────────────────
import json

def get_live_model() -> str:
    """models.json dosyasından canlı model adını okur, yoksa varsayılanı döner."""
    config_path = BASE_DIR / "config" / "models.json"
    default_model = "models/gemini-2.5-flash-native-audio-latest"
    
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("live_model", default_model)
        except Exception as e:
            print(f"[JARVIS] Config okunurken hata oluştu: {e}")
            return default_model
    return default_model

LIVE_MODEL = get_live_model()

# ── Audio ───────────────────────────────────────────────────────────────────
FORMAT           = pyaudio.paInt16
CHANNELS         = 1
SEND_SAMPLE_RATE = 16000
RECV_SAMPLE_RATE = 24000
CHUNK_SIZE       = 1024
pya              = pyaudio.PyAudio()

# ── Tool tanımları — paylaşılan modülden ────────────────────────────────────
from tool_defs import PLUGIN_LOAD_ERRORS, PLUGIN_REGISTRY, TOOL_DECLARATIONS


def get_api_key() -> str:
    return str(get_app_config_value("gemini_api_key", "") or "")


def load_system_prompt() -> str:
    try:
        return load_base_prompt(PROMPT_PATH)
    except Exception:
        return (
            "Sen JARVIS'sin — Windows'ta çalışan kişisel AI asistanı. "
            "Türkçe konuş. Kısa ve net yanıtlar ver. "
            "Araçları kullanarak görevleri tamamla, asla taklit etme."
        )


class JarvisLive:
    def __init__(self, ui: JarvisUI):
        self.ui             = ui
        self.session        = None
        self.audio_in_queue = None
        self.out_queue      = None
        self._loop          = None
        self._is_speaking   = False
        self._speaking_lock = threading.Lock()
        self._last_speaking_time = 0.0
        self._music_proc    = None
        self._webcam_streamer = WebcamStreamer()
        self._context_manager = DynamicContextManager(BASE_DIR)
        self._tool_orchestrator = ToolOrchestrator(PLUGIN_REGISTRY)
        self._last_user_text = ""
        self._mic_noise_threshold = 420  # Noise gate threshold to prevent background hiss/fan tripping barge-in

        self.ui.on_text_command  = self._on_text_command
        self.ui.on_pause_toggle  = self._on_pause_toggle
        self.ui.on_effects_state_change = self._on_effects_state_change
        self.ui.on_webcam_toggle = self._on_webcam_toggle_ui
        self._paused             = False
        if PLUGIN_LOAD_ERRORS:
            print(f"[JARVIS-PLUGINS] {len(PLUGIN_LOAD_ERRORS)} plugin uyarisi var.")

        # Proaktif Zeka Motorunu Başlat
        try:
            from core.proactive_engine import get_proactive_engine
            self._proactive_engine = get_proactive_engine(ui=self.ui)
            self._proactive_engine.start()
        except Exception as pe_err:
            print(f"[JARVIS] Proaktif motor başlatma hatası: {pe_err}")

    def _on_pause_toggle(self, paused: bool):
        self._paused = paused
        if paused:
            self._stop_music()

    def _on_effects_state_change(self, enabled: bool):
        if not enabled:
            self._stop_music()

    def _on_webcam_toggle_ui(self, activate: bool):
        if activate:
            status = self._webcam_streamer.start()
            self.ui.set_webcam_active(status == "ok" or status == "already_active")
        else:
            self._webcam_streamer.stop()
            self.ui.set_webcam_active(False)

    def _focus_ui_section_for_tool(self, tool_name: str, args: dict):
        if tool_name == "sys_info":
            query = str(args.get("query", "")).strip().lower()
            if query in {"time", "saat", "zaman", "date", "tarih"}:
                self.ui.focus_panel("time", duration_ms=5200)
            else:
                self.ui.focus_panel("system", duration_ms=5200)
        elif tool_name == "get_weather":
            self.ui.focus_panel("weather", duration_ms=5600)

    def _on_text_command(self, text: str):
        if self._paused:
            return

        self._last_user_text = text
        self.ui.write_log(f"Siz: {text}")

        if not self._loop or not self.session:
            self.ui.write_log(
                "ERR: JARVIS bağlantısı koptu veya henüz aktif değil! "
                "Sunucu ayarlarını/API key'i kontrol et."
            )
            self.ui.set_state("ERROR")
            return

        outbound_text = self._decorate_text_command(text)

        try:
            future = asyncio.run_coroutine_threadsafe(
                self.session.send_realtime_input(
                    text=outbound_text
                ),
                self._loop
            )

            def _chat_done(f):
                try:
                    f.result()
                    print("[JARVIS] ✅ Chat mesajı Gemini'ye gönderildi.")
                    self.ui.write_debug(
                        "Chat mesajı Live API'ye gönderildi.",
                        level="INFO"
                    )
                except Exception as e:
                    print(f"[JARVIS] ❌ Chat gönderim hatası: {e}")
                    traceback.print_exc()
                    self.ui.write_log(
                        f"ERR: Chat gönderilemedi — {e}"
                    )
                    self.ui.set_state("ERROR")

            future.add_done_callback(_chat_done)

        except Exception as e:
            print(f"[JARVIS] ❌ Text komut gönderilemedi: {e}")
            self.ui.write_log(
                f"ERR: Mesaj gönderilemedi - {e}"
            )
            self.ui.set_state("ERROR")

    def _decorate_text_command(self, text: str) -> str:
        try:
            from core.claude_plugin_adapter import format_plugin_context
            from core.skill_library import format_skill_context
            from memory.vector_memory import get_relevant_memory_context
            from core.user_profiler import get_user_profiler

            # Kullanıcı cümlesinden tercih/bilgi öğrenme
            profiler = get_user_profiler()
            profiler.analyze_user_text(text)
            facts_summary = profiler.get_facts_summary(limit=5)

            parts = [
                "[JARVIS_RUNTIME_CONTEXT]",
                self._context_manager.system_snapshot(),
            ]
            if facts_summary:
                parts.append(facts_summary)

            # RAG Semantik Hafıza Enjeksiyonu
            mem_context = get_relevant_memory_context(text, limit=3)
            if mem_context:
                parts.append(mem_context)

            skill_context = format_skill_context(text, limit=4)
            if skill_context:
                parts.append(skill_context)
            plugin_context = format_plugin_context(text, limit=4)
            if plugin_context:
                parts.append(plugin_context)
            parts.append("[END_RUNTIME_CONTEXT]")
            parts.append("[USER_TEXT]\n" + text)
            return "\n\n".join(parts)
        except Exception:
            return text


    async def process_message(self, text: str):
        if self._paused:
            return

        self._last_user_text = text

        if not self.session:
            if self.ui:
                self.ui.write_log(
                    "ERR: JARVIS bağlantısı henüz hazır değil."
                )
            return

        await self.session.send_realtime_input(
            text=self._decorate_text_command(text)
        )

    async def _interrupt_audio(self):
        try:
            if self.audio_in_queue:
                while not self.audio_in_queue.empty():
                    try:
                        self.audio_in_queue.get_nowait()
                    except Exception:
                        break
            if self.session:
                await self.session.send_realtime_input(audio_stream_end=True)
            self.set_speaking(False)
        except Exception:
            pass

    def _stop_music(self):
        proc = self._music_proc
        if proc and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass
        self._music_proc = None

    def set_speaking(self, value: bool):
        with self._speaking_lock:
            self._is_speaking = value
            if value:
                self._last_speaking_time = time.time()
            else:
                # Hoparlör sustuktan sonra odadaki yankının mikrofona sızıp
                # Gemini'yi yanıltmaması için 400ms hangover payı bırakıyoruz
                self._last_speaking_time = time.time()
        if value:
            self.ui.set_state("SPEAKING")
        else:
            self.ui.set_state("LISTENING")

    @staticmethod
    def _calculate_audio_rms(data: bytes) -> float:
        """PCM 16-bit ses verisinin RMS (enerji) seviyesini hesaplar."""
        if not data or len(data) < 2:
            return 0.0
        try:
            import audioop
            return float(audioop.rms(data, 2))
        except Exception:
            # Python 3.13+ veya audioop yoksa saf Python alternatifi
            count = len(data) // 2
            if count == 0:
                return 0.0
            import struct
            shorts = struct.unpack(f"<{count}h", data[:count * 2])
            sum_sq = sum(s * s for s in shorts)
            return (sum_sq / count) ** 0.5

    def speak_error(self, tool_name: str, error: str):
        short = str(error)[:120]
        self.ui.write_log(f"ERR: {tool_name} — {short}")
        self.ui.write_debug(f"{tool_name}: {short}", level="ERROR")
        self.ui.set_state("ERROR")

    @staticmethod
    def _result_looks_like_error(result) -> bool:
        text = str(result or "").strip().lower()
        if not text:
            return False
        error_markers = (
            "hata",
            "error",
            "alinamadi",
            "alınamadı",
            "bulunamadi",
            "bulunamadı",
            "acilamadi",
            "açılamadı",
            "tamamlanamadi",
            "tamamlanamadı",
            "gecersiz",
            "geçersiz",
            "izin gerekiyor",
            "izin gerekli",
            "baglanti",
            "bağlantı",
            "gerekli.",
        )
        return any(marker in text for marker in error_markers)

    @staticmethod
    def _should_play_success_sfx(tool_name: str, args: dict, result) -> bool:
        action_tools = {
            "open_app",
            "add_calendar_event",
            "add_reminder",
            "delete_calendar_event",
            "remove_calendar_event",
        }
        if tool_name in action_tools:
            return True

        if tool_name == "send_whatsapp_message":
            text = str(result or "").lower()
            if bool(args.get("send_now", False)):
                return "gönderildi" in text or "gonderildi" in text
            return False

        return False

    @staticmethod
    def _clean_transcript_text(text: str) -> tuple[str, bool]:
        raw = str(text or "")
        had_noise = False
        if CONTROL_TOKEN_RE.search(raw):
            had_noise = True
            raw = CONTROL_TOKEN_RE.sub(" ", raw)
        cleaned = []
        for ch in raw:
            if ch in "\n\r\t" or ord(ch) >= 32:
                cleaned.append(ch)
            else:
                had_noise = True
        normalized = " ".join("".join(cleaned).split())
        return normalized.strip(), had_noise

    @staticmethod
    def _merge_streaming_transcript(current: str, new_text: str) -> str:
        current = " ".join(str(current or "").split())
        new_text = " ".join(str(new_text or "").split())
        if not new_text:
            return current
        if not current:
            return new_text

        cur_cf = current.casefold()
        new_cf = new_text.casefold()
        if new_cf == cur_cf or new_cf in cur_cf:
            return current
        if new_cf.startswith(cur_cf):
            return new_text
        if cur_cf.endswith(new_cf):
            return current

        max_overlap = min(len(current), len(new_text))
        for size in range(max_overlap, 3, -1):
            if cur_cf[-size:] == new_cf[:size]:
                return (current + new_text[size:]).strip()
        return f"{current} {new_text}".strip()

    def _build_config(self) -> types.LiveConnectConfig:
        import datetime
        memory  = load_memory()
        mem_str = format_memory_for_prompt(memory)
        sys_p   = load_system_prompt()
        dynamic_instruction = self._context_manager.build(
            base_prompt=sys_p,
            memory_prompt=mem_str,
            tool_names=[tool.get("name", "") for tool in TOOL_DECLARATIONS],
            user_hint=self._last_user_text,
        )
        now     = datetime.datetime.now()
        time_ctx = f"[ŞU ANKİ ZAMAN]\n{now.strftime('%A, %d %B %Y — %H:%M')}\n\n"

        parts = [time_ctx]
        if mem_str:
            parts.append(mem_str + "\n\n")
        parts.append(sys_p)

        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            output_audio_transcription={},
            input_audio_transcription={},
            system_instruction=dynamic_instruction,
            tools=[{"function_declarations": TOOL_DECLARATIONS}],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=str(get_app_config_value("voice", "Charon") or "Charon")
                    )
                )
            ),
        )

    async def _execute_tool(self, fc) -> types.FunctionResponse:
        name = fc.name
        args = dict(fc.args or {})
        print(f"[JARVIS] 🔧 {name} {args}")
        self.ui.set_state("THINKING")
        ctx = ToolContext(
            base_dir=BASE_DIR,
            ui=self.ui,
            webcam_streamer=self._webcam_streamer,
            get_api_key=get_api_key,
            focus_tool=self._focus_ui_section_for_tool,
        )
        execution = await self._tool_orchestrator.execute(name, args, ctx)
        tool_failed = execution.status == "error"
        if tool_failed:
            self.ui.set_state("ERROR")
        elif self._should_play_success_sfx(name, args, execution.result):
            self.ui.play_success_sfx()

        if not tool_failed and not self.ui.muted:
            self.ui.set_state("LISTENING")

        print(f"[JARVIS] {name} -> {execution.result[:120]}")
        return types.FunctionResponse(
            id=fc.id,
            name=name,
            response={"result": execution.result},
        )



    async def _send_realtime(self):
        while True:
            try:
                msg = await self.out_queue.get()
                if self.session:
                    await self.session.send_realtime_input(media=msg)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                print(f"[JARVIS] ⚠️ Ses gönderim hatası: {e}")
                await asyncio.sleep(0.1)

    async def _stream_webcam_frames(self):
        """
        Webcam aktifken her 1.5s'de EN GÜNCEL kareyi session'a gönderir.
        Queue'suz 'latest frame' yaklaşımı: model hep şimdiki görüntüyü görür.
        """
        _last_sent: bytes | None = None
        while True:
            if not self._webcam_streamer.is_active:
                await asyncio.sleep(0.2)
                continue

            jpeg = self._webcam_streamer.get_latest_frame()
            if jpeg is None or jpeg is _last_sent:
                await asyncio.sleep(0.2)
                continue

            _last_sent = jpeg
            try:
                await self.session.send_realtime_input(
                    media={"data": jpeg, "mime_type": "image/jpeg"}
                )
            except Exception as e:
                print(f"[Webcam] Frame gönderilemedi: {e}")

            # 1.5 saniye bekle — model her zaman taze kare alır
            await asyncio.sleep(1.5)

    async def _update_ui_webcam_preview(self):
        """UI önizlemesini ~24 FPS günceller. AI akışından bağımsız."""
        frame_interval = 1.0 / 24.0   # ~0.0417 sn → 24 FPS
        while True:
            if self._webcam_streamer.is_active:
                jpeg = self._webcam_streamer.get_latest_frame()
                if jpeg:
                    self.ui.update_webcam_preview(jpeg)
            elif getattr(self.ui, "_webcam_active", False):
                error = self._webcam_streamer.consume_error()
                self.ui.set_webcam_active(False)
                if error:
                    self.ui.write_log(f"ERR: Webcam acilamadi: {error}")
            await asyncio.sleep(frame_interval)

    async def _listen_audio(self):
        """Mikrofon okuma görevi. Akıllı yankı ve gürültü filtresiyle korunur."""
        print("[JARVIS] 🎤 Mikrofon başlatılıyor...")
        stream = None
        try:
            stream = await asyncio.to_thread(
                pya.open,
                format=FORMAT, channels=CHANNELS,
                rate=SEND_SAMPLE_RATE, input=True,
                frames_per_buffer=CHUNK_SIZE,
            )
            print("[JARVIS] 🎤 Mikrofon başladı")
        except Exception as e:
            print(f"[JARVIS] ❌ Mikrofon başlatılamadı: {e}")
            self.ui.write_log("SYS: Mikrofon başlatılamadı! Ses girişi devre dışı. (Sadece yazışma aktif)")
            try:
                while True:
                    await asyncio.sleep(60)
            except asyncio.CancelledError:
                return

        consecutive_silence = 0
        try:
            while True:
                data = await asyncio.to_thread(
                    stream.read, CHUNK_SIZE, exception_on_overflow=False)
                
                now = time.time()
                with self._speaking_lock:
                    is_speaking = self._is_speaking
                    last_spoke = self._last_speaking_time

                # 1. Anti-Echo Koruması: Jarvis konuşurken veya ses bittikten sonraki 450ms'de
                # mikrofonu kesinlikle sustur (hoparlör sesi mikrofona girip konuşmayı bölmesin).
                if is_speaking or (now - last_spoke < 0.45):
                    continue

                if self.ui.muted or self._paused:
                    continue

                # 2. Akıllı Noise Gate: Fan sesi, klavye tıkırtısı ve nefes sesini filtrele
                rms = self._calculate_audio_rms(data)
                if rms < self._mic_noise_threshold:
                    consecutive_silence += 1
                    # Sürekli sessizlikte sunucuya yük bindirme
                    if consecutive_silence > 12:
                        continue
                else:
                    consecutive_silence = 0

                await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})
        except asyncio.CancelledError:
            pass  # TaskGroup iptal etti — normal çıkış
        except Exception as e:
            print(f"[JARVIS] ❌ Mikrofon okuma hatası: {e}")
            self.ui.write_log("SYS: Mikrofon bağlantısı koptu.")
            try:
                while True:
                    await asyncio.sleep(60)
            except asyncio.CancelledError:
                pass
        finally:
            if stream:
                try:
                    stream.close()
                except Exception:
                    pass

    async def _receive_audio(self):
        print("[JARVIS] 👂 Alım başladı")
        out_buf, in_buf = "", ""
        output_noise = False
        output_noise_samples = []
        try:
            while True:
                async for response in self.session.receive():
                    if response.data:
                        self.audio_in_queue.put_nowait(response.data)

                    if response.server_content:
                        sc = response.server_content

                        if sc.output_transcription and sc.output_transcription.text:
                            self.set_speaking(True)
                            raw_txt = sc.output_transcription.text.strip()
                            if raw_txt:
                                txt, had_noise = self._clean_transcript_text(raw_txt)
                                if had_noise:
                                    output_noise = True
                                    if len(output_noise_samples) < 4:
                                        output_noise_samples.append(raw_txt)
                                if txt:
                                    out_buf = self._merge_streaming_transcript(out_buf, txt)

                        if sc.input_transcription and sc.input_transcription.text:
                            txt = sc.input_transcription.text.strip()
                            if txt:
                                in_buf = self._merge_streaming_transcript(in_buf, txt)
                                self.ui.mark_user_activity(True)

                        if getattr(sc, "interrupted", False):
                            # Kullanıcı bilerek araya girdiğinde kuyruğu temizle
                            print("[JARVIS] ⚡ Kullanıcı araya girdi (Interrupted)")
                            while not self.audio_in_queue.empty():
                                try:
                                    self.audio_in_queue.get_nowait()
                                except Exception:
                                    break
                            self.set_speaking(False)

                        if sc.turn_complete:
                            # Sentinel: ses kuyrugundaki tum chunk'lar calindiktan
                            # sonra SPEAKING -> LISTENING gecisi yapilsin (yanki onlenir).
                            self.audio_in_queue.put_nowait(None)

                            full_in = in_buf.strip()
                            if full_in:
                                self.ui.write_log(f"Siz: {full_in}")
                            in_buf = ""

                            full_out = out_buf.strip()
                            if full_out:
                                self.ui.write_log(f"JARVIS: {full_out}")
                                if output_noise_samples:
                                    self.ui.write_debug(
                                        "Kısmen filtrelenen ses transcripti: " + " | ".join(output_noise_samples),
                                        level="WARN",
                                    )
                            elif output_noise:
                                self.ui.write_log("ERR: JARVIS sesli yanıtını çözümlerken bir hata oluştu.")
                                if output_noise_samples:
                                    self.ui.write_debug(
                                        "Filtrelenen ham transcript: " + " | ".join(output_noise_samples),
                                        level="WARN",
                                    )
                                self.ui.set_state("ERROR")
                            out_buf = ""
                            output_noise = False
                            output_noise_samples = []

                    if response.tool_call:
                        fn_responses = []
                        for fc in response.tool_call.function_calls:
                            print(f"[JARVIS] 📞 {fc.name}")
                            fr = await self._execute_tool(fc)
                            fn_responses.append(fr)
                        await self.session.send_tool_response(
                            function_responses=fn_responses)

        except Exception as e:
            print(f"[JARVIS] ❌ Alım: {e}")
            traceback.print_exc()
            raise

    async def _play_audio(self):
        """Ses çalma görevi. Buffer hatalarında çökmeyen, kendini yenileyen motor."""
        print("[JARVIS] 🔊 Ses çalma başlatılıyor...")
        stream = None

        def _open_out_stream():
            try:
                return pya.open(
                    format=FORMAT, channels=CHANNELS,
                    rate=RECV_SAMPLE_RATE, output=True,
                )
            except Exception as ex:
                print(f"[JARVIS] ❌ Hoparlör açma hatası: {ex}")
                return None

        stream = await asyncio.to_thread(_open_out_stream)
        if not stream:
            self.ui.write_log("SYS: Hoparlör başlatılamadı! Ses çıkışı devre dışı.")
            try:
                while True:
                    await self.audio_in_queue.get()
            except asyncio.CancelledError:
                pass
            return

        print("[JARVIS] 🔊 Ses çalma başladı")
        try:
            while True:
                chunk = await self.audio_in_queue.get()
                if chunk is None:
                    # turn_complete: Tüm kuyruk çalındı, dinleme durumuna dön
                    self.set_speaking(False)
                    continue

                self.set_speaking(True)
                try:
                    # Windows ses cihazlarında underflow hatasını sessizce tolere et
                    await asyncio.to_thread(stream.write, chunk, exception_on_underflow=False)
                except Exception as write_err:
                    print(f"[JARVIS] ⚠️ Ses tamponu uyarısı: {write_err}. Stream yeniden başlatılıyor...")
                    try:
                        stream.close()
                    except Exception:
                        pass
                    # Hemen yeniden aç ve devam et
                    stream = await asyncio.to_thread(_open_out_stream)
                    if stream:
                        try:
                            await asyncio.to_thread(stream.write, chunk, exception_on_underflow=False)
                        except Exception:
                            pass
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[JARVIS] ❌ Beklenmeyen ses çalma hatası: {e}")
        finally:
            self.set_speaking(False)
            if stream:
                try:
                    stream.close()
                except Exception:
                    pass

    async def run(self):
        connect_attempts = 0
        while True:
            # Duraklatılmışsa bağlanma, bekle
            if self._paused:
                await asyncio.sleep(1)
                continue

            try:
                # Client'ı her bağlanışta yeniden oluştur ve anahtarı tazeden oku.
                # Böylece yeni girilen API anahtarı anında geçerli olur; ilk
                # deneme başarısız olsa bile otomatik tekrar (3sn) kendini onarır.
                client = genai.Client(
                    api_key=get_api_key(),
                    http_options={"api_version": "v1alpha"}
                )
                print("[JARVIS] 🔌 Bağlanıyor...")
                self.ui.set_state("THINKING")
                config = self._build_config()

                async with (
                    client.aio.live.connect(model=LIVE_MODEL, config=config) as session,
                    asyncio.TaskGroup() as tg,
                ):
                    self.session        = session
                    self._loop          = asyncio.get_event_loop()
                    self.audio_in_queue = asyncio.Queue()
                    self.out_queue      = asyncio.Queue(maxsize=10)

                    print("[JARVIS] ✅ Bağlandı.")
                    connect_attempts = 0          # başarılı bağlantı → sayaç sıfırla
                    self.ui.set_state("LISTENING")
                    self.ui.write_log("SYS: JARVIS hazır. Dinliyorum...")

                    tg.create_task(self._send_realtime())
                    tg.create_task(self._listen_audio())
                    tg.create_task(self._receive_audio())
                    tg.create_task(self._play_audio())
                    tg.create_task(self._stream_webcam_frames())
                    tg.create_task(self._update_ui_webcam_preview())

            except Exception as e:
                self.session        = None
                self._loop          = None
                print(f"[JARVIS] ⚠️ {e}")
                traceback.print_exc()
                self.set_speaking(False)
                # Webcam akışını durdur — yeni session'da yeniden başlayacak
                if self._webcam_streamer.is_active:
                    self._webcam_streamer.stop()
                    self.ui.set_webcam_active(False)

                connect_attempts += 1
                # İlk birkaç deneme sessiz: yeni girilen API anahtarı Google
                # tarafında saniyeler içinde aktifleşebilir. Kullanıcıya hemen
                # "hatalı anahtar" göstermeyip kısa aralıkla otomatik tekrar dene.
                if connect_attempts <= 3:
                    self.ui.set_state("INITIALISING")
                    print(f"[JARVIS] 🔄 Bağlanmayı tekrar deniyor ({connect_attempts}/3)...")
                    await asyncio.sleep(2)
                else:
                    self.ui.write_log(
                        f"ERR: JARVIS baglanamiyor — API anahtarini ve internet "
                        f"baglantisini kontrol et. ({e})"
                    )
                    self.ui.set_state("ERROR")
                    print("[JARVIS] 🔄 5 saniyede yeniden bağlanıyor...")
                    await asyncio.sleep(5)


def _load_runtime_environment_keys():
    try:
        for env_key, config_key in {
            "VERCEL_TOKEN": "VERCEL_TOKEN",
            "GITHUB_TOKEN": "GITHUB_TOKEN",
            "GEMINI_API_KEY": "gemini_api_key",
        }.items():
            value = os.getenv(env_key) or str(get_app_config_value(config_key, "") or "")
            if value:
                os.environ[env_key] = value
    except Exception as exc:
        print(f"[JARVIS] Environment key bootstrap hatasi: {exc}")


def _start_optional_services(ui: JarvisUI):
    try:
        from core.settings_store import load_settings

        settings = load_settings()
    except Exception:
        settings = {"integrations": {}}
    integrations = settings.get("integrations", {}) if isinstance(settings, dict) else {}

    if integrations.get("web_panel_enabled", True):
        try:
            from services.web_server import start_jarvis_web_server

            start_jarvis_web_server()
            ui.write_log("SYS: Web panel baslatildi: http://127.0.0.1:8000")
        except Exception as exc:
            print(f"[JARVIS] Web panel baslatilamadi: {exc}")

    if integrations.get("telegram_enabled", True):
        try:
            from services.telegram_bot import start_telegram_bot

            start_telegram_bot()
        except Exception as exc:
            print(f"[JARVIS] Telegram bot baslatilamadi: {exc}")


def _attach_service_core(jarvis: JarvisLive):
    try:
        import services.web_server as web_server

        web_server.jarvis_core_instance = jarvis
    except Exception:
        pass


def main():
    if os.environ.get("TERM_PROGRAM") == "vscode":
        print("[JARVIS] VS Code icinden baslatildi.")

    _load_runtime_environment_keys()
    ui = JarvisUI()
    _start_optional_services(ui)

    def runner():
        ui.wait_for_api_key()
        jarvis = JarvisLive(ui)
        _attach_service_core(jarvis)
        try:
            asyncio.run(jarvis.run())
        except KeyboardInterrupt:
            print("\n🔴 Kapatılıyor...")

    threading.Thread(target=runner, daemon=True).start()

    # Yerel 'Hey Jarvis' / 'Jarvis' sesli uyandırma dinleyicisi
    ENABLE_WAKE_WORD = True
    if ENABLE_WAKE_WORD and WakeGestureListener is not None:
        try:
            wake_listener = WakeGestureListener(on_wake=ui.wake_up)
            wake_listener.start()
        except Exception as exc:
            print(f"[Wake] Sesli uyandırma dinleyici başlatılamadı: {exc}")

    ui.root.mainloop()


if __name__ == "__main__":
    main()
