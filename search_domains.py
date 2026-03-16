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
    "/theme/Xoouo-Simple/assets/umi.js", "/assets/umi",
    "v2board", "xboard", "SSPanel-Uim", "layouts__index.async.js",
    r'{"message":"Unauthenticated\."}'
]

# 常见路径
PATHS = ["/", "/login", "/auth", "/panel", "/user"]

def fetch_domains(keyword, after=None, before=None):
    """从 crt.sh 获取域名，支持时间范围过滤"""
    url = f"https://crt.sh/?q={keyword}&output=json"
    if after:
        url += f"&opt=after:{after}"
    if before:
        url += f"&opt=before:{before}"
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            return []
        data = resp.json()
        domains = set()
        for entry in data:
            name = entry.get("name_value")
            if name:
                for d in name.split("\n"):
                    d = d.strip().lower()
                    if not d.startswith("*."):
                        domains.add(d)
        return list(domains)
    except Exception as e:
        print(f"[x] crt.sh 查询失败: {e}")
        return []

def check_domain(domain):
    """检测域名是否命中指纹"""
    headers = {"User-Agent": "Mozilla/5.0"}
    for scheme in ["https", "http"]:
        for path in PATHS:
            try:
                url = f"{scheme}://{domain}{path}"
                resp = requests.get(url, timeout=6, verify=False, allow_redirects=True, headers=headers)
                text = resp.text
                final_path = urlparse(resp.url).path
                if any(re.search(fp, text) for fp in FINGERPRINTS) or "/auth/login" in final_path:
                    return f"{scheme}://{domain}{path}"
            except:
                continue
    return None

def main():
    keyword = "v2board"  # 换成你要查的关键字
    after = "2026-03-13"
    before = "2026-03-16"

    print(f"[*] 正在从证书库检索关键词: {keyword}")
    domains = fetch_domains(keyword, after, before)
    print(f"[*] 获取到 {len(domains)} 个潜在域名")

    stats = {"total": len(domains), "resolved": 0, "checked": 0, "matched": 0, "resolve_fail": 0}
    found = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        future_to_domain = {executor.submit(check_domain, d): d for d in domains}
        for future in concurrent.futures.as_completed(future_to_domain):
            d = future_to_domain[future]
            try:
                res = future.result()
                stats["checked"] += 1
                if res:
                    stats["matched"] += 1
                    found.append(res)
            except Exception:
                stats["resolve_fail"] += 1

    if found:
        with open("results.txt", "a") as f:
            for item in sorted(set(found)):
                f.write(f"{item}\n")
        print(f"\n[+] 探测结束，新增 {len(found)} 个有效资产。")
    else:
        print("\n[-] 本次扫描未发现有效资产。")

    print("\n=== 扫描统计 ===")
    for k, v in stats.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    main()
