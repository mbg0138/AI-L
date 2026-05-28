import requests
import os
from dotenv import load_dotenv

# .env dosyasının içindeki gizli kasayı açar
load_dotenv()

# Şifreyi okur ve ekrana yazar
token = os.getenv("GITHUB_TEST_TOKEN")
print(f"Kullanılan Token: {token}\n")

url = 'https://api.github.com'

try:
    # 10 saniye içinde cevap gelmezse Timeout hatası fırlatır
    response = requests.get(url, timeout=10)
    response.raise_for_status() 
    
    data = response.json()
    
    # Sadece ilk 5 anahtarı numaralandırarak yazdırır
    for i, key in enumerate(list(data.keys())[:5], 1):
        print(f"{i}. {key}")
        
except requests.exceptions.Timeout:
    print("Hata: GitHub cevap vermedi (Zaman Aşımı).")
except requests.exceptions.ConnectionError:
    print("Hata: İnternet bağlantınız koptu veya GitHub çöktü.")
except requests.exceptions.RequestException as e:
    print(f"Beklenmeyen bir hata oluştu: {e}")