import requests
import re
import os
import time
from datetime import datetime, timedelta

# 深度优化的捡漏关键词：针对 Vless, Vmess, Clash 配置文件
SEARCH_QUERIES = [
    'vless sub token extension:txt',
    'vmess subscribe token extension:txt',
    'filename:proxies.yaml "type: vmess"',
    'path:v2ray filename:config.json'
]

def get_github_leaks():
    leaks = set()
    # 变量 1：系统内置 Secret，用于提高搜索配额
    token = os.getenv('GH_TOKEN')
    # 变量 2：用户定义的变量，仅用于日志显示
    bot_name = os.getenv('MY_BOT_NAME', 'GitHub_Collector')
    
    # 搜寻过去 48 小时内的代码，保证索引已经建立
    search_hours = 48 
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    time_cutoff = (datetime.utcnow() - timedelta(hours=search_hours)).isoformat()
    
    print(f"🤖 机器人 [{bot_name}] 正在全网检索 GitHub 泄露资源...")
    print(f"🕒 时间窗口：最近 {search_hours} 小时")

    for query in SEARCH_QUERIES:
        search_url = f"https://api.github.com/search/code?q={query}+pushed:>{time_cutoff}"
        try:
            r = requests.get(search_url, headers=headers, timeout=15)
            if r.status_code == 200:
                items = r.json().get('items', [])
                for item in items:
                    # 转换为原始文件下载地址
                    raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    c_r = requests.get(raw_url, timeout=10)
                    if c_r.status_code == 200:
                        # 匹配订阅链接
                        found = re.findall(r'https?://[^\s<>"]+?token=[a-zA-Z0-9]{10,}', c_r.text)
                        for link in found:
                            if 'github.com' not in link: 
                                leaks.add(link)
                print(f"✅ 关键词 [{query}]: 扫描完成")
            time.sleep(1.5) 
        except Exception as e:
            print(f"❌ 检索出错: {e}")
    return leaks

def verify_and_save(links):
    valid_links = []
    # 模拟 Clash 客户端，防止被机场拦截
    ua = {'User-Agent': 'ClashforWindows/0.19.0'}
    
    print(f"\n🧪 正在对搜集到的 {len(links)} 条源进行活性检测...")
    
    for link in links:
        try:
            # 探测链接是否有节点下发
            r = requests.get(link, headers=ua, timeout=5, stream=True)
            if r.status_code == 200:
                # 读取前 100 字节，确定不是空文件
                if len(r.raw.read(100)) > 30:
                    valid_links.append(link)
                    print(f"💎 捡到活的链接: {link[:40]}...")
        except:
            continue

    with open('github_leaks.txt', 'w', encoding='utf-8') as f:
        # ⚠️ 注意：这里绝对不写出环境变量，防止触发 Push Protection
        f.write(f"# === GitHub 自动捡漏结果 ===\n")
        f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        if valid_links:
            f.write('\n'.join(sorted(list(set(valid_links)))))
        else:
            f.write("# 本轮搜索暂未匹配到新鲜有效链接。")
    
    print(f"🎉 任务完成，共保存 {len(valid_links)} 条订阅。")

if __name__ == "__main__":
    links = get_github_leaks()
    verify_and_save(links)
