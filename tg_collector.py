import requests
import re
import logging
import csv
import html
import base64
import socket
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- 增强版配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 频道列表保持不变...
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
# 1. 节点协议正则
PROTO_PATTERN = r"(?:vmess|vless|trojan|ss|ssr|hysteria|hysteria2|hy2)://[A-Za-z0-9+/=_.:\-?&%@#]+"

# 2. 增强型订阅链接识别正则 (覆盖 V2Board, SSPanel, PHP 等各种格式)
SUB_PATTERN = r"https?://[^\s<>\"'；]+?(?:sub|subscribe|api/v\d/|token=|link/|/s/)[A-Za-z0-9\-\.=&?]+"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}

# --- 核心功能函数 ---

def safe_decode(data):
    """鲁棒性强的 Base64 解码"""
    data = data.strip()
    try:
        # 移除可能存在的空白符
        data = re.sub(r'\s+', '', data)
        missing_padding = len(data) % 4
        if missing_padding: data += '=' * (4 - missing_padding)
        return base64.b64decode(data).decode('utf-8', errors='ignore')
    except: return ""

def tcp_ping(node_url):
    """端口存活测试：判定节点是否有流量/存活"""
    try:
        parts = node_url.split('://')
        if len(parts) < 2: return False
        content = parts[1]
        if '@' in content: content = content.split('@')[1]
        host_port = content.split('/')[0].split('?')[0].split('#')[0]
        
        if ':' in host_port:
            host, port = host_port.rsplit(':', 1)
            with socket.create_connection((host, int(port)), timeout=2.5):
                return True
    except: pass
    return False

def fetch_and_parse_sub(sub_url):
    """深度探测：请求订阅地址并提取节点"""
    try:
        # 针对部分需要通过 https 访问的地址进行补全
        r = requests.get(sub_url, headers=HEADERS, timeout=12)
        if r.status_code == 200 and len(r.text) > 10:
            content = r.text.strip()
            # 自动识别 Base64 并解码
            if "://" not in content:
                content = safe_decode(content)
            
            # 从解码后的内容中提取所有节点
            return re.findall(PROTO_PATTERN, content)
    except: pass
    return []

def process_channel(channel):
    """处理单个频道"""
    try:
        r = requests.get(f"https://t.me/s/{channel}", headers=HEADERS, timeout=15)
        if r.status_code != 200: return channel, []
        
        raw_text = html.unescape(r.text)
        
        # 1. 提取页面明文节点
        found_nodes = re.findall(PROTO_PATTERN, raw_text)
        
        # 2. 提取订阅地址并逐个探测内部节点
        potential_subs = set(re.findall(SUB_PATTERN, raw_text))
        for sub in potential_subs:
            logger.info(f"正在探测订阅链接: {sub[:50]}...")
            nodes_from_sub = fetch_and_parse_sub(sub)
            if nodes_from_sub:
                found_nodes.extend(nodes_from_sub)
        
        return channel, list(set(found_nodes))
    except Exception as e:
        return channel, []

# --- 主逻辑 ---

def main():
    all_collected = []
    stats = {}

    # 多线程抓取频道 + 深度探测订阅
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_channel, ch): ch for ch in CHANNELS}
        for f in tqdm(as_completed(futures), total=len(CHANNELS), desc="频道扫描"):
            ch, nodes = f.result()
            stats[ch] = len(nodes)
            all_collected.extend(nodes)

    unique_nodes = list(set(all_collected))
    logger.info(f"探测完成。共发现 {len(unique_nodes)} 个潜在节点。开始存活验证...")

    # 多线程 TCP 验证 (过滤掉无流量/已过期的死节点)
    valid_nodes = []
    with ThreadPoolExecutor(max_workers=60) as v_executor:
        v_futures = {v_executor.submit(tcp_ping, n): n for n in unique_nodes}
        for f in tqdm(as_completed(v_futures), total=len(unique_nodes), desc="存活验证"):
            if f.result():
                valid_nodes.append(v_futures[f])

    # 结果保存
# 1. 保存明文列表
    with open("tg_collector.txt", "w", encoding="utf-8") as f:
        f.write(f"# Total: {len(valid_nodes)}\n")
        f.writelines(f"{n}\n" for n in valid_nodes)

    # 2. 保存订阅格式
    with open("sub.txt", "w", encoding="utf-8") as f:
        f.write(base64.b64encode("\n".join(valid_nodes).encode()).decode())

    # 3. 保存统计信息
    with open("tg_channel_stats.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["channel", "valid_nodes"])
        for ch, count in stats.items():
            writer.writerow([ch, count])

    logger.info(f"🎉 全部完成！有效节点总数: {len(valid_nodes)}")

if __name__ == "__main__":
    main()
