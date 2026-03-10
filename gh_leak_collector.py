import requests
import re
import os
import time
from datetime import datetime, timedelta
from urllib.parse import urlparse

# 精选的高转化率搜索关键词
SEARCH_QUERIES = [
    '"api/v1/client/subscribe?token="',
    'path:/data/ filename:subscribe.txt',
    'filename:proxies.yaml "type: vmess"',
    'filename:sub_list.txt "token="'
]

def get_github_leaks():
    leaks = set()
    domains = set()
    token = os.getenv('GH_TOKEN')
    
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    time_cutoff = (datetime.utcnow() - timedelta(hours=72)).isoformat()
    
    print(f"🕵️ 正在执行深度扫描（Code + Domain 提取）...")

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
                        # 1. 提取完整订阅链接
                        found_links = re.findall(r'https?://[^\s<>"]+?token=[a-zA-Z0-9]{10,}', c_r.text)
                        for link in found_links:
                            if 'github' not in link:
                                leaks.add(link)
                                # 2. 提取域名用于注册测试
                                domain = urlparse(link).netloc
                                if domain and not any(x in domain for x in ['github', 'google', 'cloudflare']):
                                    domains.add(domain)
                print(f"✅ 关键词 [{query}]: 扫描完成")
            time.sleep(2) 
        except Exception as e:
            print(f"❌ 出错: {e}")
            
    return leaks, domains

def save_results(links, domains):
    # 保存订阅链接
    with open('github_leaks.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 捡漏订阅列表 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write('\n'.join(sorted(list(links))) if links else "# 暂无订阅")

    # 保存提取出的域名，供注册脚本使用
    with open('domains_to_register.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(list(domains))) if domains else "")
    
    print(f"🎉 处理完毕！捡到 {len(links)} 个订阅，提取出 {len(domains)} 个潜在机场域名。")

if __name__ == "__main__":
    leaks, domains = get_github_leaks()
    save_results(leaks, domains)
