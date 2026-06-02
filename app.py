import streamlit as st
import requests
import os
import json
import logging
import urllib.parse
from dotenv import load_dotenv
from groq import Groq

# 1. KARA KUTU (Loglama) AYARLARI
# Kullanıcı ekranda hata görmez, ama biz her şeyi bu dosyaya yazarız.
logging.basicConfig(
    filename='sistem_kayitlari.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_github_repos(search_term):
    """GitHub'dan en popüler 5 projeyi çeker"""
    # BUG ÇÖZÜMÜ: Kullanıcı "game development" yazarsa aradaki boşluğu URL'e uygun hale getir (%20 veya +)
    safe_search_term = urllib.parse.quote(search_term)
    url = f"https://api.github.com/search/repositories?q={safe_search_term}&sort=stars&order=desc"
    
    response = requests.get(url, timeout=10)
    response.raise_for_status() # Hata varsa (örn. 400, 404) direkt except bloğuna fırlatır
    data = response.json()
    
    # Sadece ilk 5 projenin önemli kısımlarını alıyoruz
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
    # .env dosyasından key'i al
    token = os.getenv("GROQ_API_KEY") or os.getenv("NEW_MODEL_API_KEY")
    if not token:
        raise ValueError("API Key bulunamadı! Lütfen .env dosyanı kontrol et.")
    
    # BUG ÇÖZÜMÜ: Groq'u başlatırken model adı yazılmaz, sadece api_key verilir.
    client = Groq(api_key=token)
    
    json_string = json.dumps(repo_data, ensure_ascii=False)
    prompt = "Sen kıdemli bir teknoloji editörüsün. Sana verilen en popüler 5 GitHub projesini incele ve yazılımcılar için ilgi çekici, kısa bir teknoloji trend bülteni yaz."
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": f"{prompt}\n\nProjeler:\n{json_string}"}]
    )
    return response.choices[0].message.content

def main():
    # Çevresel değişkenleri yükle
    load_dotenv()
    
    # ARAYÜZ (FRONTEND) KISMI
    st.set_page_config(page_title="GitHub AI Trendleri", page_icon="🚀")
    st.title("🚀 GitHub Trend Analizörü")
    st.markdown("İstediğin teknolojiyi yaz, en popüler 5 projeyi yapay zeka senin için özetlesin!")
    
    # Kullanıcıdan kelime al
    search_query = st.text_input("Hangi teknolojiyi araştıralım? (Örn: python, game development, machine learning)")
    
    # Butona basılınca çalışacak olaylar
    if st.button("Analiz Et"):
        if not search_query.strip():
            st.warning("Lütfen bir arama kelimesi girin!")
            return
            
        # Yükleme efekti
        with st.spinner(f"'{search_query}' için GitHub derinliklerine iniliyor ve AI analizi yapılıyor..."):
            try:
                # 1. Aşama: Veriyi Çek
                repos = get_github_repos(search_query)
                
                if not repos:
                    st.warning("Bu kelimeyle eşleşen popüler bir proje bulunamadı.")
                    return
                
                # 2. Aşama: Yapay Zekaya Yorumlat
                ai_report = analyze_with_groq(repos)
                
                # 3. Aşama: Ekrana Bas
                st.success("Analiz tamamlandı!")
                st.markdown("### 📊 AI Trend Raporu")
                st.write(ai_report)
                
                # Başarılı işlemi de logla
                logging.info(f"Başarılı analiz yapıldı: {search_query}")
                
            except Exception as e:
                # YAZILIMCI İÇİN: Gerçek hatayı tüm detaylarıyla (Traceback) log dosyasına kaydet
                logging.error(f"İstek sırasında bir hata oluştu: {e}", exc_info=True)
                
                # KULLANICI İÇİN: Ekranda sadece kibar bir mesaj göster
                st.error("Beklenmeyen bir sorun oluştu. Lütfen daha sonra tekrar deneyin veya teknik ekibe bildirin.")

if __name__ == "__main__":
    main()