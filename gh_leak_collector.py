import requests
import re
from urllib.parse import urlparse

HEADERS = {"User-Agent": "Mozilla/5.0"}

KEYWORDS = [
    "vmess", "vless", "trojan", "ss://", "clash", "sub", "subscription"
]

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

# -----------------------------
# GitHub API（模糊搜索）
# -----------------------------
def scan_github():
    print("🔍 GitHub API 扫描中...")
    results = set()
    for kw in KEYWORDS:
        url = f"https://api.github.com/search/code?q={kw}&per_page=50"
        r = requests.get(url, headers=HEADERS)
        if r.status_code != 200:
            continue
        items = r.json().get("items", [])
        for item in items:
            raw = item["html_url"].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
            try:
                t = requests.get(raw, headers=HEADERS, timeout=10).text
                results.update(extract_links(t))
            except:
                pass
    return results

# -----------------------------
# GitLab 搜索
# -----------------------------
def scan_gitlab():
    print("🔍 GitLab 扫描中...")
    results = set()
    for kw in KEYWORDS:
        url = f"https://gitlab.com/api/v4/search?scope=blobs&search={kw}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            for item in r.json():
                raw = item.get("url", "")
                if raw.endswith(".txt") or raw.endswith(".yaml") or raw.endswith(".yml"):
                    try:
                        t = requests.get(raw, headers=HEADERS, timeout=10).text
                        results.update(extract_links(t))
                    except:
                        pass
        except:
            pass
    return results

# -----------------------------
# Pastebin 扫描
# -----------------------------
def scan_pastebin():
    print("🔍 Pastebin 扫描中...")
    results = set()
    url = "https://pastebin.com/archive"
    try:
        html = requests.get(url, headers=HEADERS).text
        ids = re.findall(r'/([A-Za-z0-9]{8})"', html)
        for pid in ids[:20]:
            raw = f"https://pastebin.com/raw/{pid}"
            try:
                t = requests.get(raw, headers=HEADERS, timeout=10).text
                results.update(extract_links(t))
            except:
                pass
    except:
        pass
    return results

# -----------------------------
# Reddit 扫描（无需登录）
# -----------------------------
def scan_reddit():
    print("🔍 Reddit 扫描中...")
    results = set()
    for kw in KEYWORDS:
        url = f"https://www.reddit.com/search.json?q={kw}&limit=20"
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            posts = r.json().get("data", {}).get("children", [])
            for p in posts:
                text = p["data"].get("selftext", "") + " " + p["data"].get("title", "")
                results.update(extract_links(text))
        except:
            pass
    return results

# -----------------------------
# 主程序
# -----------------------------
def run():
    all_links = set()

    all_links |= scan_github()
    all_links |= scan_gitlab()
    all_links |= scan_pastebin()
    all_links |= scan_reddit()

    domains = extract_domains(all_links)

    print("\n🎉 扫描完成！")
    print(f"📌 发现订阅链接：{len(all_links)} 条")
    print(f"📌 提取域名：{len(domains)} 个")

    with open("leaked_subscriptions.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(all_links)))

    with open("leaked_domains.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(domains)))

if __name__ == "__main__":
    run()
