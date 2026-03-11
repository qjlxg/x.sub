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
    
    # --- 搜索结果中的“互推与聚合源（从搜索预览的转发中提取） ---
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
    """深度流量探测：物理过滤负数流量和超配额订阅"""
    try:
        headers = {'User-Agent': 'v2rayNG/1.8.5'}
        r = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
        info = r.headers.get('subscription-userinfo')
        if info:
            # 使用改进的正则匹配，支持负数捕获
            parts = {m.group(1): int(m.group(2)) for m in re.finditer(r'(\w+)=([-]?\d+)', info)}
            total = parts.get('total', 0)
            upload = parts.get('upload', 0)
            download = parts.get('download', 0)
            expire = parts.get('expire')

            # 逻辑：总流量为负，或者已用流量超过总流量，直接判定为无效
            used = upload + download
            if total <= 0 or used >= total:
                return None
            
            remain_bytes = total - used
            if remain_bytes < 100 * 1024 * 1024: # 剩余不足 100MB 视为废弃
                return None

            # 过期检查
            if expire and 0 < expire < datetime.datetime.now().timestamp():
                return None
                
            return f" [剩余: {remain_bytes/(1024**3):.2f}GB / 总量: {total/(1024**3):.0f}GB]"
    except:
        pass
    return ""

def is_content_valid(text):
    """验证内容是否真的含有可用节点，排除“流量耗尽”提示"""
    if not text or len(text) < 300: 
        return False
    
    protocols = ['vmess://', 'vless://', 'ss://', 'trojan://', 'ssr://', 'proxies:']
    trash_keywords = ['流量耗尽', '过期', '续费', '账户禁用', 'Traffic Used Up', 'Expired', '超过限制']
    
    try:
        clean_text = re.sub(r'\s+', '', text)
        missing_padding = len(clean_text) % 4
        if missing_padding:
            clean_text += '=' * (4 - missing_padding)
        decoded = base64.b64decode(clean_text, validate=False).decode('utf-8', 'ignore')
        
        # 检查是否包含节点协议
        if any(p in decoded for p in protocols):
            # 统计包含协议的行数，如果解开后只有 1-2 行且含垃圾词，判定无效
            if any(k in decoded for k in trash_keywords):
                if decoded.count('://') < 3: 
                    return False
            return True
    except:
        # 明文格式（Clash等）检查
        if any(p in text for p in protocols):
            return True
    return False

def url_check_valid(url, bar):
    global airport_list, extracted_domains
    try:
        # 无论订阅是否有效，只要是机场域名就提取到入口文件
        parsed_url = urlparse(url)
        if parsed_url.netloc:
            with list_lock:
                extracted_domains.add(f"{parsed_url.scheme}://{parsed_url.netloc}")

        headers = {'User-Agent': 'v2rayNG/1.8.5'}
        r = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        
        if r.status_code == 200:
            content = r.text.strip()
            # 执行内容真实性验证
            if is_content_valid(content):
                status_info = get_sub_status(url)
                if status_info: 
                    with list_lock:
                        airport_list.append(f"{url}{status_info}")
    except:
        pass
    finally:
        bar.update(1)

def write_url_config(url_file, url_list):
    logger.info(f"🚀 正在针对性清洗 {len(url_list)} 条发现的链接...")
    global airport_list
    airport_list = []
    bar = tqdm(total=len(url_list), desc="质量验证")
    # 并发数保持在 10，避免频繁请求被暂时封禁 IP
    with ThreadPoolExecutor(max_workers=10) as executor:
        for url in url_list:
            executor.submit(url_check_valid, url, bar)
    bar.close()
    
    with open(url_file, 'w', encoding='utf-8') as f:
        f.write("# === 深度清洗：剔除负数、过期及流量耗尽链接 ===\n")
        f.write(f"# 更新时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write('\n'.join(sorted(list(set(airport_list)))))

def fetch_tg_data():
    raw_domains = set()
    direct_subs = set()
    
    sub_pattern = re.compile(r'https?://[a-zA-Z0-9][-a-zA-Z0-9.]+\.[a-zA-Z]{2,10}/(?:api/v1/client/)?subscribe\?token=[a-zA-Z0-9]+')
    generic_sub = re.compile(r'https?://[a-zA-Z0-9][-a-zA-Z0-9.]+\.[a-zA-Z]{2,10}/sub\?token=[a-zA-Z0-9]+')
    domain_pattern = re.compile(r'https?://([a-zA-Z0-9][-a-zA-Z0-9]{0,62}(?:\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})+)')
    
    exclude_list = ['t.me', 'telegram.org', 'google.com', 'github.com', 'baidu.com', 'yandex.com']

    logger.info("📡 正在爬取频道订阅源（保持原始频道注释逻辑）...")
    for channel in CHANNELS:
        url = f"https://t.me/s/{channel}"
        try:
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=12)
            if r.status_code == 200:
                # 提取订阅链接
                subs = sub_pattern.findall(r.text) + generic_sub.findall(r.text)
                for s in subs: direct_subs.add(s)
                # 提取潜在域名
                found_domains = domain_pattern.findall(r.text)
                for d in found_domains:
                    d = d.lower()
                    if not any(ex in d for ex in exclude_list): raw_domains.add(f"https://{d}")
        except: continue

    if direct_subs:
        write_url_config('tg_collector.txt', list(direct_subs))

    # 合并：正文域名 + 订阅链接域名
    final_entrances = raw_domains.union(extracted_domains)
    if final_entrances:
        with open('airport_entrances.txt', 'w', encoding='utf-8') as f:
            f.write("# === 机场入口库汇总 ===\n")
            clean_entrances = [d for d in final_entrances if not any(x in d for x in ['cdn.', 'oss.', 'github', 'ajax', 'static'])]
            f.write('\n'.join(sorted(clean_entrances)))
        logger.info(f"✅ 提取完成！")

if __name__ == "__main__":
    fetch_tg_data()
