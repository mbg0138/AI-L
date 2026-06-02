import requests
import os
import json
from dotenv import load_dotenv
import logging
from groq import Groq

# Logger ayarları
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_environment_variables():
    """dotenv dosyasındaki değişkenleri yükler"""
    load_dotenv()

def fetch_github_data(url, timeout=10):
    """GitHub API'den veri çeker"""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        logging.error("GitHub API'den veri çekerken zaman aşımı oldu.")
    except requests.exceptions.ConnectionError:
        logging.error("İnternet bağlantınız koptu veya GitHub çöktü.");
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
















def extract_top_repos(data):
    """Gelen veriden ilk 5 depoyu çıkarır"""
    top_repos = []
    for repo in data['items'][:5]:
        top_repo = {
            'name': repo['name'],
            'description': repo['description'],
            'stargazers_count': repo['stargazers_count'],
            'html_url': repo['html_url']
        }
        top_repos.append(top_repo)
    return top_repos
def analyze_with_groq(data):
    """Groq API'sini kullanarak verileri analiz eder"""
    token = os.getenv("NEW_MODEL_API_KEY")
    if token:
        try:
            client = Groq(api_key=token)
            json_string = json.dumps(data)

            prompt = 'Sen kıdemli bir teknoloji analistisin. Sana verilen trend GitHub projelerini incele ve yazılımcılar için Türkçe heyecan verici bir trend bülteni özeti hazırla.'
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt + " " + json_string}]
            )
            logging.info(f"\n🤖 AI ÖZETİ:\n{response.choices[0].message.content}\n")
            # AI raporu dosyasına yazma

            with open('trend_raporu.txt', 'w') as file:
                file.write(response.choices[0].message.content)

            logging.info('AI raporu trend_raporu.txt dosyasına yazıldı.')
        except Exception as e:
            logging.error(f"Groq API'si ile analiz ederken bir hata oluştu: {e}")
    else:
        logging.error("NEW_MODEL_API_KEY değişkeni bulunamadı.")

def main():
    load_environment_variables()

    url = 'https://api.github.com/search/repositories?q=language:python&sort=stars&order=desc'
    data = fetch_github_data(url)
    if data:
        save_data_to_json(data, 'github_response.json')



        top_repos = extract_top_repos(data)
        save_data_to_json(top_repos, 'filtrelenmis_linkler.json')
        analyze_with_groq(top_repos)  # Yeni fonksiyonu çağırıyoruz
    else:
        logging.error("Veri çekerken bir hata oluştu.")

if __name__ == "__main__":
    main()