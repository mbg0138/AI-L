import requests

def fetch_github_keys():
    url = 'https://api.github.com'
    response = requests.get(url)
    
    if response.status_code == 200:
        keys = list(response.json().keys())[:5]  # İlk 5 anahtarı al
        for i, key in enumerate(keys, start=1):
            print(f"{i}. {key}")
    else:
        print(f"Hata: {response.status_code}")

fetch_github_keys()