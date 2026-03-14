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

# 频道列表保持你之前的活跃源即可
CHANNELS = [
    "dingyue_Center", "pgkj666", "anranbp", "hkaa0", "wxgqlfx", "freeVPNjd", "arzhecn", 
    "schpd", "jichang_list", "linux_do_channel", "nodeseekc", "hostloc_pro", 
    "serveruniverse", "sharecentrepro", "VlessConfig", "V2rayNGX", "V2rayClashNode", 
    "SSR_V2RAY_Clash", "v2cross", "Gfwh_Sub", "NodeFree", "free_ss", "Tizi_Share"
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

def extract_nodes(text):
    nodes = re.findall(PROTO_PATTERN, text)
    b64_blocks = re.findall(r"[A-Za-z0-9+/]{80,}", text)
    for block in b64_blocks:
        decoded = safe_decode(block)
        if "://" in decoded:
            nodes.extend(re.findall(PROTO_PATTERN, decoded))
    return [n.split('<')[0].split('"')[0].strip() for n in nodes if n]

def fetch_sub_content(sub_url):
    """
    不仅抓取内容，还检查流量元数据 (核心修复)
    """
    try:
        r = requests.get(sub_url, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            return [], False

        # --- 仿照你提供的代码逻辑：检查流量元数据 ---
        # 很多机场会在响应头返回: upload=xxx; download=xxx; total=xxx; expire=xxx
        user_info = r.headers.get('Subscription-Userinfo') or r.headers.get('subscription-userinfo')
        if user_info:
            info = dict(item.split('=') for item in user_info.split('; ') if '=' in item)
            upload = int(info.get('upload', 0))
            download = int(info.get('download', 0))
            total = int(info.get('total', 0))
            
            # 如果总流量 > 0 且 (已用 >= 总量)，说明废了
            if total > 0 and (upload + download) >= total:
                logger.warning(f"跳过废源 (流量耗尽): {sub_url}")
                return [], False

        # --- 深度校验：内容必须包含节点协议 ---
        content = r.text
        if "://" not in content:
            content = safe_decode(content)
        
        nodes = extract_nodes(content)
        
        # 再次确认：如果是“流量耗尽”提示，extract_nodes 应该抓不到任何有效节点
        if nodes:
            return nodes, True
            
    except Exception as e:
        pass
    return [], False

def process_channel(channel):
    try:
        r = requests.get(f"https://t.me/s/{channel}", headers=HEADERS, timeout=15)
        if r.status_code != 200: return channel, [], []
        
        text = html.unescape(r.text)
        channel_nodes = extract_nodes(text)
        valid_subs = []

        raw_subs = re.findall(SUB_PATTERN, text)
        for sub in set(raw_subs):
            clean_sub = sub.rstrip('.,;)')
            nodes_from_sub, is_valid = fetch_sub_content(clean_sub)
            if is_valid:
                channel_nodes.extend(nodes_from_sub)
                valid_subs.append(clean_sub)
                
        return channel, list(set(channel_nodes)), valid_subs
    except: return channel, [], []

def main():
    all_nodes, all_valid_subs, stats = [], [], {}
    logger.info("📡 深度过滤模式启动...")

    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(process_channel, ch): ch for ch in CHANNELS}
        for f in tqdm(as_completed(futures), total=len(CHANNELS), desc="采集进度"):
            ch, n_list, s_list = f.result()
            stats[ch] = len(n_list)
            all_nodes.extend(n_list)
            all_valid_subs.extend(s_list)

    unique_nodes = sorted(list(set(all_nodes)))
    unique_subs = sorted(list(set(all_valid_subs)))

    # 保存文件 (保持原有文件名)
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

    logger.info(f"✅ 过滤完成！存活节点: {len(unique_nodes)}, 真活源: {len(unique_subs)}")

if __name__ == "__main__":
    main()
