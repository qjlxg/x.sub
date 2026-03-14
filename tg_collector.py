import requests
import re
import logging
import csv
import html
import base64
import socket
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- 配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CHANNELS = [
    "dingyue_Center", "pgkj666", "anranbp", "hkaa0", "wxgqlfx", "freeVPNjd", "arzhecn", 
    "schpd", "jichang_list", "linux_do_channel", "nodeseekc", "hostloc_pro", 
    "serveruniverse", "sharecentrepro", "Impart_Cloud", "helingqi", "AI_News_CN",
    "Newlearner", "DocOfCard", "baipiao_ml", "jichangtuijian", "Airport_News", 
    "freemason6", "jichangbaipiao", "v2ray_configs_pool", "IP_CF_Config", "FreakConfig",
    "oneclickvpnkeys", "PrivateVPNs", "DirectVPN", "VlessConfig", "manVPN", "ELiV2RAY", 
    "Outline_Vpn", "V2rayNGX", "ccbaohe", "wangcai_8", "vpn_3000", "academi_vpn",
    "freedatazone1", "freev2rayi", "mypremium98", "inikotesla", "v2rayngalpha", 
    "v2rayngalphagamer", "jiedian_share", "vpn_mafia", "dr_v2ray", "bigsmoke_config",
    "vpn_443", "prossh", "mftizi", "qun521", "v2rayng_my2", "go4sharing", 
    "trand_farsi", "vpnplusee_free", "freekankan", "awxdy666"
]

PROTO_PATTERN = r"(?:vmess|vless|trojan|ss|ssr|hysteria|hysteria2|hy2)://[A-Za-z0-9+/=_.:\-?&%@#]+"
SUB_PATTERN = r"https?://[^\s<>\"'；]+?(?:sub|subscribe|api/v[1-9]|token)=[A-Za-z0-9\-]+"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}

# --- 功能函数 ---

def safe_decode(data):
    try:
        data = data.strip()
        missing_padding = len(data) % 4
        if missing_padding: data += '=' * (4 - missing_padding)
        return base64.b64decode(data).decode('utf-8', errors='ignore')
    except: return ""

def tcp_test(node_url):
    """简单的端口存活检测"""
    try:
        # 提取域名/IP和端口 (处理简单格式)
        content = node_url.split('://')[1]
        if '@' in content: content = content.split('@')[1]
        host_port = content.split('/')[0].split('?')[0]
        if ':' in host_port:
            host, port = host_port.rsplit(':', 1)
            with socket.create_connection((host, int(port)), timeout=2):
                return True
    except: pass
    return False

def extract_nodes(text):
    nodes = re.findall(PROTO_PATTERN, text)
    b64_blocks = re.findall(r"[A-Za-z0-9+/]{80,}", text)
    for block in b64_blocks:
        decoded = safe_decode(block)
        if "://" in decoded: nodes.extend(re.findall(PROTO_PATTERN, decoded))
    return [n.split('<')[0].split('"')[0].strip() for n in nodes if n]

def process_channel(channel):
    try:
        r = requests.get(f"https://t.me/s/{channel}", headers=HEADERS, timeout=10)
        if r.status_code != 200: return channel, []
        
        text = html.unescape(r.text)
        nodes = extract_nodes(text)
        
        # 尝试爬取订阅链接
        subs = set(re.findall(SUB_PATTERN, text))
        for sub in subs:
            sr = requests.get(sub, headers=HEADERS, timeout=10)
            if sr.status_code == 200:
                s_text = sr.text if "://" in sr.text else safe_decode(sr.text)
                nodes.extend(extract_nodes(s_text))
        return channel, list(set(nodes))
    except: return channel, []

# --- 主逻辑 ---

def main():
    raw_nodes = []
    stats = {}

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_channel, ch): ch for ch in CHANNELS}
        for f in tqdm(as_completed(futures), total=len(CHANNELS), desc="抓取频道"):
            ch, n = f.result()
            stats[ch] = len(n)
            raw_nodes.extend(n)

    unique_nodes = list(set(raw_nodes))
    logger.info(f"抓取完成，去重后共 {len(unique_nodes)} 个节点。开始存活检测...")

    # 并发测速
    valid_nodes = []
    with ThreadPoolExecutor(max_workers=50) as executor:
        future_to_node = {executor.submit(tcp_test, node): node for node in unique_nodes}
        for f in tqdm(as_completed(future_to_node), total=len(unique_nodes), desc="存活检测"):
            if f.result():
                valid_nodes.append(future_to_node[f])

    # 保存
    valid_nodes.sort()
    with open("tg_collector.txt", "w", encoding="utf-8") as f:
        f.write(f"# Total: {len(valid_nodes)}\n")
        f.writelines(f"{n}\n" for n in valid_nodes)

    with open("sub.txt", "w", encoding="utf-8") as f:
        f.write(base64.b64encode("\n".join(valid_nodes).encode()).decode())

    with open("tg_channel_stats.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["channel", "node_count"])
        for ch, count in stats.items():
            writer.writerow([ch, count])

    logger.info(f"全部完成！有效节点: {len(valid_nodes)}")

if __name__ == "__main__":
    main()
