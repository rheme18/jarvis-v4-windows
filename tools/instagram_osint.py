# tools/instagram_osint.py
import instaloader
import contextlib
import sys
import os

def get_instagram_profile_osint(username: str) -> str:
    try:
        @contextlib.contextmanager
        def Output():
            with open(os.devnull, 'w') as devnull:
                old_stdout, old_stderr = sys.stdout, sys.stderr
                sys.stdout, sys.stderr = devnull, devnull
                try: yield
                finally: sys.stdout, sys.stderr = old_stdout, old_stderr

        with Output():
            loader = instaloader.Instaloader()
            profile = instaloader.Profile.from_username(loader.context, username)
        
        report = [
            f"👤 [INSTAGRAM PROFİL RAPORU] — {username}",
            f" 🆔 ID              : {profile.profile_id}",
            f" 📝 Username        : {profile.username}",
            f" 📖 Name            : {profile.full_name or 'None'}",
            f" ✍️ Biography       : {profile.biography or 'None'}",
            f" 👥 Followers       : {profile.followers}",
            f" 📉 Subscriptions   : {profile.followees}",
            f" ✅ Verified        : {'True' if profile.is_verified else 'False'}",
            f" 🔒 Private Account : {'True' if profile.is_private else 'False'}",
            f" 💼 Pro Account     : {'True' if profile.is_business_account else 'False'}"
        ]
        
        if profile.is_business_account:
            report.append(f"    ↳ Category Pro    : {profile.business_category_name or 'None'}")
            
        # Orijinal son 5 post tarama döngüsü
        if not profile.is_private:
            report.append("\n📸 [GÖNDERİ ÖZETLERİ]")
            posts = profile.get_posts()
            for i, post in enumerate(posts):
                if i >= 5: break
                report.append(
                    f" 📌 Publication n°{i+1}\n"
                    f"  ↳ URL        : https://www.instagram.com/p/{post.shortcode}/\n"
                    f"  ↳ Date       : {post.date}\n"
                    f"  ↳ Likes      : {post.likes}\n"
                    f"  ↳ Comments   : {post.comments}\n"
                    f"  ↳ Legend     : {post.caption.strip() if post.caption else 'None'}\n"
                    f"────────────────────────────────────────"
                )
        return "\n".join(report)
    except Exception as e:
        return f"❌ Instagram siber analiz hatası: {str(e)}"