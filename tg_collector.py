import requests
import re
import logging
from tqdm import tqdm
import csv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Telegram频道列表
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

# URL 协议类节点（全协议）
REGEX_PROTOCOLS = [
    r"vmess://[A-Za-z0-9+/=_.:\-?&%]+",
    r"vless://[A-Za-z0-9+/=_.:\-?&%]+",
    r"trojan://[A-Za-z0-9+/=_.:\-?&%]+",
    r"ss://[A-Za-z0-9+/=_.:\-?&%]+",
    r"ssr://[A-Za-z0-9+/=_.:\-?&%]+",

    # Hysteria / Hysteria2 / hy
    r"hy://[A-Za-z0-9@:/?&=._+\-]+",
    r"hysteria://[A-Za-z0-9@:/?&=._+\-]+",
    r"hysteria2://[A-Za-z0-9@:/?&=._+\-]+",
]

# Clash / Surge / YAML / QX 明文
REGEX_YAML = [
    r"proxies:\s*[\s\S]+?proxy-groups:",
    r"proxies:\s*[\s\S]+",
    r"

\[Proxy\]

[\s\S]+?\n\n",
    r"type:\s*(vmess|vless|ss|trojan)[\s\S]+?\n\n",

    # Hysteria YAML
    r"type:\s*hysteria[\s\S]+?\n\n",
    r"type:\s*hysteria2[\s\S]+?\n\n",

    # Surge hy
    r"hysteria,.*",
    r"hysteria2,.*",
]

# Base64 长串（订阅）
REGEX_BASE64 = [
    r"(?<![A-Za-z0-9+/=])(?:[A-Za-z0-9+/]{80,}={0,2})(?![A-Za-z0-9+/=])"
]


def extract_all_nodes(text):
    """从 HTML 中提取所有节点格式"""
    results = []

    # 1. URL 协议类
    for pattern in REGEX_PROTOCOLS:
        results += re.findall(pattern, text)

    # 2. YAML / Clash / Surge
    for pattern in REGEX_YAML:
        results += re.findall(pattern, text)

    # 3. Base64 长串
    for pattern in REGEX_BASE64:
        results += re.findall(pattern, text)

    return results


def fetch_tg_channels():
    all_nodes = []
    stats = {}  # 频道 → 节点数量

    logger.info("📡 正在抓取 Telegram 频道节点（最简洁版，无验证）...")

    for channel in tqdm(CHANNELS, desc="抓取频道"):
        url = f"https://t.me/s/{channel}"
        count = 0

        try:
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=12)
            if r.status_code == 200:
                nodes = extract_all_nodes(r.text)
                count = len(nodes)
                all_nodes.extend(nodes)
        except Exception:
            pass

        stats[channel] = count

    # 去重
    all_nodes = list(set(all_nodes))

    # 保存节点全集
    with open("tg_collector.txt", "w", encoding="utf-8") as f:
        f.write("# === Telegram 全协议节点全集（无验证） ===\n")
        for n in all_nodes:
            f.write(n.strip() + "\n")

    # 保存频道统计 CSV
    with open("tg_channel_stats.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["channel", "count"])
        for ch, ct in stats.items():
            writer.writerow([ch, ct])

    logger.info(f"🎉 完成！共提取 {len(all_nodes)} 条节点")
    logger.info("📊 频道统计已保存到 tg_channel_stats.csv")


if __name__ == "__main__":
    fetch_tg_channels()
