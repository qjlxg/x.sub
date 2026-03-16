import requests
from bs4 import BeautifulSoup
import re

FINGERPRINTS = ["v2board", "xboard", "SSPanel-Uim"]

def google_scrape(query, num=10):
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://www.google.com/search?q={query}&num={num}"
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    for a in soup.select("a"):
        href = a.get("href")
        if href and href.startswith("http"):
            links.append(href)
    return links

def check_url(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, timeout=6, verify=False, headers=headers)
        text = resp.text
        if any(fp in text for fp in FINGERPRINTS):
            print(f"[!] 命中指纹: {url}")
            return url
    except:
        pass
    return None

def main():
    queries = ["v2board", "xboard", "sspanel"]
    found = []
    for q in queries:
        print(f"[*] 搜索关键词: {q}")
        urls = google_scrape(q, num=20)
        for u in urls:
            res = check_url(u)
            if res:
                found.append(res)

    if found:
        with open("results_google.txt", "a") as f:
            for u in sorted(set(found)):
                f.write(f"{u}\n")
        print(f"\n[+] 探测结束，新增 {len(found)} 个有效资产。")
    else:
        print("\n[-] 本次扫描未发现有效资产。")

if __name__ == "__main__":
    main()
