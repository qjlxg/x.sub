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

# 目标频道
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

# 协议与正则
PROTO_PATTERN = r"(?:vmess|vless|trojan|ss|ssr|hysteria|hysteria2|hy2)://[A-Za-z0-9+/=_.:\-?&%@#]+"
SUB_URL_PATTERN = r"https?://[^\s<>\"'；]+?(?:sub|subscribe|api/v[1-9]|token)=[A-Za-z0-9\-]+"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

# --- 功能函数 ---

def safe_decode(data):
    """通用 Base64 解码"""
    try:
        data = data.strip()
        missing_padding = len(data) % 4
        if missing_padding: data += '=' * (4 - missing_padding)
        return base64.b64decode(data).decode('utf-8', errors='ignore')
    except:
        return ""

def extract_from_text(text):
    """从纯文本中提取所有节点链接"""
    # 提取明文链接
    nodes = re.findall(PROTO_PATTERN, text)
    # 提取并解码 Base64 块
    b64_blocks = re.findall(r"[A-Za-z0-9+/]{50,}", text)
    for block in b64_blocks:
        decoded = safe_decode(block)
        if "://" in decoded:
            nodes.extend(re.findall(PROTO_PATTERN, decoded))
    return nodes

def fetch_content(url):
    """通用网页/链接请求"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            return r.text
    except:
        pass
    return ""

def process_channel(channel):
    """核心逻辑：处理单个频道"""
    raw_html = fetch_content(f"https://t.me/s/{channel}")
    if not raw_html: return channel, []
    
    clean_text = html.unescape(raw_html)
    found_nodes = extract_from_text(clean_text)
    
    # 进阶：尝试识别订阅链接并爬取（递归 1 层）
    sub_urls = re.findall(SUB_URL_PATTERN, clean_text)
    for sub in list(set(sub_urls)):
        sub_content = fetch_content(sub)
        if sub_content:
            # 如果订阅返回的是 Base64，先解码
            if "://" not in sub_content:
                sub_content = safe_decode(sub_content)
            found_nodes.extend(extract_from_text(sub_content))
            
    # 简单清洗节点末尾（去除 HTML 残留）
    final = [n.split('<')[0].split('"')[0].strip() for n in found_nodes if n]
    return channel, list(set(final))

# --- 主程序 ---

def main():
    all_results = []
    stats = {}

    logger.info("开始多线程深度抓取...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_channel, ch): ch for ch in CHANNELS}
        for f in tqdm(as_completed(futures), total=len(CHANNELS), desc="进度"):
            ch, nodes = f.result()
            stats[ch] = len(nodes)
            all_results.extend(nodes)

    # 全局去重与格式化
    unique_nodes = sorted(list(set(all_results)))

    # 保存文件
    with open("tg_nodes.txt", "w", encoding="utf-8") as f:
        f.write(f"# Updated: 2026-01-24\n# Total: {len(unique_nodes)}\n")
        f.writelines(f"{n}\n" for n in unique_nodes)

    with open("sub.txt", "w", encoding="utf-8") as f:
        content = "\n".join(unique_nodes)
        f.write(base64.b64encode(content.encode()).decode())

    with open("tg_channel_stats.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["channel", "node_count"])
        for ch, count in stats.items():
            writer.writerow([ch, count])

    logger.info(f"抓取完毕！共获得 {len(unique_nodes)} 个唯一节点。")

if __name__ == "__main__":
    main()
