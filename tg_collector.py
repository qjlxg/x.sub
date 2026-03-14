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
   
    "v2raynodeauto",
    "clashnodeauto",
    "v2rayautoshare",
    "clashautoshare",
    "v2rayautodaily",
    "clashautodaily",
    "v2rayautonodehub",
    "clashautonodehub",
    "v2rayautonetwork",
    "clashautonetwork",
    "v2rayautoworld",
    "clashautoworld",
    "v2rayautoplanet",
    "clashautoplanet",
    "v2rayautogalaxy",
    "clashautogalaxy",
    "v2rayautouniverse",
    "clashautouniverse",
    "v2rayautolab",
    "clashautolab",
    "v2rayautocenter",
    "clashautocenter",
    "v2rayautobackup",
    "clashautobackup",
    "v2rayautofast",
    "clashautofast",
    "v2rayautopremium",
    "clashautopremium",
    "v2rayautovip",
    "clashautovip",
    "v2rayautoglobal",
    "clashautoglobal",
    "v2rayautocloud",
    "clashautocloud",
    "v2rayautohub",
    "clashautohub",
    "v2rayautolink",
    "clashautolink",
    "v2rayautodrop",
    "clashautodrop",
    "v2rayautofreedaily",
    "clashautofreedaily",
    "v2rayautofreenode",
    "clashautofreenode",
    "v2rayautofreeshare",
    "clashautofreeshare",
    "v2rayautofreecloud",
    "clashautofreecloud",
    "v2rayautofreecenter",
    "clashautofreecenter",
    "v2rayautofreebackup",
    "clashautofreebackup",
    "v2rayautofreefast",
    "clashautofreefast",
    "v2rayautofreepremium",
    "clashautofreepremium",
    "v2rayautofreevip",
    "clashautofreevip",
    "v2rayautofreeglobal",
    "clashautofreeglobal",
    "v2rayautofreenetwork",
    "clashautofreenetwork",
    "v2rayautofreeplanet",
    "clashautofreeplanet",
    "v2rayautofreegalaxy",
    "clashautofreegalaxy",
    "v2rayautofreeuniverse",
    "clashautofreeuniverse",
    "v2rayautofreelab",
    "clashautofreelab",
    "v2rayautofreehub",
    "clashautofreehub",
    "v2rayautofreelink",
    "clashautofreelink",
    "v2rayautofreedrop",
    "clashautofreedrop",
    "v2rayautofreecloudhub",
    "clashautofreecloudhub",
    "v2rayautofreeworldhub",
    "clashautofreeworldhub",
    "v2rayautofreecenterhub",
    "clashautofreecenterhub",
    "v2rayautofreebackuphub",
    "clashautofreebackuphub",
    "v2rayautofreefasthub",
    "clashautofreefasthub",
    "v2rayautofreepremiumhub",
    "clashautofreepremiumhub",
    "v2rayautofreeviphub",
    "clashautofreeviphub",
    "v2rayautofreeglobalhub",
    "clashautofreeglobalhub",
    "v2rayautofreenetworkhub",
    "clashautofreenetworkhub",
    "v2rayautofreeplanethub",
    "clashautofreeplanethub",
    "v2rayautofreegalaxyhub",
    "clashautofreegalaxyhub",
    "v2rayautofreeuniversehub",
    "clashautofreeuniversehub",
    "v2rayautofreelabhub",
    "clashautofreelabhub",
    "v2rayautofreelinkhub",
    "clashautofreelinkhub",
    "v2rayautofreedrophub",
    "clashautofreedrophub",
    "v2rayautofreeclouddaily",
    "clashautofreeclouddaily",
    "v2rayautofreeworlddaily",
    "clashautofreeworlddaily",
    "v2rayautofreecenterdaily",
    "clashautofreecenterdaily",
    "v2rayautofreebackupdaily",
    "clashautofreebackupdaily",
    "v2rayautofreefastdaily",
    "clashautofreefastdaily",
    "v2rayautofreepremiumdaily",
    "clashautofreepremiumdaily",
    "v2rayautofreevipdaily",
    "clashautofreevipdaily",
    "v2rayautofreeglobaldaily",
    "clashautofreeglobaldaily",
    "v2rayautofreenetworkdaily",
    "clashautofreenetworkdaily",
    "v2rayautofreeplanetdaily",
    "clashautofreeplanetdaily",
    "v2rayautofreegalaxydaily",
    "clashautofreegalaxydaily",
    "v2rayautofreeuniversedaily",
    "clashautofreeuniversedaily",
    "v2rayautofreelabdaily",
    "clashautofreelabdaily",
    "v2rayautofreehubdaily",
    "clashautofreehubdaily",
    "v2rayautofreelinkdaily",
    "clashautofreelinkdaily",
    "v2rayautofreedropdaily",
    "clashautofreedropdaily",
    "v2rayautofreecloudcenter",
    "clashautofreecloudcenter",
    "v2rayautofreeworldcenter",
    "clashautofreeworldcenter",
    "v2rayautofreecentercenter",
    "clashautofreecentercenter",
    "v2rayautofreebackupcenter",
    "clashautofreebackupcenter",
    "v2rayautofreefastcenter",
    "clashautofreefastcenter",
    "v2rayautofreepremiumcenter",
    "clashautofreepremiumcenter",
    "v2rayautofreevipcenter",
    "clashautofreevipcenter",
    "v2rayautofreeglobalcenter",
    "clashautofreeglobalcenter",
    "v2rayautofreenetworkcenter",
    "clashautofreenetworkcenter",
    "v2rayautofreeplanetcenter",
    "clashautofreeplanetcenter",
    "v2rayautofreegalaxycenter",
    "clashautofreegalaxycenter",
    "v2rayautofreeuniversecenter",
    "clashautofreeuniversecenter",
    "v2rayautofreelabcenter",
    "clashautofreelabcenter",
    "v2rayautofreehubcenter",
    "clashautofreehubcenter",
    "v2rayautofreelinkcenter",
    "clashautofreelinkcenter",
    "v2rayautofreedropcenter",
    "clashautofreedropcenter",
    "v2rayautofreecloudpro",
    "clashautofreecloudpro",
    "v2rayautofreeworldpro",
    "clashautofreeworldpro",
    "v2rayautofreecenterpro",
    "clashautofreecenterpro",
    "v2rayautofreebackuppro",
    "clashautofreebackuppro",
    "v2rayautofreefastpro",
    "clashautofreefastpro",
    "v2rayautofreepremiumpro",
    "clashautofreepremiumpro",
    "v2rayautofreevippro",
    "clashautofreevippro",
    "v2rayautofreeglobalpro",
    "clashautofreeglobalpro",
    "v2rayautofreenetworkpro",
    "clashautofreenetworkpro",
    "v2rayautofreeplanetpro",
    "clashautofreeplanetpro",
    "v2rayautofreegalaxypro",
    "clashautofreegalaxypro",
    "v2rayautofreeuniversepro",
    "clashautofreeuniversepro",
    "v2rayautofreelabpro",
    "clashautofreelabpro",
    "v2rayautofreehubpro",
    "clashautofreehubpro",
    "v2rayautofreelinkpro",
    "clashautofreelinkpro",
    "v2rayautofreedroppro",
    "clashautofreedroppro",


    "v2raynewnode",
    "clashnewnode",
    "v2raydailyshare",
    "clashdailyshare",
    "v2rayfastupdatepro",
    "clashfastupdatepro",
    "v2raycloudnode",
    "clashcloudnodepro",
    "v2rayfreedrops",
    "clashfreedrops",
    "v2rayfreelinks",
    "clashfreelinks",
    "v2rayfreesshub",
    "clashfreesshub",
    "v2rayfreessrhub",
    "clashfreessrhub",
    "v2rayfreessdaily",
    "clashfreessdaily",
    "v2rayfreessrshare",
    "clashfreessrshare",
    "v2rayfreessbackup",
    "clashfreessbackup",
    "v2rayfreessrbackup",
    "clashfreessrbackup",
    "v2rayfreesscenter",
    "clashfreesscenter",
    "v2rayfreessrcenter",
    "clashfreessrcenter",
    "v2rayfreesscloud",
    "clashfreesscloud",
    "v2rayfreessrcloud",
    "clashfreessrcloud",
    "v2rayfreessworld",
    "clashfreessworld",
    "v2rayfreessrworld",
    "clashfreessrworld",
    "v2rayfreessplanet",
    "clashfreessplanet",
    "v2rayfreessrplanet",
    "clashfreessrplanet",
    "v2rayfreessgalaxy",
    "clashfreessgalaxy",
    "v2rayfreessrgalaxy",
    "clashfreessrgalaxy",
    "v2rayfreessuniverse",
    "clashfreessuniverse",
    "v2rayfreessruniverse",
    "clashfreessruniverse",
    "v2rayfreesslab",
    "clashfreesslab",
    "v2rayfreessrlab",
    "clashfreessrlab",
    "v2rayfreesscenterpro",
    "clashfreesscenterpro",
    "v2rayfreessrcenterpro",
    "clashfreessrcenterpro",
    "v2rayfreessdailypro",
    "clashfreessdailypro",
    "v2rayfreessrdailypro",
    "clashfreessrdailypro",
    "v2rayfreessbackuphub",
    "clashfreessbackuphub",
    "v2rayfreessrbackuphub",
    "clashfreessrbackuphub",
    "v2rayfreesslinkhub",
    "clashfreesslinkhub",
    "v2rayfreessrlinkhub",
    "clashfreessrlinkhub",
    "v2rayfreessfast",
    "clashfreessfast",
    "v2rayfreessrfast",
    "clashfreessrfast",
    "v2rayfreesspremium",
    "clashfreesspremium",
    "v2rayfreessrpremium",
    "clashfreessrpremium",
    "v2rayfreessvip",
    "clashfreessvip",
    "v2rayfreessrvip",
    "clashfreessrvip",
    "v2rayfreesselite",
    "clashfreesselite",
    "v2rayfreessrelite",
    "clashfreessrelite",
    "v2rayfreessglobal",
    "clashfreessglobal",
    "v2rayfreessrglobal",
    "clashfreessrglobal",
    "v2rayfreessnetwork",
    "clashfreessnetwork",
    "v2rayfreessrnetwork",
    "clashfreessrnetwork",
    "v2rayfreesscloudpro",
    "clashfreesscloudpro",
    "v2rayfreessrcloudpro",
    "clashfreessrcloudpro",
    "v2rayfreesshubpro",
    "clashfreesshubpro",
    "v2rayfreessrhubpro",
    "clashfreessrhubpro",
    "v2rayfreessdrop",
    "clashfreessdrop",
    "v2rayfreessrdrop",
    "clashfreessrdrop",
    "v2rayfreessbackupdaily",
    "clashfreessbackupdaily",
    "v2rayfreessrbackupdaily",
    "clashfreessrbackupdaily",
    "v2rayfreessfastdaily",
    "clashfreessfastdaily",
    "v2rayfreessrfastdaily",
    "clashfreessrfastdaily",
    "v2rayfreesspremiumdaily",
    "clashfreesspremiumdaily",
    "v2rayfreessrpremiumdaily",
    "clashfreessrpremiumdaily",
    "v2rayfreessvipdaily",
    "clashfreessvipdaily",
    "v2rayfreessrvipdaily",
    "clashfreessrvipdaily",
    "v2rayfreessglobaldaily",
    "clashfreessglobaldaily",
    "v2rayfreessrglobaldaily",
    "clashfreessrglobaldaily",
    "v2rayfreessnetworkdaily",
    "clashfreessnetworkdaily",
    "v2rayfreessrnetworkdaily",
    "clashfreessrnetworkdaily",
    "v2rayfreesscloudhub",
    "clashfreesscloudhub",
    "v2rayfreessrcloudhub",
    "clashfreessrcloudhub",
    "v2rayfreessworldhub",
    "clashfreessworldhub",
    "v2rayfreessrworldhub",
    "clashfreessrworldhub",
    "v2rayfreessplanetdaily",
    "clashfreessplanetdaily",
    "v2rayfreessrplanetdaily",
    "clashfreessrplanetdaily",
    "v2rayfreessgalaxydaily",
    "clashfreessgalaxydaily",
    "v2rayfreessrgalaxydaily",
    "clashfreessrgalaxydaily",
    "v2rayfreessuniversehub",
    "clashfreessuniversehub",
    "v2rayfreessruniversehub",
    "clashfreessruniversehub",
    "v2rayfreesslabdaily",
    "clashfreesslabdaily",
    "v2rayfreessrlabdaily",
    "clashfreessrlabdaily",
    "v2rayfreesscenterhub",
    "clashfreesscenterhub",
    "v2rayfreessrcenterhub",
    "clashfreessrcenterhub",
    "v2rayfreessdailyhub",
    "clashfreessdailyhub",
    "v2rayfreessrdailyhub",
    "clashfreessrdailyhub",
    "v2rayfreessbackupcenter",
    "clashfreessbackupcenter",
    "v2rayfreessrbackupcenter",
    "clashfreessrbackupcenter",
    "v2rayfreessfastcenter",
    "clashfreessfastcenter",
    "v2rayfreessrfastcenter",
    "clashfreessrfastcenter",
    "v2rayfreesspremiumcenter",
    "clashfreesspremiumcenter",
    "v2rayfreessrpremiumcenter",
    "clashfreessrpremiumcenter"


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
