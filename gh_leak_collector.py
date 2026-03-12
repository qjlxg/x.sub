import requests
import re
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# 更宽松、更高命中率的关键词
SEARCH_KEYWORDS = [
    "vmess",
    "vless",
    "trojan",
    "ss://",
    "subscription",
    "sub",
    "机场",
    "clash",
    "proxies",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def github_search(keyword, page=1):
    """使用 GitHub 网页搜索（非 API），命中率极高"""
    url = f"https://github.com/search?q={keyword}&type=code&p={page}"
    r = requests.get(url, headers=HEADERS, timeout=10)
    return r.text if r.status_code == 200 else None


def extract_raw_urls(html):
    """从搜索结果中提取 raw.githubusercontent.com 文件地址"""
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select("a.Link--primary")
    raw_urls = []

    for a in links:
        href = a.get("href")
        if "/blob/" in href:
            raw = "https://raw.githubusercontent.com" + href.replace("/blob/", "/")
            raw_urls.append(raw)

    return raw_urls


def extract_sub_links(text):
    """提取订阅链接"""
    pattern = r'https?://[^\s"\'<>]+'
    return re.findall(pattern, text)


def extract_domains(links):
    domains = set()
    for link in links:
        domain = urlparse(link).netloc
        if domain and not any(x in domain for x in ["github", "google", "cloudflare"]):
            domains.add(domain)
    return domains


def run():
    all_links = set()
    all_domains = set()

    print("🚀 开始 GitHub 高命中率捡漏扫描...\n")

    for kw in SEARCH_KEYWORDS:
        print(f"🔍 正在搜索关键词：{kw}")

        for page in range(1, 3):  # 每个关键词扫 2 页
            html = github_search(kw, page)
            if not html:
                continue

            raw_files = extract_raw_urls(html)

            for raw in raw_files:
                try:
                    r = requests.get(raw, headers=HEADERS, timeout=10)
                    if r.status_code == 200:
                        subs = extract_sub_links(r.text)
                        for s in subs:
                            if any(x in s for x in ["vmess", "vless", "trojan", "ss://", "sub"]):
                                all_links.add(s)
                    time.sleep(1)
                except:
                    pass

        print(f"✔ 完成：{kw}\n")
        time.sleep(2)

    # 提取域名
    all_domains = extract_domains(all_links)

    # 保存结果
    with open("leaked_subscriptions.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(all_links)))

    with open("leaked_domains.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(all_domains)))

    print("🎉 扫描完成！")
    print(f"📌 发现订阅链接：{len(all_links)} 条")
    print(f"📌 提取域名：{len(all_domains)} 个")


if __name__ == "__main__":
    run()
