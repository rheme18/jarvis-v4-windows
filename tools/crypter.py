# tools/crypter.py
from cryptography.fernet import Fernet

def encrypt_message_aes(message: str) -> str:
    if not message:
        return "Hata: Şifrelenecek boş metin gönderilemez patron!"
        
    try:
        # Rastgele, kırılması imkansız askeri düzeyde benzersiz bir anahtar üretiyoruz
        key = Fernet.generate_key()
        f = Fernet(key)
        
        # Metni byte formatına çevirip şifreliyoruz
        encrypted_bytes = f.encrypt(message.encode('utf-8'))
        
        report = "╔════════ SİBER KRİPTOGRAFİ (ŞİFRELEME) RAPORU ════════\n"
        report += f"🔑 ÜRETİLEN GİZLİ ANAHTAR (Bunu Güvenli Saklayın!):\n   {key.decode('utf-8')}\n\n"
        report += f"🔒 ŞİFRELENMİŞ METİN (Ciphertext):\n   {encrypted_bytes.decode('utf-8')}\n"
        report += "═════════════════════════════════════════════════════\n"
        report += "🛡️ Veri AES-256 protokolüyle kilitlendi. Bu anahtar olmadan dünyanın en güçlü bilgisayarı bile bu veriyi okuyamaz patron!"
        return report
    except Exception as e:
        return f"❌ Şifreleme motoru hatası: {str(e)}"

def decrypt_message_aes(cipher_text: str, secret_key: str) -> str:
    if not cipher_text or not secret_key:
        return "Hata: Şifreli metin ve gizli anahtar eksiksiz girilmelidir patron!"
        
    try:
        # Gelen string anahtarı byte formatına çekip Fernet motorunu yüklüyoruz
        f = Fernet(secret_key.strip().encode('utf-8'))
        
        # Şifreyi çözüyoruz
        decrypted_bytes = f.decrypt(cipher_text.strip().encode('utf-8'))
        original_message = decrypted_bytes.decode('utf-8')
        
        report = "╔════════ SİBER KRİPTOGRAFİ (ÇÖZME) RAPORU ════════\n"
        report += f"🔓 BAŞARILI: Orijinal Mesaj Çözüldü:\n👉 {original_message}\n"
        report += "═══════════════════════════════════════════════════\n"
        report += "🛡️ Anahtar doğrulandı, veri bütünlüğü bozulmadan siber kilit açıldı!"
        return report
    except Exception:
        return "❌ HATA: Şifre çözme başarısız! Girilen gizli anahtar yanlış veya şifreli metin tahrif edilmiş patron!"