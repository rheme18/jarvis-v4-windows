import os
import shutil
from pathlib import Path
from google import genai

BASE_DIR = Path(__file__).resolve().parent.parent

def _is_git_available() -> bool:
    """Sistemde git çalıştırılabilir dosyasının varlığını kontrol eder."""
    return bool(shutil.which("git"))

def _get_repo():
    """GitPython Repo nesnesini güvenli şekilde yükler."""
    if not _is_git_available():
        raise RuntimeError("Sistemde Git bulunamadı. Lütfen Git'i kurun veya PATH ortam değişkenine ekleyin.")
    try:
        from git import Repo
        if not os.path.exists(BASE_DIR / ".git"):
            return Repo.init(BASE_DIR)
        return Repo(BASE_DIR)
    except Exception as exc:
        raise RuntimeError(f"Git deposu açılamadı: {exc}")

def _get_gemini_client():
    """AI Studio client'ını başlatır."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        try:
            from app_config import get_app_config_value
            api_key = str(get_app_config_value("gemini_api_key", "") or "")
        except Exception:
            pass
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

def _generate_smart_commit_message(diff_text: str) -> str:
    """Gemini kullanarak değişikliklerden anlamlı bir commit mesajı üretir."""
    client = _get_gemini_client()
    if not client or not diff_text.strip():
        return "chore: automatic update via JARVIS"
    
    prompt = (
        f"Aşağıdaki git diff çıktısını analiz et ve 'Conventional Commits' "
        f"standartlarına uygun (feat:, fix:, chore:, docs:, refactor:) kısa, net ve "
        f"profesyonel bir Türkçe commit mesajı yaz. Sadece mesajı döndür, başka açıklama yazma:\n\n{diff_text[:3000]}"
    )
    try:
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip().replace('"', '')
    except Exception:
        return "chore: automatic update via JARVIS"

def _security_scan(diff_text: str) -> tuple[bool, str]:
    """Kodda gizli anahtar veya hassas dosya sızıntısı var mı kontrol eder."""
    danger_keywords = ["client_secret", "gocspx", "api_key", "password", "private_key", "secret_key"]
    diff_lower = diff_text.lower()
    
    for kw in danger_keywords:
        if kw in diff_lower:
            return False, f"Kritik güvenlik riski! Kodda '{kw}' ifadesi tespit edildi. Push engellendi."
            
    # Hassas dosya isimleri kontrolü
    for unsafe_file in ["credentials.json", "token.json", "jarvis_google_token.json", ".env", "api_keys.json", "memory.json"]:
        if unsafe_file in diff_text:
            return False, f"Hassas dosya ({unsafe_file}) değişikliklere dahil edilmiş! Güvenlik nedeniyle engellendi."
            
    return True, "Güvenli"

def jarvis_git_push(commit_msg: str = "auto") -> str:
    """Tüm değişiklikleri index'ler, güvenliği tarar, commit'ler ve push'lar."""
    try:
        repo = _get_repo()
            
        # 1. Değişiklikleri tara (Untracked ve Modified)
        untracked = repo.untracked_files
        changed = [item.a_path for item in repo.index.diff(None)]
        
        if not untracked and not changed and not (repo.head.is_valid() and repo.index.diff("HEAD")):
            return "Kodu inceledim Patron, pushlanacak hiçbir değişiklik yok. Tertemiz!"
            
        # Tümünü sahneye (staging area) ekle
        repo.git.add(A=True)
        
        # 2. Güvenlik Taraması İçin Diff Al
        diff_text = repo.git.diff("HEAD") if repo.head.is_valid() else ""
        is_safe, security_msg = _security_scan(diff_text)
        if not is_safe:
            repo.git.reset()
            return security_msg
            
        # 3. Akıllı Commit Mesajı Üretimi
        if commit_msg == "auto":
            final_msg = _generate_smart_commit_message(diff_text)
        else:
            final_msg = commit_msg
            
        # 4. Commit At
        repo.index.commit(final_msg)
        
        # 5. Remote ve Push Ayarları
        if not repo.remotes:
            return f"Commit başarıyla atıldı ('{final_msg}'). Ancak uzak sunucu (origin) tanımlı değil Patron. 'git remote add origin <url>' yapmalısın."
            
        origin = repo.remote(name="origin")
        current_branch = repo.active_branch.name
        
        # Push işlemi
        origin.push(refspec=f"{current_branch}:{current_branch}")
        return f"İşlem tamam Patron! Kodlar güvenle pushlandı.\nCommit Mesajı: {final_msg}\nBranch: {current_branch}"
        
    except Exception as e:
        return f"Git operasyonu sırasında bir hata meydana geldi Patron: {str(e)}"
