import requests
import re
import os
import threading
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    'jichangbaipiao',   # 机场白嫖（基础库）

    # --- 新增频道源 ---
    'v2ray_configs_pool',
    'IP_CF_Config',
    'FreakConfig',
    'oneclickvpnkeys',
    'PrivateVPNs',
    'DirectVPN',
    'VlessConfig',
    'manVPN',
    'ELiV2RAY',
    'Outline_Vpn',
    'PPT_f66_zHk2ZDY8',
    'V2rayNGX',
    'ccbaohe',
    'wangcai_8',
    'vpn_3000',
    'academi_vpn',
    'freedatazone1',
    'freev2rayi',
    'mypremium98',
    'inikotesla',
    'v2rayngalpha',
    'v2rayngalphagamer',
    'jiedian_share',
    'vpn_mafia',
    'dr_v2ray',
    'allv2board',
    'bigsmoke_config',
    'vpn_443',
    'prossh',
    'mftizi',
    'qun521',
    'v2rayng_my2',
    'go4sharing',
    'trand_farsi',
    'vpnplusee_free',
    'freekankan',
    'awxdy666'
]

# 全员变量用于存储有效结果
airport_list = []
list_lock = threading.Lock()

def get_sub_status(url):
    """探测订阅链接的剩余流量和有效期"""
    try:
        headers = {'User-Agent': 'ClashforWindows/0.19.0'}
        r = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
        info = r.headers.get('subscription-userinfo')
        if info:
            parts = {m.group(1): int(m.group(2)) for m in re.finditer(r'(\w+)=(\d+)', info)}
            total = parts.get('total', 0) / (1024**3)
            used = (parts.get('upload', 0) + parts.get('download', 0)) / (1024**3)
            remain = total - used
            return f" [剩余: {remain:.2f}GB / 总量: {total:.0f}GB]"
    except:
        pass
    return ""

def url_check_valid(target, url, bar):
    """检测单个URL是否有效并存入列表"""
    global airport_list
    try:
        headers = {'User-Agent': 'ClashforWindows/0.19.0'}
        # 使用 HEAD 请求快速检测
        r = requests.head(url, headers=headers, timeout=8, allow_redirects=True)
        if r.status_code == 200:
            status_info = get_sub_status(url)
            with list_lock:
                airport_list.append(f"{url}{status_info}")
    except:
        pass
    finally:
        bar.update(1)

def write_url_config(url_file, url_list, target):
    """执行多线程检测并写入文件"""
    logger.info(f'🚀 开始检测 {target} 订阅节点有效性 (共 {len(url_list)} 条)')
    
    global airport_list
    airport_list = [] # 重置列表

    bar = tqdm(total=len(url_list), desc=f'{target}检测')
    
    # 使用线程池控制并发，避免瞬间压力过大
    with ThreadPoolExecutor(max_workers=15) as executor:
        for url in url_list:
            executor.submit(url_check_valid, target, url, bar)
            
    bar.close()
    
    # 处理路径替换逻辑
    final_file = url_file.replace('sub_store', target) if 'sub_store' in url_file else f"{target}_{url_file}"
    
    write_str = '\n'.join(airport_list)
    with open(final_file, 'w', encoding='utf-8') as f:
        f.write(f"# === {target} 有效节点汇总 ===\n")
        f.write(write_str)
    
    logger.info(f'✅ {target} 检测完成，有效节点已保存至: {final_file}')

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
            headers = {'User-Agent': 'Mozilla/5.0'}
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
                
                print(f"✅ 频道 [{channel}]: 提取到 {len(subs)} 条直接订阅")
        except Exception as e:
            print(f"❌ 频道 {channel} 抓取失败: {e}")

    # --- 关键：合并原有保存逻辑与新检测逻辑 ---
    if direct_subs:
        # 调用你要求的检测函数
        write_url_config('tg_collector.txt', list(direct_subs), 'valid_subs')

    if all_domains:
        with open('airport_entrances.txt', 'w', encoding='utf-8') as f:
            f.write("# === 机场注册入口 ===\n")
            f.write('\n'.join(sorted(list(all_domains))))

    print(f"\n✨ 任务全部完成！")

if __name__ == "__main__":
    fetch_tg_data()
