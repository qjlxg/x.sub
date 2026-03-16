import requests
import re
import urllib3
import os
from googlesearch import search
from urllib.parse import urlparse

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 指纹特征（保持之前的精准指纹）
FINGERPRINTS = [
    "/theme/Rocket/assets/", "/theme/Aurora/static/", "/theme/default/assets/umi.js",
    "v2board", "xboard", "SSPanel-Uim", "layouts__index.async.js",
    r'{"message":"Unauthenticated\."}'
]

# 精选 Google Dorks 关键词：利用搜索语法过滤无关结果
# 例如搜 inurl:login 会过滤掉大部分博客文章
DORKS = [
    'inurl:login "v2board"',
    'inurl:auth/login "xboard"',
    '"sspanel-uim" inurl:auth/login',
    'intitle:"V2Board" login'
]

def check_url(url):
    """指纹检测核心"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        # 增加 allow_redirects=True 处理跳转
        resp = requests.get(url, timeout=7, verify=False, allow_redirects=True, headers=headers)
        text = resp.text
        final_url = resp.url.lower()
        
        # 匹配内容指纹或 URL 特征
        if any(re.search(fp, text) for fp in FINGERPRINTS) or "/auth/login" in final_url:
            # 提取根域名，方便去重存储
            domain = urlparse(resp.url).netloc
            return domain
    except:
        pass
    return None

def main():
    res_file = "results_google.txt"
    # 加载已有的库，避免重复
    existing = set()
    if os.path.exists(res_file):
        with open(res_file, "r") as f:
            existing = {line.strip() for line in f if line.strip()}

    found_this_time = set()

    for query in DORKS:
        print(f"[*] 正在 Google 检索: {query}")
        try:
            # 使用 googlesearch-python 库，自动处理分页和 User-Agent
            # stop=30 表示每个关键词取前 30 个结果
            for url in search(query, stop=30, pause=2):
                # 过滤掉常见的干扰域名
                if any(noise in url for noise in ['github.com', 'google.com', 'twitter.com', 'facebook.com']):
                    continue
                
                domain = urlparse(url).netloc
                if domain in existing or domain in found_this_time:
                    continue

                print(f"    - 正在扫描: {url}")
                res = check_url(url)
                if res:
                    print(f"    [!] 命中指纹: {res}")
                    found_this_time.add(res)
        except Exception as e:
            print(f"[x] Google 搜索出错 (可能触发频率限制): {e}")

    # 存储结果
    if found_this_time:
        with open(res_file, "a") as f:
            for d in sorted(found_this_time):
                f.write(f"{d}\n")
        print(f"\n[+] 探测结束，Google 维度新增 {len(found_this_time)} 个有效资产。")
    else:
        print("\n[-] 本次 Google 扫描未发现新资产。")

if __name__ == "__main__":
    main()
