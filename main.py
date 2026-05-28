# src/main.py

import requests
import os
import json
from dotenv import load_dotenv
import logging

# Logger ayarları
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_environment_variables():
    """dotenv dosyasındaki değişkenleri yükler"""
    load_dotenv()

def get_github_token():
    """GITHUB_TEST_TOKEN değişkenini oku"""
    token = os.getenv("GITHUB_TEST_TOKEN")
    if token:
        return token
    else:
        logging.error("GITHUB_TEST_TOKEN değişkeni bulunamadı.")
        return None

def fetch_github_data(url, timeout=10):
    """GitHub API'den veri çeker"""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        logging.error("GitHub API'den veri çekerken zaman aşımı oldu.")
    except requests.exceptions.ConnectionError:
        logging.error("İnternet bağlantınız koptu veya GitHub çöktü.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Beklenmeyen bir hata oluştu: {e}")
    return None

def save_data_to_json(data, filename):
    """Verileri JSON dosyasına kaydeder"""
    try:
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)
        logging.info(f"Veriler {filename} dosyasına kaydedildi.")
    except Exception as e:
        logging.error(f"Verileri {filename} dosyasına kaydetme hatası: {e}")

def find_search_keys(data, indentation=0):
    """JSON verilerini arar ve 'search' kelimesi geçen anahtarları bulur"""
    filtered_data = {}
    for key, value in data.items():
        if 'search' in key.lower():
            logging.info('  ' * indentation + f"{key}: {value}")
            filtered_data[key] = value
        if isinstance(value, dict):
            filtered_data.update(find_search_keys(value, indentation + 1))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    filtered_data.update(find_search_keys(item, indentation + 1))
    return filtered_data

def mock_ai_analyze(data):
    """Sahte AI analizi"""
    new_model_api_key = os.getenv("NEW_MODEL_API_KEY")
    if new_model_api_key:
        link_count = sum(1 for value in data.values() if isinstance(value, str) and value.startswith("http"))
        logging.info(f"🤖 AI Analizi: {link_count} adet link bulundu, sistem harika!")
    else:
        logging.error("NEW_MODEL_API_KEY değişkeni bulunamadı.")

def main():
    load_environment_variables()
    token = get_github_token()
    if token:
        logging.info(f"Kullanılan Token: {token}")
    else:
        return

    url = 'https://api.github.com'
    data = fetch_github_data(url)
    if data:
        save_data_to_json(data, 'github_response.json')
        filtered_data = find_search_keys(data)
        save_data_to_json(filtered_data, 'filtrelenmis_linkler.json')
        mock_ai_analyze(filtered_data)  # Fonksiyonu main() akışının en sonuna ekliyoruz
    else:
        logging.error("Veri çekerken bir hata oluştu.")

if __name__ == "__main__":
    main()