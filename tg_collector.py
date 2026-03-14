import requests
import re
import logging
import csv
import html
import base64
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- 基础配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# 包含以下关键词的订阅链接将被直接跳过，不爬取其节点
BLACKLIST_DOMAINS = [
    'mojie.app',
    'xn--ehqa22b.site',
    'subscribe002.awsy.top',
    'onlysub.mjurl.com',
    'ktm001.top',
    '52pokemon.yunjnet.com',
    'mojie.link'
]

CHANNELS = [
    # --- 搜索结果中的“白嫖/试用”大户 ---
    'dingyue_Center',    'pgkj666',          'anranbp',          'hkaa0',            
    'wxgqlfx',          'freeVPNjd',        'arzhecn',          'schpd',            
    'jichang_list',     'linux_do_channel', 'nodeseekc',        'hostloc_pro',      
    'serveruniverse',   'sharecentrepro',   'Impart_Cloud',     'helingqi',         
    'AI_News_CN',       'Newlearner',       'DocOfCard',        'baipiao_ml',       
    'jichangtuijian',   'Airport_News',     'freemason6',       'jichangbaipiao',   

    # --- 新增频道源 ---
    'v2ray_configs_pool', 'Gap_Mafiya',     'IP_CF_Config',     'FreakConfig',
    'oneclickvpnkeys',    'PrivateVPNs',    'DirectVPN',        'VlessConfig',
    'manVPN',             'ELiV2RAY',       'Outline_Vpn',      'PPT_f66_zHk2ZDY8',
    'V2rayNGX',           'ccbaohe',        'wangcai_8',        'vpn_3000',
    'academi_vpn',        'freedatazone1',  'freev2rayi',       'mypremium98',
    'inikotesla',         'v2rayngalpha',   'v2rayngalphagamer','jiedian_share',
    'vpn_mafia',          'dr_v2ray',       'allv2board',       'bigsmoke_config',
    'vpn_443',            'prossh',         'mftizi',           'qun521',
    'v2rayng_my2',        'go4sharing',     'trand_farsi',      'vpnplusee_free',
    'freekankan',         'awxdy666'
]

PROTO_PATTERN = r"(?:vmess|vless|trojan|ss|ssr|hysteria|hysteria2|hy2)://[A-Za-z0-9+/=_.:\-?&%@#]+"
SUB_PATTERN = r"https?://[^\s<>\"'；]+?(?:sub|subscribe|api/v\d/|token=|link/|/s/|/clash/|/v2ray/|/free/)[A-Za-z0-9\-\.=&?%/]+"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'}

def safe_decode(data):
    try:
        data = re.sub(r'\s+', '', data.strip())
        missing_padding = len(data) % 4
        if missing_padding: data += '=' * (4 - missing_padding)
        return base64.b64decode(data).decode('utf-8', errors='ignore')
    except: return ""

def extract_nodes_only(text):
    nodes = re.findall(PROTO_PATTERN, text)
    b64_blocks = re.findall(r"[A-Za-z0-9+/]{80,}", text)
    for block in b64_blocks:
        decoded = safe_decode(block)
        if "://" in decoded:
            nodes.extend(re.findall(PROTO_PATTERN, decoded))
    return [n.split('<')[0].split('"')[0].strip() for n in nodes if n]

def fetch_sub_content(sub_url):
    try:
        r = requests.get(sub_url, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            return [], False

        # 流量元数据校验
        user_info = r.headers.get('Subscription-Userinfo') or r.headers.get('subscription-userinfo')
        if user_info:
            info = dict(item.split('=') for item in user_info.split('; ') if '=' in item)
            upload = int(info.get('upload', 0))
            download = int(info.get('download', 0))
            total = int(info.get('total', 0))
            
            if total > 0 and (upload + download) >= total:
                return [], False

        content = r.text
        if "://" not in content:
            content = safe_decode(content)
        
        nodes = extract_nodes_only(content)
        if nodes:
            return nodes, True
            
    except:
        pass
    return [], False

def process_channel_only_subs(channel):
    try:
        r = requests.get(f"https://t.me/s/{channel}", headers=HEADERS, timeout=15)
        if r.status_code != 200: return channel, [], []
        
        text = html.unescape(r.text)
        sub_only_nodes = []
        valid_subs = []

        # 1. 扫描页面中的所有潜在订阅链接
        raw_subs = re.findall(SUB_PATTERN, text)
        
        # 2. 对每个链接进行过滤和校验
        for sub in set(raw_subs):
            clean_sub = sub.rstrip('.,;)')
            
            # --- 黑名单过滤逻辑 ---
            if any(domain in clean_sub for domain in BLACKLIST_DOMAINS):
                continue 
            # --------------------

            nodes_from_sub, is_valid = fetch_sub_content(clean_sub)
            if is_valid:
                sub_only_nodes.extend(nodes_from_sub)
                valid_subs.append(clean_sub)
                
        return channel, list(set(sub_only_nodes)), valid_subs
    except:
        return channel, [], []

def main():
    all_sub_nodes, all_valid_links, stats = [], [], {}
    logger.info("📡 模式：纯订阅链接节点提取 (域名过滤 + 流量校验)")

    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(process_channel_only_subs, ch): ch for ch in CHANNELS}
        for f in tqdm(as_completed(futures), total=len(CHANNELS), desc="抓取进度"):
            ch, n_list, s_list = f.result()
            stats[ch] = len(n_list)
            all_sub_nodes.extend(n_list)
            all_valid_links.extend(s_list)

    unique_nodes = sorted(list(set(all_sub_nodes)))
    unique_subs = sorted(list(set(all_valid_links)))

    # 保存结果
    with open("tg_collector.txt", "w", encoding="utf-8") as f:
        f.write(f"# 纯订阅源节点总数: {len(unique_nodes)}\n")
        f.writelines(f"{n}\n" for n in unique_nodes)
        
    with open("sub.txt", "w", encoding="utf-8") as f:
        f.write(base64.b64encode("\n".join(unique_nodes).encode()).decode())
        
    with open("valid_subs.txt", "w", encoding="utf-8") as f:
        f.writelines(f"{s}\n" for s in unique_subs)
        
    with open("tg_channel_stats.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["channel", "valid_sub_nodes"])
        for ch, count in stats.items():
            writer.writerow([ch, count])

    logger.info(f"✅ 提取完成！排除黑名单后总节点: {len(unique_nodes)}, 有效订阅数: {len(unique_subs)}")

if __name__ == "__main__":
    main()
