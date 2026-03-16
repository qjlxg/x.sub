import requests
import re
import concurrent.futures
import urllib3
import os
import time
from urllib.parse import urlparse
from googlesearch import search  # 确保 pip install googlesearch-python

# 屏蔽 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 配置区 ---
FINGERPRINTS = [
    "/theme/Rocket/assets/", "/theme/Aurora/static/", "/theme/default/assets/umi.js",
    "/theme/Xoouo-Simple/assets/umi.js", "v2board", "xboard", "SSPanel-Uim", 
    "layouts__index.async.js", r'{"message":"Unauthenticated\."}'
]

# Google Dorks 语法
DORKS = [
    'inurl:login "v2board"',
    'inurl:auth/login "xboard"',
    '"sspanel-uim" inurl:auth/login'
]

# 证书搜索关键词
CRT_KEYWORDS = ["v2board", "xboard", "sspanel"]

# 目标结果文件
RESULT_FILE = "results.txt"

def fetch_from_crt(keyword):
    """维度1：从证书库抓取历史域名"""
    print(f"[*] [证书库] 检索关键词: {keyword}")
    url = f"https://crt.sh/?q={keyword}&output=json"
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            domains = {e.get("name_value").strip().lower() for e in data if e.get("name_value")}
            return {d for raw in domains for d in raw.split('\n') if not d.startswith("*.")}
    except Exception as e:
        print(f"[x] crt.sh 报错: {e}")
    return set()

def fetch_from_google(query):
    """维度2：从 Google 抓取实时活跃站点"""
    print(f"[*] [Google] 检索 Dork: {query}")
    found_urls = set()
    try:
        # 适配新版 googlesearch-python (1.2.0+)
        # num_results 替代了旧版的 stop
        results = search(query, num_results=20, lang="en")
        for url in results:
            if not any(noise in url for noise in ['github.com', 'google.com', 'twitter.com']):
                found_urls.add(urlparse(url).netloc)
    except Exception as e:
        print(f"[x] Google 搜索异常: {e}")
    return found_urls

def check_domain(domain):
    """维度3：指纹检测核心逻辑"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    for scheme in ["https", "http"]:
        for path in ["/", "/login"]:
            try:
                url = f"{scheme}://{domain}{path}"
                resp = requests.get(url, timeout=5, verify=False, allow_redirects=True, headers=headers)
                text = resp.text
                # 命中指纹或跳转到登录页
                if any(re.search(fp, text) for fp in FINGERPRINTS) or "/auth/login" in resp.url.lower():
                    return urlparse(resp.url).netloc
            except:
                continue
    return None

def main():
    # 1. 加载本地旧资产，实现增量更新
    existing = set()
    if os.path.exists(RESULT_FILE):
        with open(RESULT_FILE, "r") as f:
            existing = {line.strip() for line in f if line.strip()}

    # 2. 汇总所有待测域名
    all_potential = set()
    
    # 执行 Google 抓取
    for q in DORKS:
        all_potential.update(fetch_from_google(q))
        time.sleep(5) # 降低 Google 封锁概率

    # 执行 证书库 抓取
    for kw in CRT_KEYWORDS:
        all_potential.update(fetch_from_crt(kw))

    # 3. 过滤已知资产，减少请求压力
    pending = all_potential - existing
    print(f"\n[*] 汇总唯一域名: {len(all_potential)} | 待检测新域名: {len(pending)}")

    # 4. 并发探测
    new_found = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_domain = {executor.submit(check_domain, d): d for d in pending}
        for future in concurrent.futures.as_completed(future_to_domain):
            res = future.result()
            if res and res not in existing:
                print(f"[!] 发现资产: {res}")
                new_found.add(res)

    # 5. 持久化存储
    if new_found:
        with open(RESULT_FILE, "a") as f:
            for item in sorted(new_found):
                f.write(f"{item}\n")
        print(f"\n[+] 扫描结束！本次新增 {len(new_found)} 个资产。")
    else:
        print("\n[-] 本次任务未发现新资产。")

if __name__ == "__main__":
    main()
