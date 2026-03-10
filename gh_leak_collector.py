import requests
import re
import os
import time
from datetime import datetime, timedelta

# 精选的高转化率搜索关键词
SEARCH_QUERIES = [
    'vless sub token extension:txt',
    'vmess subscribe token extension:txt',
    'filename:proxies.yaml "vmess"',
    'filename:config.json "v2ray"',
    'sub_list "token="'
]

def get_github_leaks():
    leaks = set()
    token = os.getenv('GH_TOKEN')
    # 获取 Secret，如果是星号说明读取成功
    bot_name = os.getenv('MY_BOT_NAME', 'GitHub_Bot')
    
    # 将搜索范围扩大到最近 48 小时，确保一定有货
    search_hours = 48 
    
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    time_cutoff = (datetime.utcnow() - timedelta(hours=search_hours)).isoformat()
    
    # 注意：Secret 在打印到 GitHub Actions Log 时会被自动屏蔽为 ***
    print(f"🤖 机器人 [已读取机密] 正在启动全网检索...")
    print(f"🕒 追溯时间：过去 {search_hours} 小时")

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
                        # 兼容更多格式的 token 匹配
                        found = re.findall(r'https?://[^\s<>"]+?token=[a-zA-Z0-9]{8,}', c_r.text)
                        for link in found:
                            if 'github' not in link: 
                                leaks.add(link)
                print(f"✅ 关键词 [{query}]: 扫描到 {len(items)} 个相关文件")
            time.sleep(1.5) 
        except Exception as e:
            print(f"❌ 检索出错: {e}")
    return leaks, bot_name

def verify_and_save(links, bot_name):
    valid_links = []
    ua = {'User-Agent': 'ClashforWindows/0.19.0'}
    
    print(f"\n🧪 正在验证 {len(links)} 条订阅链接...")
    
    for link in links:
        try:
            r = requests.get(link, headers=ua, timeout=5, stream=True)
            if r.status_code == 200 and len(r.raw.read(100)) > 20:
                valid_links.append(link)
                print(f"💎 捡到有效订阅: {link[:40]}...")
        except:
            continue

    with open('github_leaks.txt', 'w', encoding='utf-8') as f:
        # 如果 Secret 是星号，在文件里我们也用这个占位，或者你可以手动在 Variables 里设一个公开的名字
        display_name = "Secret_Bot" if "***" in bot_name or not bot_name else bot_name
        f.write(f"# === 来自机器人 [{display_name}] 的捡漏结果 ===\n")
        f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        if valid_links:
            f.write('\n'.join(sorted(list(set(valid_links)))))
        else:
            f.write("# 本轮由于 GitHub 索引延迟，未发现新鲜有效链接。")

if __name__ == "__main__":
    links, name = get_github_leaks()
    verify_and_save(links, name)
