import telebot
import requests
import json
import logging
import os
from dotenv import load_dotenv
from urllib.parse import quote
from groq import Groq  # Groq kütüphanesini eklemeyi unutmuştu, biz ekledik!

# Loglama ayarları (Kara Kutu)
logging.basicConfig(
    filename='bot_log.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Çevresel değişkenleri yükle
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
# İŞTE BURAYI DÜZELTTİK: Senin .env dosyasındaki anahtar ismini yazdık
GROQ_API_KEY = os.getenv("NEW_MODEL_API_KEY") 

# Bot'u başlatalım
bot = telebot.TeleBot(TELEGRAM_TOKEN)

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
        
        # 3. Sonucu kullanıcıya Telegram'dan gönder
        bot.edit_message_text(f"📊 **Trend Raporu: {search_query}**\n\n{ai_report}", chat_id=message.chat.id, message_id=waiting_message.message_id, parse_mode="Markdown")
        
        logging.info(f"Başarılı bot araması: {search_query}")
        
    except Exception as e:
        logging.error(f"Bot işlemi sırasında hata: {e}", exc_info=True)
        bot.edit_message_text("Beklenmeyen bir sorun oluştu. Detaylar log dosyasına yazıldı.", chat_id=message.chat.id, message_id=waiting_message.message_id)

# Botu sürekli dinlemede tut
print("🤖 Bot başarıyla çalıştırıldı! Telegram'dan mesaj atabilirsin.")
bot.infinity_polling()