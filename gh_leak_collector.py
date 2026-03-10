import requests
import re
import os
import time
from datetime import datetime, timedelta

# === 核心优化：关键词库升级 ===
SEARCH_QUERIES = [
    'path:/data/ filename:subscribe.txt',      # 针对特定路径
    '"is_suc":true "total": extension:txt',    # 针对脚本日志格式
    'filename:proxies.yaml "type: vmess"',     # 针对 Clash 配置文件
    'filename:config.json "outbounds" "vless"', # 针对原始 V2Ray 配置
    'sub_list "token=" extension:txt'          # 针对通用订阅清单
]

def get_github_leaks():
    leaks = set()
    token = os.getenv('GH_TOKEN')
    # 从变量读名字，但不写入文件，仅用于 Actions 日志
    bot_name = os.getenv('MY_BOT_NAME', 'GitHub_Collector')
    
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    # 稍微拉长一点时间窗口到 72 小时，对抗索引延迟
    time_cutoff = (datetime.utcnow() - timedelta(hours=72)).isoformat()
    
    print(f"🤖 机器人 [{bot_name}] 正在尝试“深海掘金”...")

    for query in SEARCH_QUERIES:
        search_url = f"https://api.github.com/search/code?q={query}+pushed:>{time_cutoff}"
        try:
            r = requests.get(search_url, headers=headers, timeout=15)
            if r.status_code == 200:
                items = r.json().get('items', [])
                print(f"🔎 关键词 [{query}] 命中 {len(items)} 个候选文件")
                for item in items:
                    raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    c_r = requests.get(raw_url, timeout=10)
                    if c_r.status_code == 200:
                        # 降低匹配门槛，捕获更多格式
                        found = re.findall(r'https?://[^\s<>"]+?token=[a-zA-Z0-9]{8,}', c_r.text)
                        for link in found:
                            if 'github' not in link: leaks.add(link)
            time.sleep(2) # 礼貌请求，避免 403
        except Exception as e:
            print(f"❌ 检索失败: {e}")
            
    return leaks

def verify_and_save(links):
    valid_links = []
    ua = {'User-Agent': 'ClashforWindows/0.19.0'}
    
    print(f"\n🧪 正在验证 {len(links)} 条潜在源...")
    for link in links:
        try:
            r = requests.get(link, headers=ua, timeout=5, stream=True)
            if r.status_code == 200:
                # 如果返回内容太小，可能是空订阅或报错信息
                if len(r.raw.read(100)) > 30:
                    valid_links.append(link)
        except:
            continue

    with open('github_leaks.txt', 'w', encoding='utf-8') as f:
        f.write(f"# === GitHub 自动捡漏结果 ===\n")
        f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        if valid_links:
            f.write('\n'.join(sorted(list(set(valid_links)))))
            print(f"🎉 成功！捡到 {len(valid_links)} 条活的订阅。")
        else:
            f.write("# 本轮搜索暂未匹配到有效链接。这可能是因为今日全网更新较少，请保持运行。")

if __name__ == "__main__":
    links = get_github_leaks()
    verify_and_save(links)
