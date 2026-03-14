import requests
import re
import logging
import csv
import html
import base64
import binascii
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- 配置区 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CHANNELS = [
    "dingyue_Center", "pgkj666", "anranbp", "hkaa0", "wxgqlfx",
    "freeVPNjd", "arzhecn", "schpd", "jichang_list",
    "linux_do_channel", "nodeseekc", "hostloc_pro", "serveruniverse",
    "sharecentrepro", "Impart_Cloud", "helingqi", "AI_News_CN",
    "Newlearner", "DocOfCard", "baipiao_ml", "jichangtuijian",
    "Airport_News", "freemason6", "jichangbaipiao",
    "v2ray_configs_pool", "IP_CF_Config", "FreakConfig",
    "oneclickvpnkeys", "PrivateVPNs", "DirectVPN", "VlessConfig",
    "manVPN", "ELiV2RAY", "Outline_Vpn", "PPT_f66_zHk2ZDY8",
    "V2rayNGX", "ccbaohe", "wangcai_8", "vpn_3000", "academi_vpn",
    "freedatazone1", "freev2rayi", "mypremium98", "inikotesla",
    "v2rayngalpha", "v2rayngalphagamer", "jiedian_share",
    "vpn_mafia", "dr_v2ray", "allv2board", "bigsmoke_config",
    "vpn_443", "prossh", "mftizi", "qun521", "v2rayng_my2",
    "go4sharing", "trand_farsi", "vpnplusee_free",
    "freekankan", "awxdy666"
]

# 协议正则
REGEX_PROTOCOLS = r"(?:vmess|vless|trojan|ss|ssr|hysteria|hysteria2|hy2)://[A-Za-z0-9+/=_.:\-?&%@#]+"
# Base64特征正则 (通常长度大于50且包含特定字符)
REGEX_BASE64 = r"[A-Za-z0-9+/]{50,}"

# --- 核心功能区 ---

def safe_base64_decode(data):
    """尝试解码 Base64 字符串"""
    try:
        # 补齐长度
        missing_padding = len(data) % 4
        if missing_padding:
            data += '=' * (4 - missing_padding)
        return base64.b64decode(data).decode('utf-8', errors='ignore')
    except (binascii.Error, UnicodeDecodeError):
        return ""

def extract_nodes(text):
    """从文本中提取并清洗节点"""
    nodes = []
    # 1. 解码 HTML 转义符
    content = html.unescape(text)
    
    # 2. 直接提取协议链接
    found_urls = re.findall(REGEX_PROTOCOLS, content)
    nodes.extend(found_urls)
    
    # 3. 提取可能的 Base64 块并深度解析
    b64_blocks = re.findall(REGEX_BASE64, content)
    for block in b64_blocks:
        decoded = safe_base64_decode(block)
        if "://" in decoded:
            inner_nodes = re.findall(REGEX_PROTOCOLS, decoded)
            nodes.extend(inner_nodes)
            
    # 清洗：去除空行和重复，去掉末尾可能残留的 HTML 标签
    cleaned = {n.split('<')[0].strip() for n in nodes if n}
    return list(cleaned)

def fetch_channel(channel):
    """抓取单个频道的逻辑"""
    url = f"https://t.me/s/{channel}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        # 增加超时限制，防止卡死
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            nodes = extract_nodes(resp.text)
            return channel, nodes
    except Exception as e:
        logger.debug(f"Error fetching {channel}: {e}")
    return channel, []

def main():
    all_nodes_list = []
    stats = {}

    logger.info(f"🚀 开始抓取，目标频道数: {len(CHANNELS)}")

    # 并发抓取 (建议 max_workers 5-10 之间)
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_channel = {executor.submit(fetch_channel, ch): ch for ch in CHANNELS}
        
        for future in tqdm(as_completed(future_to_channel), total=len(CHANNELS), desc="抓取进度"):
            channel, nodes = future.result()
            stats[channel] = len(nodes)
            all_nodes_list.extend(nodes)

    # 全局去重
    unique_nodes = sorted(list(set(all_nodes_list)))

    # --- 输出保存 ---
    
    # 1. 保存明文列表 (tg_nodes.txt)
    with open("tg_nodes.txt", "w", encoding="utf-8") as f:
        f.write("# Total Nodes: " + str(len(unique_nodes)) + "\n")
        f.writelines(f"{n}\n" for n in unique_nodes)

    # 2. 保存 Base64 订阅格式 (sub.txt)
    with open("sub.txt", "w", encoding="utf-8") as f:
        sub_content = "\n".join(unique_nodes)
        b64_sub = base64.b64encode(sub_content.encode('utf-8')).decode('utf-8')
        f.write(b64_sub)

    # 3. 保存频道统计信息 (stats.csv)
    with open("tg_channel_stats.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["channel", "node_count"])
        for ch, count in stats.items():
            writer.writerow([ch, count])

    logger.info(f"✅ 抓取完成！")
    logger.info(f"📊 唯一节点总数: {len(unique_nodes)}")
    logger.info(f"📂 结果文件: tg_nodes.txt (明文), sub.txt (Base64订阅)")

if __name__ == "__main__":
    main()
