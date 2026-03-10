import requests
import re
import os
import time
from datetime import datetime, timedelta

# 深度优化的捡漏关键词
SEARCH_QUERIES = [
    'vless sub token extension:txt',
    'vmess subscribe token extension:txt',
    'filename:proxies.yaml "type: vmess"',
    'path:v2ray filename:config.json'
]

def get_github_leaks():
    leaks = set()
    # 变量 1：系统的 Secret，用于权限
    token = os.getenv('GH_TOKEN')
    # 变量 2：你设置的 Variable，用于控制
    bot_var = os.getenv('MY_BOT_NAME', '6') 
    
    # 逻辑：如果 BOT 变量是纯数字，就搜过去 X 小时，否则默认 6 小时
    search_hours = int(bot_var) if bot_var.isdigit() else 6
    
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    time_cutoff = (datetime.utcnow() - timedelta(hours=search_hours)).isoformat()
    
    print(f"🤖 机器人 [{bot_var}] 正在执行捡漏任务...")
    print(f"🕒 搜索深度：最近 {search_hours} 小时内更新的代码")

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
                        # 识别订阅格式
                        found = re.findall(r'https?://[^\s<>"]+?token=[a-zA-Z0-9]{15,}', c_r.text)
                        for link in found:
                            if 'github' not in link: 
                                leaks.add(link)
                print(f"✅ 关键词 [{query}]: 扫描完成")
            time.sleep(1.5) 
        except Exception as e:
            print(f"❌ 出错: {e}")
    return leaks

def verify_and_save(links):
    valid_links = []
    bot_name = os.getenv('MY_BOT_NAME', 'Collector')
    ua = {'User-Agent': 'ClashforWindows/0.19.0'}
    
    print(f"🧪 正在验证 {len(links)} 条源的活性...")
    
    for link in links:
        try:
            r = requests.get(link, headers=ua, timeout=5, stream=True)
            if r.status_code == 200 and len(r.raw.read(100)) > 30:
                valid_links.append(link)
        except:
            continue

    with open('github_leaks.txt', 'w', encoding='utf-8') as f:
        f.write(f"# === 来自机器人 [{bot_name}] 的捡漏结果 ===\n")
        f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        if valid_links:
            f.write('\n'.join(sorted(valid_links)))
        else:
            f.write("# 本轮未发现新鲜泄露。")

if __name__ == "__main__":
    links = get_github_leaks()
    verify_and_save(links)
