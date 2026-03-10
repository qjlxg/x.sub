import requests
import re
import os
import time
from datetime import datetime, timedelta

# 深度优化的捡漏关键词
SEARCH_QUERIES = [
    'vless sub token extension:txt',
    'vmess subscribe token extension:txt',
    'filename:proxies.yaml "type: vmess"',  # 捡漏 Clash 配置文件
    'path:v2ray filename:config.json',      # 捡漏 V2Ray 原始配置
    'filename:sub_list.txt "token="',       # 捡漏其他脚本生成的订阅清单
    '"is_suc":true "total"'                 # 某些测速脚本的运行日志
]

def get_github_leaks():
    leaks = set()
    token = os.getenv('GH_TOKEN')
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    # 只抓取最近 3 小时内变动的代码
    time_cutoff = (datetime.utcnow() - timedelta(hours=3)).isoformat()
    
    print(f"🕵️ 正在 GitHub 搜索过去 3 小时内的‘意外泄露’源...")

    for query in SEARCH_QUERIES:
        search_url = f"https://api.github.com/search/code?q={query}+pushed:>{time_cutoff}"
        try:
            r = requests.get(search_url, headers=headers, timeout=15)
            if r.status_code == 200:
                items = r.json().get('items', [])
                for item in items:
                    raw_url = item['html_url'].replace('github.com', '/').replace('/blob/', '/').replace('https://', 'https://raw.githubusercontent.com/')
                    
                    # 抓取内容提取链接
                    c_r = requests.get(raw_url, timeout=10)
                    if c_r.status_code == 200:
                        # 匹配订阅链接
                        found = re.findall(r'https?://[^\s<>"]+?token=[a-zA-Z0-9]{15,}', c_r.text)
                        # 同时也匹配原始节点（vmess:// 或 vless://）
                        raw_nodes = re.findall(r'(vmess://|vless://)[a-zA-Z0-9\+/=\-_@:\.]+', c_r.text)
                        
                        for link in found:
                            if 'github' not in link: leaks.add(link)
                        # 如果发现原始节点，也可以考虑记录（这里简单处理为打印）
                        if raw_nodes:
                            print(f"💡 发现 {len(raw_nodes)} 条原始节点信息")
                            
                print(f"✅ 关键词 [{query}]: 扫描完成")
            elif r.status_code == 403:
                print(f"⚠️ 速率受限，剩余配额不足。")
                break
            time.sleep(1.5) 
        except Exception as e:
            print(f"❌ 出错: {e}")

    return leaks

def verify_and_save(links):
    valid_links = []
    # 伪装流量指纹
    ua = {'User-Agent': 'ClashforWindows/0.19.0'}
    
    print(f"\n🧪 正在对 {len(links)} 条泄露源进行活性检测...")
    
    for link in links:
        try:
            # 只要能下发数据就算活的
            r = requests.get(link, headers=ua, timeout=5, stream=True)
            if r.status_code == 200:
                head = r.raw.read(300)
                if len(head) > 50:
                    valid_links.append(link)
        except:
            continue

    with open('github_leaks.txt', 'w', encoding='utf-8') as f:
        f.write(f"# GitHub 实时捡漏清单\n# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        if valid_links:
            f.write('\n'.join(sorted(valid_links)))
        else:
            f.write("# 暂未发现新鲜泄露，请保持脚本运行。")
    
    print(f"🎉 清理完毕，共捡到 {len(valid_links)} 条可用订阅。")

if __name__ == "__main__":
    links = get_github_leaks()
    verify_and_save(links)
