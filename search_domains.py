import requests
import socket
import re
import concurrent.futures
import urllib3
from urllib.parse import urlparse

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FINGERPRINTS = [
    "/theme/Rocket/assets/", "/theme/Aurora/static/", "/theme/default/assets/umi.js",
    "v2board", "xboard", "SSPanel-Uim", "layouts__index.async.js",
    r'{"message":"Unauthenticated\."}' # 转义特殊字符
]

# 优化路径：先测根目录，根目录没中再测 /login
PATHS = ["/", "/login"] 

def fetch_domains(keyword):
    """从 crt.sh 获取域名，增加异常处理"""
    url = f"https://crt.sh/?q={keyword}&output=json"
    try:
        # crt.sh 经常超时，给 30 秒
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200: return []
        data = resp.json()
        domains = {entry.get("name_value").strip().lower() for entry in data if entry.get("name_value")}
        
        # 处理多域名合并的情况 (name_value 可能是 "a.com\nb.com")
        final_domains = set()
        for d in domains:
            for sub_d in d.split('\n'):
                if not sub_d.startswith("*."):
                    final_domains.add(sub_d)
        return list(final_domains)
    except Exception as e:
        print(f"[x] crt.sh 查询失败: {e}")
        return []

def check_domain(domain):
    """检测优化：命中即止，减少请求"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    # 策略：如果 https 通了就不跑 http
    for scheme in ["https", "http"]:
        for path in PATHS:
            try:
                url = f"{scheme}://{domain}{path}"
                # allow_redirects=True 很重要，因为面板常在 /auth/login
                resp = requests.get(url, timeout=6, verify=False, allow_redirects=True, headers=headers)
                
                # 同时检测内容和最终跳转的路径
                text = resp.text
                final_path = urlparse(resp.url).path
                
                if any(re.search(fp, text) for fp in FINGERPRINTS) or "/auth/login" in final_path:
                    return f"{scheme}://{domain}{path}"
            except:
                continue
    return None

def main():
    # 关键字建议：除了域名，还可以搜 "v2board", "xboard", "v2ray"
    keyword = "v2board" 
    print(f"[*] 正在从证书库检索关键词: {keyword}")

    domains = fetch_domains(keyword)
    if not domains:
        print("[!] 未获取到域名，请检查 crt.sh 状态或更换关键字。")
        return

    print(f"[*] 获取到 {len(domains)} 个潜在域名，开始存活及指纹扫描...")

    found = []
    # 线程不宜过高，防止被 WAF 批量封禁
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        future_to_domain = {executor.submit(check_domain, d): d for d in domains}
        for future in concurrent.futures.as_completed(future_to_domain):
            res = future.result()
            if res:
                print(f"[!] 命中目标: {res}")
                found.append(res)

    if found:
        with open("results.txt", "a") as f:
            for item in sorted(set(found)):
                f.write(f"{item}\n")
        print(f"\n[+] 探测结束，库内新增 {len(found)} 个有效资产。")
    else:
        print("\n[-] 本次扫描未发现有效资产。")

if __name__ == "__main__":
    main()
