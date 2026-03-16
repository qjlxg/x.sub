import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time
import random

def get_domain(url):
    try:
        domain = urlparse(url).netloc
        if domain and not any(x in domain for x in ['google', 'github', 'youtube', 'facebook']):
            return domain
    except:
        return None

def google_search_scraping(query):
    domains = set()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    # 模拟 Google 搜索链接
    url = f"https://www.google.com/search?q={query}&num=50"
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Google 搜索结果的链接通常在 h3 标签附近的 a 标签里
            for a in soup.find_all('a'):
                href = a.get('href')
                if href and "url?q=" in href:
                    # 提取真实 URL
                    clean_url = href.split("url?q=")[1].split("&sa=")[0]
                    domain = get_domain(clean_url)
                    if domain:
                        domains.add(domain)
        elif resp.status_code == 429:
            print("触发了 Google 429 频率限制。")
    except Exception as e:
        print(f"请求出错: {e}")
    return domains

def main():
    queries = [
        'inurl:"/theme/Rocket/assets/"',
        'intitle:"V2Board" login'
    ]
    
    all_found = set()
    for q in queries:
        print(f"正在深度搜索: {q}")
        all_found.update(google_search_scraping(q))
        time.sleep(random.uniform(5, 10)) # 延长等待时间

    # ... 后续的去重和写入 logic 同之前一样 ...
    # (省略部分参考之前的脚本)
