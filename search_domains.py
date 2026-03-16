import requests
import ipaddress
import concurrent.futures
import re
import os
from urllib.parse import urlparse
# 引入 urllib3 用来静默 SSL 警告
import urllib3

# 禁用安全请求警告（针对 verify=False 产生的警告）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 配置区 ---
FINGERPRINTS = [
    "/theme/Rocket/assets/", 
    "/theme/Aurora/static/", 
    "/theme/default/assets/umi.js",
    "v2board", 
    "xboard", 
    "layouts__index.async.js",
    "auth/login",
    "auth/register"
]

TARGET_RANGES = [
    "154.223.160.0/24", 
    "45.195.153.0/24", 
    "103.117.138.0/24",
    "103.85.24.0/24"
]

SUB_SOURCES = [
    "https://raw.githubusercontent.com/freefq/free/master/v2",
    "https://raw.githubusercontent.com/ssrsub/ssr/master/v2ray",
    "https://raw.githubusercontent.com/Pawpieee/Free-V2ray-Config/main/base64"
]

def check_url(url):
    """深度指纹探测"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        # 增加 allow_redirects=True 处理自动跳转
        resp = requests.get(url, timeout=4, verify=False, allow_redirects=True, headers=headers)
        
        # 只要命中了指纹，或者跳转后的 URL 包含特征路径
        content = resp.text.lower()
        final_url = resp.url.lower()
        
        if any(fp.lower() in content for fp in FINGERPRINTS) or "/auth/login" in final_url:
            target = urlparse(resp.url).netloc
            print(f"[+] 发现目标: {target}")
            return target
    except:
        pass
    return None

def scan_ips():
    print(">>> 正在进行 IP 段指纹扫描...")
    test_targets = []
    for r in TARGET_RANGES:
        try:
            net = ipaddress.ip_network(r)
            for ip in net.hosts():
                # 同时扫描 80 和 443
                test_targets.append(f"http://{ip}")
                test_targets.append(f"https://{ip}")
        except:
            continue
    
    found = set()
    # 增加线程到 150，GitHub Actions 绰绰有余
    with concurrent.futures.ThreadPoolExecutor(max_workers=150) as executor:
        results = list(executor.map(check_url, test_targets))
        found = {r for r in results if r}
    return found

def fetch_subs():
    print(">>> 正在从订阅源提取域名...")
    domains = set()
    headers = {"User-Agent": "Mozilla/5.0"}
    for s in SUB_SOURCES:
        try:
            resp = requests.get(s, timeout=10, headers=headers)
            # 改进正则：匹配更符合域名的字符串
            matches = re.findall(r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}', resp.text)
            for d in matches:
                d_low = d.lower()
                # 排除噪音
                if not any(noise in d_low for noise in ['github', 'google', 'cloudflare', 'apple', 'v2ray', 'microsoft', 'pki']):
                    domains.add(d_low)
        except:
            continue
    return domains

def main():
    # 1. 探测
    found_assets = scan_ips() | fetch_subs()
    
    # 2. 读取历史记录 (results.txt)
    file_path = 'results.txt'
    existing = set()
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            existing = {line.strip() for line in f if line.strip()}
    
    # 3. 筛选新资产
    new_assets = found_assets - existing
    
    if new_assets:
        print(f"[*] 发现 {len(new_assets)} 个新资产，正在存入库中...")
        with open(file_path, 'a') as f:
            for a in sorted(list(new_assets)):
                f.write(f"{a}\n")
    else:
        print("[-------] 暂未发现库外新资产。")

if __name__ == "__main__":
    main()
