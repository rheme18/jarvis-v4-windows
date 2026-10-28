from __future__ import annotations

from pathlib import Path


SENSITIVE_NAMES = {"powershell.exe", "cmd.exe", "wscript.exe", "cscript.exe", "rundll32.exe", "regsvr32.exe"}


def process_risk_scanner(limit: int = 20) -> str:
    try:
        import psutil
    except Exception as exc:
        return f"psutil yuklenemedi: {exc}"
    limit = max(5, min(int(limit or 20), 80))
    findings = []
    for proc in psutil.process_iter(["pid", "name", "exe", "cmdline"]):
        try:
            name = str(proc.info.get("name") or "").lower()
            exe = proc.info.get("exe") or ""
            cmdline = " ".join(proc.info.get("cmdline") or [])
            score = 0
            reasons = []
            if name in SENSITIVE_NAMES:
                score += 1
                reasons.append("komut/scripting sureci")
            if exe and not Path(exe).exists():
                score += 1
                reasons.append("exe yolu okunamiyor")
            low = (exe + " " + cmdline).lower()
            if "appdata\\local\\temp" in low or "\\temp\\" in low:
                score += 2
                reasons.append("temp konumundan calisiyor")
            if "-enc" in low or "encodedcommand" in low:
                score += 3
                reasons.append("encoded command izi")
            if score:
                findings.append((score, proc.info.get("pid"), proc.info.get("name"), reasons))
        except Exception:
            continue
    findings.sort(reverse=True, key=lambda item: item[0])
    if not findings:
        return "Surec risk taramasi: belirgin risk sinyali yok."
    lines = [f"Surec risk taramasi: {len(findings)} sinyal bulundu."]
    for score, pid, name, reasons in findings[:limit]:
        lines.append(f"- PID {pid} | {name} | risk {score} | {', '.join(reasons)}")
    return "\n".join(lines)
