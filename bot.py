import telebot
import requests
import json
import logging
import os
from dotenv import load_dotenv
from urllib.parse import quote
from groq import Groq
import sqlite3
from datetime import datetime
# Loglama ayarları (Kara Kutu)
logging.basicConfig(
    filename='bot_log.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Çevresel değişkenleri yükle
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("NEW_MODEL_API_KEY") 

# Bot'u başlatalım
bot = telebot.TeleBot(TELEGRAM_TOKEN)

def init_db():
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS searches
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT, search_query TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

def get_github_repos(search_term):
    """GitHub'dan en popüler 5 projeyi çeker"""
    safe_search_term = quote(search_term)
    url = f"https://api.github.com/search/repositories?q={safe_search_term}&sort=stars&order=desc"
    
    response = requests.get(url, timeout=10)
    response.raise_for_status() 
    data = response.json()
    
    top_5 = []
    for item in data.get('items', [])[:5]:
        top_5.append({
            "İsim": item.get("name"),
            "Açıklama": item.get("description"),
            "Yıldız": item.get("stargazers_count"),
            "Link": item.get("html_url")
        })
    return top_5

def analyze_with_groq(repo_data):
    """Çekilen projeleri Llama 3.3'e verip yorumlatır"""
    if not GROQ_API_KEY:
        raise ValueError("Groq API Key bulunamadı! Lütfen .env dosyanı kontrol et.")
    
    # İşte doğru Groq bağlantısı!
    client = Groq(api_key=GROQ_API_KEY)
    
    json_string = json.dumps(repo_data, ensure_ascii=False)
    prompt = "Sen kıdemli bir teknoloji editörüsün. Sana verilen en popüler 5 GitHub projesini incele ve yazılımcılar için ilgi çekici, kısa bir teknoloji trend bülteni yaz."
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": f"{prompt}\n\nProjeler:\n{json_string}"}]
    )
    return response.choices[0].message.content

# /start veya /help yazılınca çalışacak fonksiyon
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "🚀 Merhaba! Ben senin kişisel AI Trend asistanınım.\nHangi teknolojiyi araştırmak istersin? (Örn: python, react, game development)")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    try:
        # Veritabanına bağlanıp son 5 aramayı tersine sıralayarak çekiyoruz
        conn = sqlite3.connect('bot_database.db')
        c = conn.cursor()
        c.execute("SELECT username, search_query, timestamp FROM searches ORDER BY id DESC LIMIT 5")
        rows = c.fetchall()
        conn.close()

        if not rows:
            bot.reply_to(message, "Veritabanı şu an bomboş patron.")
            return

        rapor_metni = "👑 **PATRON RAPORU - SON 5 ARAMA** 👑\n\n"
        for row in rows:
            kullanici = row[0] if row[0] else "Gizli_Kullanici" # Kullanıcı adı yoksa gizli yazsın
            kelime = row[1]
            zaman = row[2]
            rapor_metni += f"👤 @{kullanici} ➡️ 🔍 {kelime}\n🕒 {zaman}\n➖➖➖➖➖➖\n"

        bot.reply_to(message, rapor_metni)

    except Exception as e:
        bot.reply_to(message, f"Rapor çekilirken hata oluştu: {e}")

# Normal bir mesaj (kelime) yazılınca çalışacak ana fonksiyon
@bot.message_handler(func=lambda message: True)
# Normal bir mesaj (kelime) yazılınca çalışacak ana fonksiyon
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    search_query = message.text
    
    if not search_query.strip():
        bot.reply_to(message, "Lütfen bir arama kelimesi girin!")
        return
    
    # Kullanıcıya bekleme mesajı at
    waiting_message = bot.reply_to(message, "⏳ GitHub derinliklerine iniliyor ve AI analizi yapılıyor. Lütfen bekle...")
    
    try:
        # 1. GitHub'dan veriyi çek
        repos = get_github_repos(search_query)
        if not repos:
            bot.edit_message_text("Bu kelimeyle eşleşen popüler bir proje bulunamadı.", chat_id=message.chat.id, message_id=waiting_message.message_id)
            return
        
        # 2. Veriyi Groq'a (Llama'ya) gönder ve analiz raporunu al
        ai_report = analyze_with_groq(repos)
        
        # 3. Sonucu kullanıcıya Telegram'dan gönder (B Planlı Sistem)
        try:
            # Önce havalı (Markdown) göndermeyi dene
            bot.edit_message_text(f"📊 *Trend Raporu: {search_query}*\n\n{ai_report}", chat_id=message.chat.id, message_id=waiting_message.message_id, parse_mode="Markdown")
        except:
            # Eğer Llama formatı bozduysa, B Planı: Düz metin olarak at
            bot.edit_message_text(f"📊 Trend Raporu: {search_query}\n\n{ai_report}", chat_id=message.chat.id, message_id=waiting_message.message_id)
        
        # 4. Veritabanına kaydet
        conn = sqlite3.connect('bot_database.db')
        c = conn.cursor()
        c.execute("INSERT INTO searches (user_id, username, search_query, timestamp) VALUES (?, ?, ?, ?)",
                  (message.from_user.id, message.from_user.username, search_query, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()

        logging.info(f"Başarılı bot araması: {search_query}")
        
    except Exception as e:
        logging.error(f"Bot işlemi sırasında hata: {e}", exc_info=True)
        bot.edit_message_text("Beklenmeyen bir sorun oluştu. Detaylar log dosyasına yazıldı.", chat_id=message.chat.id, message_id=waiting_message.message_id)
        
        # 2. Veriyi Groq'a (Llama'ya) gönder ve analiz raporunu al
        ai_report = analyze_with_groq(repos)
        
        # 3. Sonucu kullanıcıya Telegram'dan gönder
        bot.edit_message_text(f"📊 **Trend Raporu: {search_query}**\n\n{ai_report}", chat_id=message.chat.id, message_id=waiting_message.message_id, parse_mode="Markdown")
        
        # Veritabanına kaydet
        conn = sqlite3.connect('bot_database.db')
        c = conn.cursor()
        c.execute("INSERT INTO searches (user_id, username, search_query, timestamp) VALUES (?, ?, ?, ?)",
                  (message.from_user.id, message.from_user.username, search_query, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()

        logging.info(f"Başarılı bot araması: {search_query}")
        
    except Exception as e:
        logging.error(f"Bot işlemi sırasında hata: {e}", exc_info=True)
        bot.edit_message_text("Beklenmeyen bir sorun oluştu. Detaylar log dosyasına yazıldı.", chat_id=message.chat.id, message_id=waiting_message.message_id)

# Veritabanını initialize et
init_db()

# Botu sürekli dinlemede tut
print("🤖 Bot başarıyla çalıştırıldı! Telegram'dan mesaj atabilirsin.")
bot.infinity_polling()