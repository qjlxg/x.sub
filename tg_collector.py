import requests
import re
import logging
import html
import base64
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

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

# 增强版正则：支持多层路径、查询参数、百分号编码
PROTO_PATTERN = r"(?:vmess|vless|trojan|ss|ssr|hysteria|hysteria2|hy2)://[A-Za-z0-9+/=_.:\-?&%@#]+"
SUB_PATTERN = r"https?://[^\s<>\"'；]+?(?:sub|subscribe|api/v\d/|token=|link/|/s/|/clash/|/v2ray/|/free/)[A-Za-z0-9\-\.=&?%/]+"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'}

def process_channel(channel):
    try:
        # 增加超时，TG 页面加载有时较慢
        r = requests.get(f"https://t.me/s/{channel}", headers=HEADERS, timeout=15)
        if r.status_code != 200: return channel, [], []
        
        # 核心：必须先处理 HTML 转义，否则链接里的 &amp; 会让订阅失效
        text = html.unescape(r.text)
        
        # 1. 提取直发节点
        channel_nodes = extract_nodes(text)
        
        # 2. 提取并清洗订阅链接
        raw_subs = re.findall(SUB_PATTERN, text)
        valid_subs = []
        
        # 清洗并实测链接
        for sub_url in set(raw_subs):
            clean_url = sub_url.rstrip('.,;)') # 剔除正则误抓的末尾标点
            nodes_from_sub, is_valid = fetch_sub_content(clean_url)
            if is_valid:
                channel_nodes.extend(nodes_from_sub)
                valid_subs.append(clean_url)
                
        return channel, list(set(channel_nodes)), valid_subs
    except:
        return channel, [], []

# fetch_sub_content 和 extract_nodes 保持逻辑不变，但需确保支持 Base64 解码
