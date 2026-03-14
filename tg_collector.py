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

# 精选 2026 真实活跃频道
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
    "trand_farsi", "vpnplusee_free", "freekankan", "awxdy666",
    "V2rayClashNode", "SSR_V2RAY_Clash", "v2cross", "VlessConfigPool", "Shadowrocket_VN", 
    "Gfwh_Sub", "NodeFree", "Clash_V2ray_Node", "i_v2ray", "free_ss", "v2ray_vpn_free", 
    "ssrList", "v2free_node", "ClashNode_Free", "Tizi_Share", "Link_Vless_Nodes",
    "FreeNode_List", "DailyNode_Update", "V2Ray_Shadowrocket", "One_Node_One_World", "Fast_V2ray_Nodes"
]

PROTO_PATTERN = r"(?:vmess|vless|trojan|ss|ssr|hysteria|hysteria2|hy2)://[A-Za-z0-9+/=_.:\-?&%@#]+"
# 修正后的正则：包含 % 和 /，防止链接截断
SUB_PATTERN = r"https?://[^\s<>\"'；]+?(?:sub|subscribe|api/v\d/|token=|link/|/s/|/clash/|/v2ray/|/free/)[A-Za-z0-9\-\.=&?%/]+"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'}

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
        # 只有解码后包含协议头的才算有效
        if "://" in decoded:
            nodes.extend(re.findall(PROTO_PATTERN, decoded))
    return [n.split('<')[0].split('"')[0].strip() for n in nodes if n]

def fetch_sub_content(sub_url):
    """
    深度验证：不仅要下载成功，还得确保内容里真的有节点协议头
    """
    try:
        r = requests.get(sub_url, headers=HEADERS, timeout=12)
        if r.status_code == 200 and len(r.text) > 50:
            content = r.text
            # 如果不包含协议头，尝试解码
            if "://" not in content:
                content = safe_decode(content)
            
            # 提取节点并校验数量
            nodes = extract_nodes(content)
            if nodes:
                return nodes, True
    except:
        pass
    return [], False

def process_channel(channel):
    try:
        r = requests.get(f"https://t.me/s/{channel}", headers=HEADERS, timeout=15)
        if r.status_code != 200: return channel, [], []
        
        text = html.unescape(r.text)
        channel_nodes = extract_nodes(text)
        valid_subs = []

        # 发现链接并实测
        raw_subs = re.findall(SUB_PATTERN, text)
        for sub in set(raw_subs):
            clean_sub = sub.rstrip('.,;)')
            nodes_from_sub, is_valid = fetch_sub_content(clean_sub)
            if is_valid:
                channel_nodes.extend(nodes_from_sub)
                valid_subs.append(clean_sub)
                
        return channel, list(set(channel_nodes)), valid_subs
    except:
        return channel, [], []

def main():
    all_nodes, all_valid_subs, stats = [], [], {}
    logger.info(f"🚀 启动采集器 | 频道数: {len(CHANNELS)}")

    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(process_channel, ch): ch for ch in CHANNELS}
        for f in tqdm(as_completed(futures), total=len(CHANNELS), desc="进度"):
            ch, n_list, s_list = f.result()
            stats[ch] = len(n_list)
            all_nodes.extend(n_list)
            all_valid_subs.extend(s_list)

    unique_nodes = sorted(list(set(all_nodes)))
    unique_subs = sorted(list(set(all_valid_subs)))

    # 保存文件
    with open("tg_collector.txt", "w", encoding="utf-8") as f:
        f.write(f"# Total: {len(unique_nodes)}\n")
        f.writelines(f"{n}\n" for n in unique_nodes)
    with open("sub.txt", "w", encoding="utf-8") as f:
        f.write(base64.b64encode("\n".join(unique_nodes).encode()).decode())
    with open("valid_subs.txt", "w", encoding="utf-8") as f:
        f.writelines(f"{s}\n" for s in unique_subs)
    with open("tg_channel_stats.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["channel", "valid_nodes"])
        for ch, count in stats.items():
            writer.writerow([ch, count])

    logger.info(f"✅ 完成 | 节点: {len(unique_nodes)} | 有效链接: {len(unique_subs)}")

if __name__ == "__main__":
    main()
