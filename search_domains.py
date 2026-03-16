import requests
import ipaddress
import concurrent.futures
import re
import os
from urllib.parse import urlparse

# --- 配置区 ---
# 1. 网页指纹特征 (V2Board/XBoard/SSPanel)
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

# 2. 目标 IP 网段 (建议根据 FOFA 观察定期更换)
TARGET_RANGES = [
    "154.223.160.0/24", 
    "45.195.153.0/24", 
    "103.117.138.0/24",
    "103.85.24.0/24"
]

# 3. 公开订阅源 (从中反查面板域名)
SUB_SOURCES = [
    "https://raw.githubusercontent.com/freefq/free/master/v2",
    "https://raw.githubusercontent.com/ssrsub/ssr/master/v2ray",
    "https://raw.githubusercontent.com/Pawpieee/Free-V2ray-Config/main/base64"
]

def check_url(url):
    """指纹探测核心逻辑"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        # 允许跳转，有些站会自动跳转到 /auth/login
        resp = requests.get(url, timeout=5, verify=False, allow_redirects=True, headers=headers)
        content = resp.text.lower()
        if any(fp.lower() in content for fp in FINGERPRINTS):
            # 如果命中了，返回最终跳转后的域名/IP
            final_url = urlparse(resp.url).netloc
            return final_url
    except:
        pass
    return None

def scan_ips():
    print(">>> 正在进行 IP 段主动扫描...")
    test_targets = []
    for r in TARGET_RANGES:
        net = ipaddress.ip_network(r)
        for ip in net.hosts():
            test_targets.append(f"http://{ip}")
            test_targets.append(f"https://{ip}")
    
    found = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        results = list(executor.map(check_url, test_targets))
        found = {r for r in results if r}
    return found

def fetch_subs():
    print(">>> 正在从订阅源逆向提取域名...")
    domains = set()
    for s in SUB_SOURCES:
        try:
            resp = requests.get(s, timeout=10)
            # 匹配可能的域名
            matches = re.findall(r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}', resp.text)
            for d in matches:
                # 排除常见干扰项
                if not any(noise in d.lower() for noise in ['github', 'google', 'cloudflare', 'apple', 'v2ray']):
                    domains.add(d.lower())
        except:
            continue
    return domains

def main():
    # 1. 抓取数据
    ip_assets = scan_ips()
    sub_assets = fetch_subs()
    all_found = ip_assets | sub_assets
    
    # 2. 读取历史数据
    file_path = 'results.txt'
    existing = set()
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            existing = {line.strip() for line in f if line.strip()}
    
    # 3. 比对新资产
    new_assets = all_found - existing
    
    if new_assets:
        print(f"[*] 本次扫描结束，新增 {len(new_assets)} 个新资产！")
        # 追加写入
        with open(file_path, 'a') as f:
            for a in sorted(list(new_assets)):
                f.write(f"{a}\n")
    else:
        print("[-------] 暂未发现库外新资产。")

if __name__ == "__main__":
    main()
