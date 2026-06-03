import telebot
import requests
import json
import logging
import os
import sqlite3
from dotenv import load_dotenv
from urllib.parse import quote
from groq import Groq
from datetime import datetime
from flask import Flask
from threading import Thread

# Loglama ayarları (Kara Kutu)
logging.basicConfig(filename='bot_log.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Çevresel değişkenleri yükle
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("NEW_MODEL_API_KEY") 

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# --- 1. VERİTABANI KISMI ---
def init_db():
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS searches
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT, search_query TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

# --- 2. YAPAY ZEKA VE GITHUB KISMI ---
def get_github_repos(search_term):
    safe_search_term = quote(search_term)
    url = f"https://api.github.com/search/repositories?q={safe_search_term}&sort=stars&order=desc"
    response = requests.get(url, timeout=10)
    response.raise_for_status() 
    data = response.json()
    top_5 = [{"İsim": item.get("name"), "Açıklama": item.get("description"), "Yıldız": item.get("stargazers_count"), "Link": item.get("html_url")} for item in data.get('items', [])[:5]]
    return top_5

def analyze_with_groq(repo_data):
    if not GROQ_API_KEY:
        raise ValueError("Groq API Key bulunamadı!")
    client = Groq(api_key=GROQ_API_KEY)
    json_string = json.dumps(repo_data, ensure_ascii=False)
    prompt = "Sen kıdemli bir teknoloji editörüsün. Sana verilen popüler GitHub projelerini incele ve kısa bir teknoloji trend bülteni yaz."
    response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"{prompt}\n\nProjeler:\n{json_string}"}])
    return response.choices[0].message.content

# --- 3. TELEGRAM MESAJ KISMI ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "🚀 Merhaba! Ben senin kişisel AI Trend asistanınım.\nHangi teknolojiyi araştırmak istersin?")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    try:
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
            kullanici = row[0] if row[0] else "Gizli_Kullanici"
            rapor_metni += f"👤 @{kullanici} ➡️ 🔍 {row[1]}\n🕒 {row[2]}\n➖➖➖➖➖➖\n"
        bot.reply_to(message, rapor_metni)
    except Exception as e:
        bot.reply_to(message, f"Rapor çekilirken hata: {e}")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    search_query = message.text
    if not search_query.strip():
        bot.reply_to(message, "Lütfen bir arama kelimesi girin!")
        return
    
    waiting_message = bot.reply_to(message, "⏳ GitHub derinliklerine iniliyor ve AI analizi yapılıyor. Lütfen bekle...")
    
    try:
        repos = get_github_repos(search_query)
        if not repos:
            bot.edit_message_text("Bu kelimeyle eşleşen proje bulunamadı.", chat_id=message.chat.id, message_id=waiting_message.message_id)
            return
        
        ai_report = analyze_with_groq(repos)
        
        try:
            bot.edit_message_text(f"📊 *Trend Raporu: {search_query}*\n\n{ai_report}", chat_id=message.chat.id, message_id=waiting_message.message_id, parse_mode="Markdown")
        except:
            bot.edit_message_text(f"📊 Trend Raporu: {search_query}\n\n{ai_report}", chat_id=message.chat.id, message_id=waiting_message.message_id)
        
        conn = sqlite3.connect('bot_database.db')
        c = conn.cursor()
        c.execute("INSERT INTO searches (user_id, username, search_query, timestamp) VALUES (?, ?, ?, ?)", (message.from_user.id, message.from_user.username, search_query, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
    except Exception as e:
        bot.edit_message_text("Beklenmeyen bir sorun oluştu.", chat_id=message.chat.id, message_id=waiting_message.message_id)

# --- 4. BULUT İÇİN SAHTE WEB SUNUCUSU (HACK) ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot Bulutta 7/24 Çalışıyor!"

def run_web_server():
    # Render'ın verdiği portu kullanır, yoksa 8080'i dener
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    init_db()
    
    # Web sunucusunu arka planda (ayrı bir thread) başlat
    server_thread = Thread(target=run_web_server)
    server_thread.start()
    
    # Botu başlat
    print("🤖 Bot başarıyla çalıştırıldı! Telegram'dan mesaj atabilirsin.")
    bot.infinity_polling()