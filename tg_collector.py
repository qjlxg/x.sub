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

# 协议与订阅正则
PROTO_PATTERN = r"(?:vmess|vless|trojan|ss|ssr|hysteria|hysteria2|hy2)://[A-Za-z0-9+/=_.:\-?&%@#]+"
# 识别订阅链接（支持常见 API 格式）
SUB_URL_PATTERN = r"https?://[^\s<>\"'；]+?(?:sub|subscribe|api/v[1-9]|token)=[A-Za-z0-9\-]+"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

# --- 工具函数 ---

def safe_decode(data):
    """尝试 Base64 解码"""
    try:
        data = data.strip()
        missing_padding = len(data) % 4
        if missing_padding: data += '=' * (4 - missing_padding)
        return base64.b64decode(data).decode('utf-8', errors='ignore')
    except:
        return ""

def extract_nodes(text):
    """从文本中深度提取节点"""
    nodes = []
    # 直接匹配协议
    nodes.extend(re.findall(PROTO_PATTERN, text))
    # 匹配长 Base64 字符串（可能是节点集）
    b64_blocks = re.findall(r"[A-Za-z0-9+/]{80,}", text)
    for block in b64_blocks:
        decoded = safe_decode(block)
        if "://" in decoded:
            nodes.extend(re.findall(PROTO_PATTERN, decoded))
    return nodes

def fetch_url(url):
    """安全请求 URL"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            return r.text
    except:
        return ""
    return ""

def process_channel(channel):
    """处理单个频道：包含网页提取和订阅链接二次爬取"""
    url = f"https://t.me/s/{channel}"
    html_content = fetch_url(url)
    if not html_content:
        return channel, []

    # 1. 解码 HTML 实体并初步提取
    clean_text = html.unescape(html_content)
    nodes = extract_nodes(clean_text)

    # 2. 深度挖掘：识别并爬取订阅链接
    sub_urls = set(re.findall(SUB_URL_PATTERN, clean_text))
    for sub_url in sub_urls:
        sub_raw = fetch_url(sub_url)
        if sub_raw:
            # 订阅链接通常返回 Base64 或明文列表
            if "://" not in sub_raw:
                sub_raw = safe_decode(sub_raw)
            nodes.extend(extract_nodes(sub_raw))

    # 清洗：去除残留标签、去重
    cleaned_nodes = list(set([n.split('<')[0].split('"')[0].strip() for n in nodes if n]))
    return channel, cleaned_nodes

# --- 执行主逻辑 ---

def main():
    all_collected = []
    stats = {}

    logger.info(f"开始抓取 {len(CHANNELS)} 个频道...")

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(process_channel, ch): ch for ch in CHANNELS}
        for f in tqdm(as_completed(futures), total=len(CHANNELS), desc="抓取中"):
            ch, nodes = f.result()
            stats[ch] = len(nodes)
            all_collected.extend(nodes)

    # 全局去重并排序
    unique_nodes = sorted(list(set(all_collected)))

    # 1. 保存明文列表
    with open("tg_collector.txt", "w", encoding="utf-8") as f:
        f.write(f"# Total Nodes: {len(unique_nodes)}\n")
        f.writelines(f"{n}\n" for n in unique_nodes)

    # 2. 保存 Base64 订阅格式
    with open("sub.txt", "w", encoding="utf-8") as f:
        encoded = base64.b64encode("\n".join(unique_nodes).encode()).decode()
        f.write(encoded)

    # 3. 保存统计信息
    with open("tg_channel_stats.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["channel", "node_count"])
        for ch, count in stats.items():
            writer.writerow([ch, count])

    logger.info(f"任务完成。唯一节点总数: {len(unique_nodes)}")

if __name__ == "__main__":
    main()
