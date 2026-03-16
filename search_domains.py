import requests
import os
import concurrent.futures

# 1. 定义你那串极其精准的指纹（只要命中其中一个就是目标）
FINGERPRINTS = [
    "/theme/Rocket/assets/",
    "/theme/Aurora/static/",
    "/theme/default/assets/umi.js",
    "v2board",
    "xboard",
    "layouts__index.async.js"
]

# 2. 目标 IP 段（示例：你可以换成你观察到的机场常用 IP 段）
# 这里以几个常见的香港机房网段为例
TARGET_RANGES = [
    "103.117.138.0/24",
    "154.223.160.0/24",
    "45.195.153.0/24"
]

def check_url(ip):
    url = f"http://{ip}"
    try:
        # 只要 3 秒内有响应
        resp = requests.get(url, timeout=3, verify=False)
        text = resp.text
        # 匹配指纹
        if any(fp in text for fp in FINGERPRINTS):
            print(f"[!] 发现匹配目标: {ip}")
            return ip
    except:
        pass
    return None

def main():
    print("开始主动探测指纹...")
    found_ips = []
    
    # 将 CIDR 转为 IP 列表（简单处理）
    # 实际建议使用 ipaddress 库生成列表
    test_ips = []
    for r in TARGET_RANGES:
        prefix = ".".join(r.split('.')[:-1])
        for i in range(1, 255):
            test_ips.append(f"{prefix}.{i}")

    # 开启 100 线程极速扫描
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        results = list(executor.map(check_url, test_ips))
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
