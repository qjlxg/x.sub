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
    # --- 搜索结果中的“白嫖/试用”大户 ---
    'dingyue_Center',    # 订阅分享中心（流量之王）
    'pgkj666',          # 白嫖分享社（0元优惠码基地）
    'anranbp',          # 我爱白嫖（无需验证、反复注册）
    'hkaa0',            # 五叶TG节点（1.95T超大流量）
    'wxgqlfx',          # 翻墙世界的梯子（100G/月，0元购）
    'freeVPNjd',        # 免费高速订阅节点（含专属优惠码）
    'arzhecn',          # 一群🐂🐎的机场（新站首发地）
    'schpd',            # 山茶花の机场频道（七喜机场等实测源）
    'jichang_list',
    
    # --- 搜索结果中的“技术/中转/号商”源 ---
    'linux_do_channel', # LINUX DO（技术大佬、号商进货）
    'nodeseekc',        # NodeSeek（新站开业、各种云主机试用）
    'hostloc_pro',      # HostlocPro（各种1元试用、余额赠送）
    'serveruniverse',   # 机界（300$体验金等高价值信息）
    
    # --- 搜索结果中的“互推与聚合源（从搜索预览的转发中提取） ---
    'sharecentrepro',   # SCP（每日免费节点、2PB订阅链接）
    'Impart_Cloud',     # Impart（稀有地区、转运公司送余额）
    'helingqi',         # 禾令奇Club（各种大会员/机场试用）
    'AI_News_CN',       # AI新闻（伴生大量Gemini/ChatGPT试用）
    'Newlearner',       # 自留地（虽然是大站，但偶尔有顶级Pro试用）
    'DocOfCard',        # 卡粉订阅（支付指纹、漫游WiFi试用）
    'baipiao_ml',       # 白嫖ML（专注订阅链接搬运）
    'jichangtuijian',   # 机场推荐（带实测数据）
    'Airport_News',     # 机场动态（全网新开业监控）
    'freemason6',       # 机场观测（白嫖无罪，0元包）
    'jichangbaipiao',   # 机场白嫖（基础库）

    # --- 新增频道源 ---
    'v2ray_configs_pool',
    'IP_CF_Config',
    'FreakConfig',
    'oneclickvpnkeys',
    'PrivateVPNs',
    'DirectVPN',
    'VlessConfig',
    'manVPN',
    'ELiV2RAY',
    'Outline_Vpn',
    'PPT_f66_zHk2ZDY8',
    'V2rayNGX',
    'ccbaohe',
    'wangcai_8',
    'vpn_3000',
    'academi_vpn',
    'freedatazone1',
    'freev2rayi',
    'mypremium98',
    'inikotesla',
    'v2rayngalpha',
    'v2rayngalphagamer',
    'jiedian_share',
    'vpn_mafia',
    'dr_v2ray',
    'allv2board',
    'bigsmoke_config',
    'vpn_443',
    'prossh',
    'mftizi',
    'qun521',
    'v2rayng_my2',
    'go4sharing',
    'trand_farsi',
    'vpnplusee_free',
    'freekankan',
    'awxdy666'
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
