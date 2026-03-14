import requests
import re
import logging
import csv
import html
import base64
import socket
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- 锁定配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 增强版频道列表 ---
CHANNELS = [
    # --- 原有核心频道 ---
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
    "trand_farsi", "vpnplusee_free", "freekankan", "awxdy666",

    # --- 新增：高速订阅与全能分享类 ---
    "V2rayClashNode",      # 每日更新大量 Clash/V2Ray 订阅
    "SSR_V2RAY_Clash",     # 长期稳定的节点分享
    "v2cross",             # 包含大量订阅链接地址
    "VlessConfigPool",     # 专注 Vless 协议
    "Shadowrocket_VN",     # 越南活跃频道，节点存活率高
    "Gfwh_Sub",            # 节点订阅源整合
    "NodeFree",            # 每日自动推送节点列表
    "Clash_V2ray_Node",    # 综合节点池
    
    # --- 新增：大厂与技术宅自建类 ---
    "i_v2ray",             # 老牌节点分享频道
    "free_ss",             # 专注于 SS 协议
    "v2ray_vpn_free",      # 包含大量 Base64 订阅块
    "ssrList",             # SSR 与 V2 订阅汇总
    "v2free_node",         # 每日多时段更新
    "ClashNode_Free",      # 专注于 Clash 订阅转换链接
    "Tizi_Share",          # 综合性梯子分享
    "Link_Vless_Nodes",    # 纯净 Vless 协议源

    # --- 新增：海外与聚合资源类 ---
    "FreeNode_List",       # 自动采集全网公开节点
    "DailyNode_Update",    # 每日凌晨固定更新
    "V2Ray_Shadowrocket",  # 小火箭专用订阅
    "One_Node_One_World",  # 节点质量较高
    "Fast_V2ray_Nodes"     # 专注于低延迟节点
]
PROTO_PATTERN = r"(?:vmess|vless|trojan|ss|ssr|hysteria|hysteria2|hy2)://[A-Za-z0-9+/=_.:\-?&%@#]+"
SUB_PATTERN = r"https?://[^\s<>\"'；]+?(?:sub|subscribe|api/v[1-9]|token=|link/|/s/)[A-Za-z0-9\-\.=&?]+"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}

# --- 功能函数 ---

def safe_decode(data):
    try:
        data = re.sub(r'\s+', '', data.strip())
        missing_padding = len(data) % 4
        if missing_padding: data += '=' * (4 - missing_padding)
        return base64.b64decode(data).decode('utf-8', errors='ignore')
    except: return ""

def extract_nodes(text):
    nodes = re.findall(PROTO_PATTERN, text)
    b64_blocks = re.findall(r"[A-Za-z0-9+/]{80,}", text)
    for block in b64_blocks:
        decoded = safe_decode(block)
        if "://" in decoded: nodes.extend(re.findall(PROTO_PATTERN, decoded))
    return [n.split('<')[0].split('"')[0].strip() for n in nodes if n]

def fetch_sub_content(sub_url):
    """测试订阅地址：返回 (提取到的节点列表, 是否有效)"""
    try:
        r = requests.get(sub_url, headers=HEADERS, timeout=10)
        if r.status_code == 200 and len(r.text) > 10:
            content = r.text
            if "://" not in content: content = safe_decode(content)
            nodes = extract_nodes(content)
            return nodes, True if nodes else False
    except: pass
    return [], False

def process_channel(channel):
    """处理频道：返回 (频道名, 节点列表, 有效订阅链接列表)"""
    try:
        r = requests.get(f"https://t.me/s/{channel}", headers=HEADERS, timeout=12)
        if r.status_code != 200: return channel, [], []
        
        text = html.unescape(r.text)
        channel_nodes = extract_nodes(text)
        valid_subs = []

        # 发现订阅地址并实测
        subs = set(re.findall(SUB_PATTERN, text))
        for sub in subs:
            nodes_from_sub, is_valid = fetch_sub_content(sub)
            if is_valid:
                channel_nodes.extend(nodes_from_sub)
                valid_subs.append(sub)
                
        return channel, list(set(channel_nodes)), valid_subs
    except: return channel, [], []

# --- 主逻辑 ---

def main():
    all_nodes = []
    all_valid_subs = []
    stats = {}

    logger.info("📡 开始深度抓取与订阅探测...")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_channel, ch): ch for ch in CHANNELS}
        for f in tqdm(as_completed(futures), total=len(CHANNELS), desc="频道进度"):
            ch, n_list, s_list = f.result()
            stats[ch] = len(n_list)
            all_nodes.extend(n_list)
            all_valid_subs.extend(s_list)

    unique_nodes = sorted(list(set(all_nodes)))
    unique_subs = sorted(list(set(all_valid_subs)))

    # --- 保存文件 (锁定文件名) ---
    
    # 1. 有效节点明文
    with open("tg_collector.txt", "w", encoding="utf-8") as f:
        f.write(f"# Total Nodes: {len(unique_nodes)}\n")
        f.writelines(f"{n}\n" for n in unique_nodes)

    # 2. 节点 Base64 订阅
    with open("sub.txt", "w", encoding="utf-8") as f:
        f.write(base64.b64encode("\n".join(unique_nodes).encode()).decode())

    # 3. 有效原始订阅链接
    with open("valid_subs.txt", "w", encoding="utf-8") as f:
        f.writelines(f"{s}\n" for s in unique_subs)

    # 4. 统计信息
    with open("tg_channel_stats.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["channel", "valid_nodes"])
        for ch, count in stats.items():
            writer.writerow([ch, count])

    logger.info(f"✅ 完成！节点: {len(unique_nodes)}, 有效订阅地址: {len(unique_subs)}")

if __name__ == "__main__":
    main()
