from __future__ import annotations


def window_snap(action: str, title: str = "") -> str:
    action = (action or "left").strip().lower()
    title = (title or "").strip()

    try:
        import pyautogui
    except Exception as exc:
        return f"Pencere duzeni icin pyautogui gerekli: {exc}"

    try:
        if title:
            try:
                from pywinauto import Desktop

                windows = Desktop(backend="uia").windows()
                for win in windows:
                    if title.lower() in (win.window_text() or "").lower():
                        win.set_focus()
                        break
            except Exception:
                pass

        mapping = {
            "left": ["win", "left"],
            "right": ["win", "right"],
            "up": ["win", "up"],
            "down": ["win", "down"],
            "maximize": ["win", "up"],
            "minimize": ["win", "down"],
            "desktop": ["win", "d"],
        }
        keys = mapping.get(action)
        if not keys:
            return "Desteklenen pencere eylemleri: left, right, up, down, maximize, minimize, desktop."
        pyautogui.hotkey(*keys)
        return f"Pencere duzeni uygulandi: {action}"
    except Exception as exc:
        return f"Pencere duzeni uygulanamadi: {exc}"
