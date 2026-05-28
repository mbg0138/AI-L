import requests
import os
import json
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
    
    # Verileri json dosyasına kaydeder
    with open('github_response.json', 'w') as file:
        json.dump(data, file, indent=4)

    print('Veriler başarıyla JSON dosyasına kaydedildi.')
except requests.exceptions.Timeout:
    print("Hata: GitHub cevap vermedi (Zaman Aşımı).")
except requests.exceptions.ConnectionError:
    print("Hata: İnternet bağlantınız koptu veya GitHub çöktü.")
except requests.exceptions.RequestException as e:
    print(f"Beklenmeyen bir hata oluştu: {e}")