import requests
import re
from urllib.parse import urlparse

HEADERS = {"User-Agent": "Mozilla/5.0"}

# 公开订阅源（不会被封）
SUB_SOURCES = [
    # GitHub 公开订阅聚合
    "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.txt",
    "https://raw.githubusercontent.com/adiwzx/freenode/main/sub",
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/subscribe.txt",
    "https://raw.githubusercontent.com/learnhard-cn/free_proxy_ss/main/free",
    "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/sub/sub_merge.txt",

    # 公开订阅站
    "https://sub.pmsub.me/clash.yaml",
    "https://sub.pmsub.me/base64",
    "https://raw.githubusercontent.com/freefq/free/master/v2",
    "https://raw.githubusercontent.com/freefq/free/master/ssr",

    # GitHub issue RSS（有效）
    "https://rsshub.app/github/issue/adiwzx/freenode",
    "https://rsshub.app/github/issue/peasoft/NoMoreWalls",
]


KEYWORDS = ["vmess", "vless", "trojan", "ss://", "sub", "subscription"]

def extract_links(text):
    pattern = r'https?://[^\s"\'<>]+'
    return [x for x in re.findall(pattern, text) if any(k in x for k in KEYWORDS)]

def extract_domains(links):
    domains = set()
    for link in links:
        domain = urlparse(link).netloc
        if domain and not any(x in domain for x in ["github", "google", "cloudflare"]):
            domains.add(domain)
    return domains

def run():
    all_links = set()

    print("🚀 开始从订阅源收集泄露订阅...\n")

    for src in SUB_SOURCES:
        print(f"🔍 正在抓取：{src}")
        try:
            r = requests.get(src, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                all_links.update(extract_links(r.text))
        except:
            pass

    domains = extract_domains(all_links)

    print("\n🎉 完成订阅源扫描！")
    print(f"📌 发现订阅链接：{len(all_links)} 条")
    print(f"📌 提取域名：{len(domains)} 个")

    with open("leaked_subscriptions.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(all_links)))

    with open("leaked_domains.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(domains)))

if __name__ == "__main__":
    run()
