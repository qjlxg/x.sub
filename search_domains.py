import requests
import ipaddress
import concurrent.futures

# 1. 指纹列表
FINGERPRINTS = [
    "/theme/Rocket/assets/",
    "/theme/Aurora/static/",
    "/theme/default/assets/umi.js",
    "v2board",
    "xboard",
    "layouts__index.async.js"
]

# 2. 目标 IP 段
TARGET_RANGES = [
    "103.117.138.0/24",
    "154.223.160.0/24",
    "45.195.153.0/24"
]

# 3. 常见端口
PORTS = [80, 443]

def check_url(ip, port):
    scheme = "https" if port == 443 else "http"
    url = f"{scheme}://{ip}:{port}"
    try:
        resp = requests.get(url, timeout=5, verify=False, allow_redirects=True)
        text = resp.text
        if any(fp in text for fp in FINGERPRINTS):
            print(f"[!] 命中指纹: {ip}:{port}")
            return f"{ip}:{port}"
        else:
            print(f"[-] {ip}:{port} 有响应但未匹配")
    except requests.exceptions.RequestException as e:
        print(f"[x] {ip}:{port} 请求失败: {e}")
    return None

def main():
    print("开始扫描指纹...")
    found_ips = []

    # 展开网段
    test_ips = []
    for r in TARGET_RANGES:
        net = ipaddress.ip_network(r)
        for ip in net.hosts():
            test_ips.append(str(ip))

    # 多线程扫描
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = []
        for ip in test_ips:
            for port in PORTS:
                futures.append(executor.submit(check_url, ip, port))
        results = [f.result() for f in futures]

    found_ips = [r for r in results if r]

    # 写入结果
    if found_ips:
        with open('results.txt', 'a') as f:
            for ip in found_ips:
                f.write(f"{ip}\n")
        print(f"探测结束，新增 {len(found_ips)} 个资产。")
    else:
        print("本次探测未发现匹配指纹的活跃 IP。")

if __name__ == "__main__":
    main()
