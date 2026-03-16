import requests
from urllib.parse import urlparse
import re

FINGERPRINTS = [
    "v2board", "xboard", "SSPanel-Uim", "layouts__index.async.js",
    "/theme/Rocket/assets/", "/theme/Aurora/static/"
]

def google_search(query, api_key, cse_id):
    """调用 Google Custom Search API"""
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"q": query, "key": api_key, "cx": cse_id}
    resp = requests.get(url, params=params)
    results = resp.json().get("items", [])
    return [item["link"] for item in results]

def check_url(url):
    """检测 URL 是否命中指纹"""
    try:
        resp = requests.get(url, timeout=6, verify=False, allow_redirects=True)
        text = resp.text
        if any(re.search(fp, text) for fp in FINGERPRINTS):
            print(f"[!] 命中指纹: {url}")
            return url
    except:
        pass
    return None

def main():
    api_key = "你的Google API Key"
    cse_id = "你的Custom Search Engine ID"
    queries = ["v2board", "xboard", "sspanel", "vpn"]

    found = []
    for q in queries:
        urls = google_search(q, api_key, cse_id)
        for u in urls:
            res = check_url(u)
            if res:
                found.append(res)

    if found:
        with open("results_google.txt", "a") as f:
            for u in found:
                f.write(f"{u}\n")
        print(f"\n[+] 探测结束，新增 {len(found)} 个资产。")
    else:
        print("\n[-] 本次扫描未发现有效资产。")

if __name__ == "__main__":
    main()
