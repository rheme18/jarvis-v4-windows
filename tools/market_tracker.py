# tools/market_tracker.py
import yfinance as yf

def track_stock_market_live() -> str:
    report = "╔════════ ANALİTİK BORSA VE PİYASA TAKİP RAPORU ════════\n"
    report += " 📊 --- DÖVİZ & EMTİA --- \n"
    
    # Küresel borsa sembolleri (Dolar, Euro, Altın, BIST100)
    currencies = {
        "USD/TRY (Dolar)": "USDTRY=X",
        "EUR/TRY (Euro)": "EURTRY=X",
        "BIST 100 (Borsa)": "XU100.IS",
        "Ons Altın (Gold)": "GC=F"
    }
    
    for name, ticker in currencies.items():
        try:
            # Anlık piyasa verisini yfinance ile sorguluyoruz
            data = yf.Ticker(ticker)
            todays_data = data.history(period='1d')
            
            if not todays_data.empty:
                # En son kapanış ve anlık fiyatı alıyoruz
                close_price = todays_data['Close'].iloc[-1]
                open_price = todays_data['Open'].iloc[-1]
                # Günlük değişim yüzdesi hesabı
                change_pct = ((close_price - open_price) / open_price) * 100
                
                direction = "🔺" if change_pct >= 0 else "🔻"
                
                # BIST 100 puan bazında olduğu için TRY ibaresini kaldırıyoruz
                if "Borsa" in name:
                    report += f" {direction} {name:<18} : {close_price:,.2f}        (Değişim: %{change_pct:+.2f})\n"
                else:
                    report += f" {direction} {name:<18} : {close_price:.4f} TRY    (Değişim: %{change_pct:+.2f})\n"
            else:
                report += f" ⚠️ {name:<18} : Veri akışı kesildi.\n"
        except:
            report += f" ❌ {name:<18} : Bağlantı Sağlanamadı.\n"
            
    report += "\n 📈 --- POPÜLER HİSSE SENETLERİ (BIST) --- \n"
    
    # Borsa İstanbul hisselerinin Yahoo üzerindeki tam kodları
    hisseler = {
        "THYAO (Türk Hava Yolları)": "THYAO.IS",
        "ASELS (Aselsan)": "ASELS.IS",
        "EREGL (Ereğli Demir Çelik)": "EREGL.IS"
    }
    
    for h_name, h_ticker in hisseler.items():
        try:
            stock = yf.Ticker(h_ticker)
            stock_data = stock.history(period='1d')
            
            if not stock_data.empty:
                c_price = stock_data['Close'].iloc[-1]
                o_price = stock_data['Open'].iloc[-1]
                s_change = ((c_price - o_price) / o_price) * 100
                
                direction = "🔺" if s_change >= 0 else "🔻"
                report += f" {direction} {h_name:<26} : {c_price:.2f} TRY     (% {s_change:+.2f})\n"
            else:
                report += f" ⚠️ {h_name:<26} : Veri çekilemedi.\n"
        except:
            report += f" ❌ {h_name:<26} : Hisse bulunamadı.\n"
            
    report += "═══════════════════════════════════════════════════════\n"
    report += "✅ Veriler küresel piyasadan (Yahoo) anlık çekildi. Sistem stabil."
    return report