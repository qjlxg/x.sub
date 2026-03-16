import requests
import socket

# 指纹列表
FINGERPRINTS = [
    "/theme/Rocket/assets/",
    "/theme/Aurora/static/",
    "/theme/default/assets/umi.js",
    "/theme/Xoouo-Simple/assets/umi.js",
    "/assets/umi",
    "v2board",
    "xboard",
    "SSPanel-Uim",
    "{\"message\":\"Unauthenticated.\"}",
    "layouts__index.async.js"
]

def fetch_domains(keyword):
    """从 crt.sh 获取域名列表"""
    url = f"https://crt.sh/?q={keyword}&output=json"
    resp = requests.get(url, timeout=15)
    data = resp.json()
    domains = set()
    for entry in data:
        name = entry.get("name_value")
        if name:
            for d in name.split("\n"):
                if not d.startswith("*."):
                    domains.add(d.strip())
    return list(domains)

def resolve_domain(domain):
    """DNS解析域名 -> IP"""
    try:
        ip = socket.gethostbyname(domain)
        return ip
    except Exception:
        return None

def check_domain(domain):
    """检测域名是否命中指纹"""
    for scheme in ["http", "https"]:
        try:
            resp = requests.get(f"{scheme}://{domain}", timeout=5, verify=False)
            if any(fp in resp.text for fp in FINGERPRINTS):
                print(f"[!] 命中指纹: {domain}")
                return True
        except Exception:
            pass
    return False

def main():
    keyword = "example.com"  # 换成你要查的关键字
    domains = fetch_domains(keyword)
    print(f"共获取 {len(domains)} 个域名")

    stats = {
        "total_domains": len(domains),
        "resolved": 0,
        "checked": 0,
        "matched": 0
    }

    found = []
    for d in domains:
        ip = resolve_domain(d)
        if ip:
            stats["resolved"] += 1
            if check_domain(d):
                stats["matched"] += 1
                found.append((d, ip))
            stats["checked"] += 1

    # 输出结果
    if found:
        with open("results.txt", "a") as f:
            for d, ip in found:
                f.write(f"{d} -> {ip}\n")
        print(f"探测结束，新增 {len(found)} 个资产。")
    else:
        print("未发现匹配指纹的域名。")

    # 打印统计汇总
    print("\n=== 扫描统计 ===")
    print(f"总域名数: {stats['total_domains']}")
    print(f"解析成功: {stats['resolved']}")
    print(f"请求检测: {stats['checked']}")
    print(f"命中指纹: {stats['matched']}")

if __name__ == "__main__":
    main()
