import requests
import re
import os
from urllib.parse import urlparse

CHANNELS = [
    # --- 搜索结果中的“白嫖/试用”大户 ---
    'dingyue_Center',    # 订阅分享中心（流量之王）
    'pgkj666',          # 白嫖分享社（0元优惠码基地）
    'anranbp',          # 我爱白嫖（无需验证、反复注册）
    'hkaa0',            # 五叶TG节点（1.95T超大流量）
    'wxgqlfx',          # 翻墙世界的梯子（100G/月，0元购）
    'freeVPNjd',        # 免费高速订阅节点（含专属优惠码）
    'arzhecn',          # 一群🐂🐎的机场（新站首发地）
    'schpd',            # 山茶花の机场频道（七喜机场等实测源）
    'jichang_list',
    
    # --- 搜索结果中的“技术/中转/号商”源 ---
    'linux_do_channel', # LINUX DO（技术大佬、号商进货）
    'nodeseekc',        # NodeSeek（新站开业、各种云主机试用）
    'hostloc_pro',      # HostlocPro（各种1元试用、余额赠送）
    'serveruniverse',   # 机界（300$体验金等高价值信息）
    
    # --- 互推与聚合源（从搜索预览的转发中提取） ---
    'sharecentrepro',   # SCP（每日免费节点、2PB订阅链接）
    'Impart_Cloud',     # Impart（稀有地区、转运公司送余额）
    'helingqi',         # 禾令奇Club（各种大会员/机场试用）
    'AI_News_CN',       # AI新闻（伴生大量Gemini/ChatGPT试用）
    'Newlearner',       # 自留地（虽然是大站，但偶尔有顶级Pro试用）
    'DocOfCard',        # 卡粉订阅（支付指纹、漫游WiFi试用）
    'baipiao_ml',       # 白嫖ML（专注订阅链接搬运）
    'jichangtuijian',   # 机场推荐（带实测数据）
    'Airport_News',     # 机场动态（全网新开业监控）
    'freemason6',       # 机场观测（白嫖无罪，0元包）
    'jichangbaipiao'    # 机场白嫖（基础库）
]

def get_sub_status(url):
    """新增：探测订阅链接的剩余流量和有效期"""
    try:
        # 必须模拟机场常用客户端头，否则会被拦截
        headers = {'User-Agent': 'ClashforWindows/0.19.0'}
        r = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
        # 获取面板返回的流量信息头
        info = r.headers.get('subscription-userinfo')
        if info:
            # 数据解析: upload=xxx; download=xxx; total=xxx; expire=xxx
            parts = dict(item.split('=') for item in info.split('; '))
            total = int(parts.get('total', 0)) / (1024**3)
            used = (int(parts.get('upload', 0)) + int(parts.get('download', 0))) / (1024**3)
            remain = total - used
            # 如果有过期时间，转换成天数（可选）
            return f" [剩余: {remain:.2f}GB / 总量: {total:.0f}GB]"
    except:
        pass
    return ""

def fetch_tg_data():
    all_domains = set()
    direct_subs = set()
    
    sub_pattern = re.compile(r'https?://[a-zA-Z0-9][-a-zA-Z0-9.]+\.[a-zA-Z]{2,10}/(?:api/v1/client/)?subscribe\?token=[a-zA-Z0-9]+')
    generic_sub = re.compile(r'https?://[a-zA-Z0-9][-a-zA-Z0-9.]+\.[a-zA-Z]{2,10}/sub\?token=[a-zA-Z0-9]+')
    domain_pattern = re.compile(r'https?://([a-zA-Z0-9][-a-zA-Z0-9]{0,62}(?:\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})+)')
    
    exclude_list = ['t.me', 'telegram.org', 'google.com', 'github.com', 'baidu.com', 'yandex.com', 'v2ray', 'clash']

    print("📡 正在深度扫描频道中的注册入口与直接订阅链接...")

    for channel in CHANNELS:
        url = f"https://t.me/s/{channel}"
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                subs = sub_pattern.findall(r.text) + generic_sub.findall(r.text)
                for s in subs:
                    direct_subs.add(s)
                
                found_domains = domain_pattern.findall(r.text)
                for d in found_domains:
                    d = d.lower()
                    if not any(ex in d for ex in exclude_list):
                        all_domains.add(f"https://{d}")
                
                print(f"✅ 频道 [{channel}]: 提取到 {len(subs)} 条直接订阅, {len(found_domains)} 个域名")
        except Exception as e:
            print(f"❌ 频道 {channel} 抓取失败: {e}")

    output_file = 'tg_collector.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        if direct_subs:
            f.write("# === 直接可用订阅链接 (带流量探测) ===\n")
            # 探测每个订阅链接的状态
            for s in sorted(list(direct_subs)):
                status = get_sub_status(s)
                f.write(f"{s}{status}\n")
            f.write('\n')
        
        if all_domains:
            f.write("# === 机场注册入口 ===\n")
            f.write('\n'.join(sorted(list(all_domains))))
            f.write('\n')
            
    print(f"\n✨ 任务完成！共保存 {len(direct_subs)} 条直连订阅和 {len(all_domains)} 个注册入口。")

if __name__ == "__main__":
    fetch_tg_data()
