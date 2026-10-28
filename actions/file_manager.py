import os
from pathlib import Path

# JARVIS'in güvenle çalışabileceği klasörler
ALLOWED_ROOTS = [
    Path.home() / "Desktop",
    Path.home() / "Documents"
]

def _is_path_safe(target_path: Path) -> bool:
    try:
        resolved_target = target_path.resolve()
        for root in ALLOWED_ROOTS:
            resolved_root = root.resolve()
            if resolved_target == resolved_root:
                return True
            try:
                resolved_target.relative_to(resolved_root)
                return True
            except ValueError:
                continue
        return False
    except Exception:
        return False

def manage_file(action: str, filename: str, content: str = "", new_filename: str = "", confirm: bool = False) -> str:
    """
    Masaüstü veya Belgelerim klasöründeki dosyaları yönetir, arar ve düzenler.
    """
    confirm = bool(confirm)

    # ── ARAMA MODÜLÜ ────────────────────────────────────────────────────────
    if action == "search":
        if not filename:
            return "❌ Hata: Ne arayacağımı belirtmediniz patron."
        
        found_files = []
        for root_dir in ALLOWED_ROOTS:
            if not root_dir.exists():
                continue
            for current_root, dirs, files in os.walk(root_dir):
                for f in files:
                    if filename.lower() in f.lower():
                        found_files.append(os.path.join(current_root, f))
                for d in dirs:
                    if filename.lower() in d.lower():
                        found_files.append(os.path.join(current_root, d))
                        
        if not found_files:
            return f"🔍 Klasörlerde '{filename}' ile eşleşen hiçbir dosya veya klasör bulamadım patron."
        
        report = f"🔍 '{filename}' için bulduğum sonuçlar:\n"
        for i, path in enumerate(found_files[:10], 1):
            report += f"{i}. {Path(path).name} ({Path(path).parent.name})\n"
        if len(found_files) > 10:
            report += f"...ve {len(found_files)-10} tane daha dosya var patron."
        return report

    # ── STANDART DOSYA İŞLEMLERİ ────────────────────────────────────────────
    # Varsayılan konum Masaüstü
    target_root = ALLOWED_ROOTS[0]
    file_path = target_root / filename

    if not _is_path_safe(file_path):
        return "🛡️ GÜVENLİK ENGELİ: Bu dosya konumuna erişim yetkim yok patron. Sadece Masaüstü ve Belgeler klasöründe çalışabilirim."

    try:
        # A) DOSYA YAZMA / GÜNCELLEME
        if action == "write":
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"📝 '{filename}' dosyası başarıyla oluşturuldu ve içerik yazıldı patron."

        # B) DOSYA OKUMA
        elif action == "read":
            if not file_path.exists() or not file_path.is_file():
                return f"❌ Hata: '{filename}' adında bir dosya bulamadım patron."
            with open(file_path, "r", encoding="utf-8") as f:
                data = f.read()
            return f"📖 '{filename}' dosyasının içeriği şöyle:\n\n{data}"

        # C) DOSYA / KLASÖR SİLME (Güvenlik Korumalı)
        elif action == "delete":
            if not file_path.exists():
                return f"❌ Hata: Silmek istediğin '{filename}' zaten mevcut değil patron."

            if not confirm:
                type_str = "KLASÖRÜNÜ VE İÇİNDEKİ TÜM DOSYALARI" if file_path.is_dir() else "dosyasını"
                return f"🛡️ GÜVENLİK ONAYI GEREKLİ: '{filename}' {type_str} silmek istediğinden emin misin patron? Eğer eminsen onay ver."

            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                import shutil
                shutil.rmtree(file_path)
            return f"🗑️ İşlem Tamam: '{filename}' başarıyla ve kalıcı olarak sistemden silindi patron."

        # D) YENİ KLASÖR OLUŞTURMA
        elif action == "create_dir":
            file_path.mkdir(parents=True, exist_ok=True)
            return f"📁 '{filename}' klasör yapısı başarıyla oluşturuldu."

        # E) LİSTELEME
        elif action == "list_dir":
            target_dir = Path.home() / "Desktop" if not filename else file_path
            if not target_dir.exists() or not target_dir.is_dir():
                return f"❌ Hata: '{filename}' geçerli bir klasör değil."
            
            items = os.listdir(target_dir)
            if not items:
                return f"📁 '{filename or 'Masaüstü'}' klasörü içi tamamen boş."
            return f"🗂️ Klasör İçeriği:\n" + "\n".join([f"- {item}" for item in items[:20]])

    except Exception as e:
        return f"❌ Dosya işlemi sırasında bir hata oluştu patron: {str(e)}"
