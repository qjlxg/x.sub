import requests
import re
import os
import threading
import base64
import datetime
import logging
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

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

airport_list = []
extracted_domains = set() 
list_lock = threading.Lock()

def get_sub_status(url):
    """探测订阅链接的流量信息"""
    try:
        headers = {'User-Agent': 'v2rayNG/1.8.5'}
        r = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
        info = r.headers.get('subscription-userinfo')
        if info:
            parts = {m.group(1): int(m.group(2)) for m in re.finditer(r'(\w+)=(\d+)', info)}
            total = parts.get('total', 0) / (1024**3)
            used = (parts.get('upload', 0) + parts.get('download', 0)) / (1024**3)
            remain = total - used
            
            # 基础过滤：剩余流量不能小于等于 0
            if remain <= 0.01:
                return None
            
            # 时间过滤：如果已经过期，则过滤
            expire = parts.get('expire')
            if expire and expire < datetime.datetime.now().timestamp():
                return None
                
            return f" [剩余: {remain:.2f}GB / 总量: {total:.0f}GB]"
    except:
        pass
    return ""

def is_content_valid(text):
    """解码验证逻辑：不仅看是否有协议，还需看解开后的丰富度"""
    if not text or len(text) < 100: # 进一步提高最小字符门槛，过滤掉“OK”等简短响应
        return False
    
    protocols = ['vmess://', 'vless://', 'ss://', 'trojan://', 'ssr://', 'proxies:']
    
    # 1. 检查是否为明文
    if any(p in text for p in protocols):
        return True
        
    # 2. 尝试解码 Base64
    try:
        clean_text = re.sub(r'\s+', '', text)
        missing_padding = len(clean_text) % 4
        if missing_padding:
            clean_text += '=' * (4 - missing_padding)
            
        decoded = base64.b64decode(clean_text, validate=False).decode('utf-8', 'ignore')
        # 如果解码后的内容包含协议头，且长度也达到一定规模，才认为有效
        if any(p in decoded for p in protocols):
            return True
    except:
        pass
    return False

def url_check_valid(url, bar):
    global airport_list, extracted_domains
    try:
        # 提取主域名作为机场入口（不管订阅是否有效，只要域名合法就提取）
        parsed_url = urlparse(url)
        if parsed_url.netloc:
            with list_lock:
                extracted_domains.add(f"{parsed_url.scheme}://{parsed_url.netloc}")

        headers = {'User-Agent': 'v2rayNG/1.8.5'}
        # 获取完整内容进行多重校验
        r = requests.get(url, headers=headers, timeout=12, allow_redirects=True)
        
        if r.status_code == 200:
            content = r.text.strip()
            # 关键：内容长度必须足够，通常一个有效的节点包至少 300 字节以上
            if len(content) > 300 and is_content_valid(content):
                status_info = get_sub_status(url)
                if status_info is not None:
                    with list_lock:
                        airport_list.append(f"{url}{status_info}")
    except:
        pass
    finally:
        bar.update(1)

def write_url_config(url_file, url_list):
    logger.info(f"🚀 正在深度验证 {len(url_list)} 条发现的链接...")
    global airport_list
    airport_list = []
    bar = tqdm(total=len(url_list), desc="节点质量检测")
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        for url in url_list:
            executor.submit(url_check_valid, url, bar)
    bar.close()
    
    with open(url_file, 'w', encoding='utf-8') as f:
        f.write("# === 深度验证有效的订阅链接 (已包含大容量节点) ===\n")
        f.write(f"# 更新时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        # 汇总结果
        f.write('\n'.join(sorted(list(set(airport_list)))))

def fetch_tg_data():
    raw_domains = set()
    direct_subs = set()
    
    sub_pattern = re.compile(r'https?://[a-zA-Z0-9][-a-zA-Z0-9.]+\.[a-zA-Z]{2,10}/(?:api/v1/client/)?subscribe\?token=[a-zA-Z0-9]+')
    generic_sub = re.compile(r'https?://[a-zA-Z0-9][-a-zA-Z0-9.]+\.[a-zA-Z]{2,10}/sub\?token=[a-zA-Z0-9]+')
    domain_pattern = re.compile(r'https?://([a-zA-Z0-9][-a-zA-Z0-9]{0,62}(?:\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})+)')
    
    exclude_list = ['t.me', 'telegram.org', 'google.com', 'github.com', 'baidu.com', 'yandex.com']

    logger.info("📡 正在爬取各 Telegram 频道订阅源...")
    for channel in CHANNELS:
        url = f"https://t.me/s/{channel}"
        try:
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=12)
            if r.status_code == 200:
                subs = sub_pattern.findall(r.text) + generic_sub.findall(r.text)
                for s in subs:
                    direct_subs.add(s)
                
                found_domains = domain_pattern.findall(r.text)
                for d in found_domains:
                    d = d.lower()
                    if not any(ex in d for ex in exclude_list):
                        raw_domains.add(f"https://{d}")
        except:
            continue

    if direct_subs:
        write_url_config('tg_collector.txt', list(direct_subs))

    # 合并域名：正文域名 + 链接反推域名
    final_entrances = raw_domains.union(extracted_domains)
    
    if final_entrances:
        with open('airport_entrances.txt', 'w', encoding='utf-8') as f:
            f.write("# === 机场注册/登录入口汇集 (不管订阅是否有效均保留) ===\n")
            # 过滤掉非机场主机的干扰项
            clean_entrances = [d for d in final_entrances if not any(x in d for x in ['cdn.', 'oss.', 'github', 'ajax', 'static'])]
            f.write('\n'.join(sorted(clean_entrances)))
        logger.info(f"✅ 提取到 {len(clean_entrances)} 个机场主域名，存入 airport_entrances.txt")

if __name__ == "__main__":
    fetch_tg_data()
