from googlesearch import search
import requests
import re
from urllib.parse import urlparse
import concurrent.futures

FINGERPRINTS = [
    "v2board", "xboard", "SSPanel-Uim", "layouts__index.async.js",
    "/theme/Rocket/assets/", "/theme/Aurora/static/"
]

PATHS = ["/", "/login", "/auth", "/panel", "/user"]

def google_search(query, num=20):
    urls = []
    for u in search(query, num_results=num, lang="en"):
        # 过滤掉 Google 自家域名
        if not any(skip in u for skip in ["google.com", "youtube.com", "support.google.com"]):
            urls.append(u)
    return urls

def check_url(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    domain = urlparse(url).netloc
    for scheme in ["https", "http"]:
        for path in PATHS:
            try:
                resp = requests.get(f"{scheme}://{domain}{path}", timeout=6, verify=False, headers=headers, allow_redirects=True)
                text = resp.text
                final_path = urlparse(resp.url).path
                if any(re.search(fp, text) for fp in FINGERPRINTS) or "/auth/login" in final_path:
                    print(f"[!] 命中指纹: {scheme}://{domain}{path}")
                    return f"{scheme}://{domain}{path}"
            except:
                continue
    return None

def main():
    queries = ["inurl:/auth/login v2board", "intitle:xboard", "sspanel site:.xyz"]
    found = []

    for q in queries:
        print(f"[*] 搜索关键词: {q}")
        urls = google_search(q, num=20)
        print(f"[*] 获取到 {len(urls)} 个结果，开始检测...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_url = {executor.submit(check_url, u): u for u in urls}
            for future in concurrent.futures.as_completed(future_to_url):
                res = future.result()
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
