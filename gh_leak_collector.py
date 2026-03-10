import requests
import re
import os
import time
from datetime import datetime, timedelta

# 深度优化的捡漏关键词，专门针对“意外泄露”
SEARCH_QUERIES = [
    'vless sub token extension:txt',
    'vmess subscribe token extension:txt',
    'filename:proxies.yaml "type: vmess"',      # Clash 配置文件泄露
    'path:v2ray filename:config.json',          # V2Ray 原始配置泄露
    'filename:sub_list.txt "token="',           # 其他脚本的运行输出
    '"is_suc":true "total"'                     # 机场测速日志
]

def get_github_leaks():
    leaks = set()
    token = os.getenv('GH_TOKEN')
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    # 抓取最近 4 小时内变动的代码
    time_cutoff = (datetime.utcnow() - timedelta(hours=4)).isoformat()
    
    print(f"🕵️ 正在全网检索 GitHub 过去 4 小时内的‘意外泄露’资源...")

    for query in SEARCH_QUERIES:
        # 添加推送时间过滤
        search_url = f"https://api.github.com/search/code?q={query}+pushed:>{time_cutoff}"
        try:
            r = requests.get(search_url, headers=headers, timeout=15)
            if r.status_code == 200:
                items = r.json().get('items', [])
                for item in items:
                    # 转换 Raw URL
                    raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    
                    c_r = requests.get(raw_url, timeout=10)
                    if c_r.status_code == 200:
                        # 匹配通用订阅链接
                        found = re.findall(r'https?://[^\s<>"]+?token=[a-zA-Z0-9]{15,}', c_r.text)
                        for link in found:
                            if 'github' not in link: 
                                leaks.add(link)
                                
                print(f"✅ 关键词 [{query}]: 扫描完成")
            elif r.status_code == 403:
                print(f"⚠️ 触发 API 速率限制，请等待下一个周期。")
                break
            time.sleep(2) 
        except Exception as e:
            print(f"❌ 出错: {e}")

    return leaks

def verify_and_save(links):
    valid_links = []
    # 伪装流量指纹，极其重要！
    ua = {'User-Agent': 'ClashforWindows/0.19.0'}
    
    print(f"\n🧪 正在对 {len(links)} 条源进行活性探测...")
    
    for link in links:
        try:
            # HEAD 请求探测即可
            r = requests.get(link, headers=ua, timeout=5, stream=True)
            if r.status_code == 200:
                # 检查是否真的有内容返回
                if len(r.raw.read(100)) > 30:
                    valid_links.append(link)
        except:
            continue

    with open('github_leaks.txt', 'w', encoding='utf-8') as f:
        f.write(f"# === GitHub 实时捡漏清单 ===\n")
        f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        if valid_links:
            f.write('\n'.join(sorted(valid_links)))
        else:
            f.write("# 暂未发现新鲜泄露。")
    
    print(f"🎉 捡漏结束，共计获得 {len(valid_links)} 条可用地址。")

if __name__ == "__main__":
    links = get_github_leaks()
    verify_and_save(links)
