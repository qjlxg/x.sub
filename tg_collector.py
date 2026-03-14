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

# 使用你认可的真实活跃频道列表
CHANNELS = [
    "dingyue_Center", "pgkj666", "anranbp", "hkaa0", "wxgqlfx", "freeVPNjd", "arzhecn", 
    "schpd", "jichang_list", "linux_do_channel", "nodeseekc", "hostloc_pro", 
    "serveruniverse", "sharecentrepro", "VlessConfig", "V2rayNGX", "V2rayClashNode", 
    "SSR_V2RAY_Clash", "v2cross", "Gfwh_Sub", "NodeFree", "free_ss", "Tizi_Share",
    "VlessConfigPool", "Shadowrocket_VN", "Clash_V2ray_Node", "i_v2ray", "v2ray_vpn_free", 
    "ssrList", "v2free_node", "ClashNode_Free", "Link_Vless_Nodes", "FreeNode_List", 
    "DailyNode_Update", "V2Ray_Shadowrocket", "One_Node_One_World", "Fast_V2ray_Nodes"
]

PROTO_PATTERN = r"(?:vmess|vless|trojan|ss|ssr|hysteria|hysteria2|hy2)://[A-Za-z0-9+/=_.:\-?&%@#]+"
# 增强正则，确保链接完整性
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
    """
    仅用于从订阅内容中提取节点
    """
    nodes = re.findall(PROTO_PATTERN, text)
    b64_blocks = re.findall(r"[A-Za-z0-9+/]{80,}", text)
    for block in b64_blocks:
        decoded = safe_decode(block)
        if "://" in decoded:
            nodes.extend(re.findall(PROTO_PATTERN, decoded))
    return [n.split('<')[0].split('"')[0].strip() for n in nodes if n]

def fetch_sub_content(sub_url):
    """
    不仅抓取内容，还通过 Header 校验流量信息
    """
    try:
        r = requests.get(sub_url, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            return [], False

        # --- 流量元数据校验 (根据你提供的脚本逻辑) ---
        user_info = r.headers.get('Subscription-Userinfo') or r.headers.get('subscription-userinfo')
        if user_info:
            info = dict(item.split('=') for item in user_info.split('; ') if '=' in item)
            upload = int(info.get('upload', 0))
            download = int(info.get('download', 0))
            total = int(info.get('total', 0))
            
            # 关键：如果已用流量超过或等于总流量，直接判定为废源
            if total > 0 and (upload + download) >= total:
                return [], False

        # --- 内容解析校验 ---
        content = r.text
        if "://" not in content:
            content = safe_decode(content)
        
        nodes = extract_nodes_only(content)
        
        # 如果提取出的节点列表为空，说明该订阅链接无效或流量提示文字中无节点
        if nodes:
            return nodes, True
            
    except:
        pass
    return [], False

def process_channel_only_subs(channel):
    """
    新逻辑：只从订阅链接里拿节点，完全抛弃频道消息里的直发散点
    """
    try:
        r = requests.get(f"https://t.me/s/{channel}", headers=HEADERS, timeout=15)
        if r.status_code != 200: return channel, [], []
        
        text = html.unescape(r.text)
        sub_only_nodes = []
        valid_subs = []

        # 1. 扫描页面中的所有潜在订阅链接
        raw_subs = re.findall(SUB_PATTERN, text)
        
        # 2. 对每个链接进行深度探测和流量校验
        for sub in set(raw_subs):
            clean_sub = sub.rstrip('.,;)')
            nodes_from_sub, is_valid = fetch_sub_content(clean_sub)
            
            if is_valid:
                # 只有从有效订阅链接里抓到的节点才会被计入
                sub_only_nodes.extend(nodes_from_sub)
                valid_subs.append(clean_sub)
                
        # 注意：这里返回的节点列表完全来自于订阅链接
        return channel, list(set(sub_only_nodes)), valid_subs
    except:
        return channel, [], []

def main():
    all_sub_nodes, all_valid_links, stats = [], [], {}
    logger.info("📡 模式：纯订阅链接节点提取 (已启用流量校验)")

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

    logger.info(f"✅ 提取完成！总节点: {len(unique_nodes)} (全部来自有效订阅), 有效订阅数: {len(unique_subs)}")

if __name__ == "__main__":
    main()
