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

# 节点协议正则
PROTO_PATTERN = r"(?:vmess|vless|trojan|ss|ssr|hysteria|hysteria2|hy2)://[A-Za-z0-9+/=_.:\-?&%@#]+"
# 订阅地址正则 (匹配常见订阅格式)
SUB_PATTERN = r"https?://[^\s<>\"'；]+?(?:sub|subscribe|api/v[1-9]|token)=[A-Za-z0-9\-\.]+"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}

# --- 功能函数 ---

def safe_decode(data):
    """Base64 容错解码"""
    try:
        data = data.strip()
        missing_padding = len(data) % 4
        if missing_padding: data += '=' * (4 - missing_padding)
        return base64.b64decode(data).decode('utf-8', errors='ignore')
    except: return ""

def extract_nodes_from_text(text):
    """从文本中提取节点链接"""
    # 1. 提取直接明文
    nodes = re.findall(PROTO_PATTERN, text)
    # 2. 识别长 Base64 块并解码提取
    b64_blocks = re.findall(r"[A-Za-z0-9+/]{80,}", text)
    for block in b64_blocks:
        decoded = safe_decode(block)
        if "://" in decoded:
            nodes.extend(re.findall(PROTO_PATTERN, decoded))
    return [n.split('<')[0].split('"')[0].strip() for n in nodes if n]

def fetch_sub_content(sub_url):
    """测试读取订阅地址内容，返回提取到的节点列表"""
    try:
        r = requests.get(sub_url, headers=HEADERS, timeout=10)
        if r.status_code == 200 and r.text.strip():
            content = r.text
            # 订阅链接通常返回 Base64，尝试解码
            if "://" not in content:
                content = safe_decode(content)
            return extract_nodes_from_text(content)
    except Exception as e:
        logger.debug(f"订阅地址无效: {sub_url} -> {e}")
    return []

def process_channel(channel):
    """处理频道：抓取页面 -> 提取节点 -> 探测订阅链接"""
    try:
        r = requests.get(f"https://t.me/s/{channel}", headers=HEADERS, timeout=12)
        if r.status_code != 200: return channel, []
        
        text = html.unescape(r.text)
        # 提取页面上的明文节点
        channel_nodes = extract_nodes_from_text(text)
        
        # 提取并测试页面上的订阅地址
        subs = set(re.findall(SUB_PATTERN, text))
        for sub in subs:
            # 关键：不仅保存，还要读取内容
            nodes_from_sub = fetch_sub_content(sub)
            if nodes_from_sub:
                channel_nodes.extend(nodes_from_sub)
                
        return channel, list(set(channel_nodes))
    except:
        return channel, []

# --- 主逻辑 ---

def main():
    all_raw_nodes = []
    stats = {}

    logger.info("📡 开始深度探测模式抓取...")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_channel, ch): ch for ch in CHANNELS}
        for f in tqdm(as_completed(futures), total=len(CHANNELS), desc="频道进度"):
            ch, n_list = f.result()
            stats[ch] = len(n_list)
            all_raw_nodes.extend(n_list)

    # 全局去重
    unique_nodes = sorted(list(set(all_raw_nodes)))

    # 保存结果
    with open("tg_collector.txt", "w", encoding="utf-8") as f:
        f.write(f"# Updated: 2026-03-14\n# Total Valid Nodes: {len(unique_nodes)}\n")
        f.writelines(f"{n}\n" for n in unique_nodes)

    with open("sub.txt", "w", encoding="utf-8") as f:
        f.write(base64.b64encode("\n".join(unique_nodes).encode()).decode())

    with open("tg_channel_stats.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["channel", "valid_node_count"])
        for ch, count in stats.items():
            writer.writerow([ch, count])

    logger.info(f"✅ 抓取完毕！共获得 {len(unique_nodes)} 个活跃节点。")

if __name__ == "__main__":
    main()
