import requests
import re
import os
import time
from datetime import datetime, timedelta

# 深度优化的搜索词库
SEARCH_QUERIES = [
    'vless sub token extension:txt',
    'vmess subscribe token extension:txt',
    'filename:proxies.yaml "vmess"',
    'filename:sub_list.txt "token="'
]

def get_github_leaks():
    leaks = set()
    token = os.getenv('GH_TOKEN')
    # 安全起见，这里不再从环境变量读名字写入文件
    
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    # 搜索 72 小时内的资源
    time_cutoff = (datetime.utcnow() - timedelta(hours=72)).isoformat()
    print(f"🕵️ 正在执行 72 小时深度捡漏任务...")

    # 1. 搜索 GitHub Code
    for query in SEARCH_QUERIES:
        search_url = f"https://api.github.com/search/code?q={query}+pushed:>{time_cutoff}"
        try:
            r = requests.get(search_url, headers=headers, timeout=15)
            if r.status_code == 200:
                items = r.json().get('items', [])
                for item in items:
                    raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    c_r = requests.get(raw_url, timeout=10)
                    if c_r.status_code == 200:
                        found = re.findall(r'https?://[^\s<>"]+?token=[a-zA-Z0-9]{10,}', c_r.text)
                        for link in found:
                            if 'github.com' not in link: leaks.add(link)
            time.sleep(1.5) 
        except Exception: continue

    # 2. 额外捡漏：搜索公共 Gists (可选增加)
    print(f"⚡ 正在同步扫描 Gist 资源...")
    gist_url = "https://api.github.com/gists/public?per_page=30"
    try:
        gr = requests.get(gist_url, headers=headers, timeout=10)
        if gr.status_code == 200:
            for gist in gr.json():
                for file in gist['files'].values():
                    if file['raw_url'].endswith('.txt'):
                        fr = requests.get(file['raw_url'], timeout=5)
                        found = re.findall(r'https?://[^\s<>"]+?token=[a-zA-Z0-9]{10,}', fr.text)
                        for link in found: leaks.add(link)
    except Exception: pass

    return leaks

def verify_and_save(links):
    valid_links = []
    ua = {'User-Agent': 'ClashforWindows/0.19.0'}
    
    print(f"🧪 正在验证 {len(links)} 条源...")
    for link in links:
        try:
            r = requests.get(link, headers=ua, timeout=5, stream=True)
            if r.status_code == 200 and len(r.raw.read(100)) > 20:
                valid_links.append(link)
        except: continue

    with open('github_leaks.txt', 'w', encoding='utf-8') as f:
        f.write(f"# === GitHub 自动捡漏结果 ===\n")
        f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        if valid_links:
            f.write('\n'.join(sorted(list(set(valid_links)))))
        else:
            f.write("# 本轮搜索暂未匹配到有效链接。这通常是因为 GitHub 索引延迟，建议几小时后再次查看。")

if __name__ == "__main__":
    links = get_github_leaks()
    verify_and_save(links)
