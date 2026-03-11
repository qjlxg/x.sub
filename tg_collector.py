import requests
import re
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CHANNELS = [
    # --- 频道列表保持不变 ---
    'dingyue_Center', 'pgkj666', 'anranbp', 'hkaa0', 'wxgqlfx', 
    'freeVPNjd', 'arzhecn', 'schpd', 'jichang_list',
    'linux_do_channel', 'nodeseekc', 'hostloc_pro', 'serveruniverse',
    'sharecentrepro', 'Impart_Cloud', 'helingqi', 'AI_News_CN', 
    'Newlearner', 'DocOfCard', 'baipiao_ml', 'jichangtuijian', 
    'Airport_News', 'freemason6', 'jichangbaipiao',
    'v2ray_configs_pool', 'IP_CF_Config', 'FreakConfig', 'oneclickvpnkeys',
    'PrivateVPNs', 'DirectVPN', 'VlessConfig', 'manVPN', 'ELiV2RAY',
    'Outline_Vpn', 'PPT_f66_zHk2ZDY8', 'V2rayNGX', 'ccbaohe', 'wangcai_8',
    'vpn_3000', 'academi_vpn', 'freedatazone1', 'freev2rayi', 'mypremium98',
    'inikotesla', 'v2rayngalpha', 'v2rayngalphagamer', 'jiedian_share',
    'vpn_mafia', 'dr_v2ray', 'allv2board', 'bigsmoke_config', 'vpn_443',
    'prossh', 'mftizi', 'qun521', 'v2rayng_my2', 'go4sharing', 'trand_farsi',
    'vpnplusee_free', 'freekankan', 'awxdy666'
]

airport_list = []
list_lock = threading.Lock()

def get_sub_status(url):
    """探测订阅链接的剩余流量和有效期"""
    try:
        headers = {'User-Agent': 'ClashforWindows/0.19.0'}
        r = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
        info = r.headers.get('subscription-userinfo')
        if info:
            # 这里的正则提取更稳健
            parts = {m.group(1): int(m.group(2)) for m in re.finditer(r'(\w+)=(\d+)', info)}
            total = parts.get('total', 0) / (1024**3)
            used = (parts.get('upload', 0) + parts.get('download', 0)) / (1024**3)
            remain = total - used
            return f" [剩余: {remain:.2f}GB / 总量: {total:.0f}GB]"
    except:
        pass
    return ""

def is_content_valid(text):
    """核心改进：验证下载的内容是否包含真实的节点协议特征"""
    if not text:
        return False
    # 常见的节点协议头
    protocols = ['vmess://', 'vless://', 'ss://', 'trojan://', 'ssr://', 'proxies:', 'Proxy Group']
    # 如果包含以上特征，或者看起来是长字符串 Base64 (没有空格，长度大)
    if any(p in text for p in protocols):
        return True
    # 检查是否为 Base64 订阅（简单判断：无空格且长度较长）
    if len(text) > 64 and ' ' not in text[:100]:
        return True
    return False

def url_check_valid(target, url, bar):
    """深度检测：不仅看状态码，还看内容"""
    global airport_list
    try:
        headers = {'User-Agent': 'ClashforWindows/0.19.0'}
        # 使用 GET 请求下载少量数据进行验证，timeout 设短一点过滤慢速链接
        r = requests.get(url, headers=headers, timeout=7, allow_redirects=True, stream=True)
        
        if r.status_code == 200:
            # 只读取前 2000 个字节进行特征分析，节省流量和时间
            sample_content = r.iter_content(chunk_size=2000).__next__().decode('utf-8', 'ignore')
            
            if is_content_valid(sample_content):
                status_info = get_sub_status(url)
                with list_lock:
                    airport_list.append(f"{url}{status_info}")
    except:
        pass
    finally:
        bar.update(1)

def write_url_config(url_file, url_list, target):
    """多线程检测并写入指定的 tg_collector.txt"""
    logger.info(f'🚀 正在深度验证 {len(url_list)} 条订阅链接的真实有效性...')
    
    global airport_list
    airport_list = [] 

    bar = tqdm(total=len(url_list), desc=f'验证进度')
    
    # 线程数不宜过高，防止被机场防火墙集体屏蔽
    with ThreadPoolExecutor(max_workers=12) as executor:
        for url in url_list:
            executor.submit(url_check_valid, target, url, bar)
            
    bar.close()
    
    # 写入到你指定的 tg_collector.txt
    with open(url_file, 'w', encoding='utf-8') as f:
        f.write("# === 深度验证有效的订阅链接 ===\n")
        # 加上时间戳，方便你知道是什么时候更新的
        import datetime
        f.write(f"# 更新时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write('\n'.join(airport_list))
    
    logger.info(f'✅ 验证完成！有效节点已保存至: {url_file}')

def fetch_tg_data():
    all_domains = set()
    direct_subs = set()
    
    # 匹配规则保持不变
    sub_pattern = re.compile(r'https?://[a-zA-Z0-9][-a-zA-Z0-9.]+\.[a-zA-Z]{2,10}/(?:api/v1/client/)?subscribe\?token=[a-zA-Z0-9]+')
    generic_sub = re.compile(r'https?://[a-zA-Z0-9][-a-zA-Z0-9.]+\.[a-zA-Z]{2,10}/sub\?token=[a-zA-Z0-9]+')
    domain_pattern = re.compile(r'https?://([a-zA-Z0-9][-a-zA-Z0-9]{0,62}(?:\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})+)')
    
    exclude_list = ['t.me', 'telegram.org', 'google.com', 'github.com', 'baidu.com', 'yandex.com', 'v2ray', 'clash']

    print("📡 正在从 Telegram 抓取原始信息...")

    for channel in CHANNELS:
        url = f"https://t.me/s/{channel}"
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            r = requests.get(url, headers=headers, timeout=12)
            if r.status_code == 200:
                subs = sub_pattern.findall(r.text) + generic_sub.findall(r.text)
                for s in subs:
                    direct_subs.add(s)
                
                found_domains = domain_pattern.findall(r.text)
                for d in found_domains:
                    d = d.lower()
                    if not any(ex in d for ex in exclude_list):
                        all_domains.add(f"https://{d}")
        except:
            pass

    # 开始深度检测并写入 tg_collector.txt
    if direct_subs:
        write_url_config('tg_collector.txt', list(direct_subs), 'valid_subs')

    # 机场入口依然单独保存
    if all_domains:
        with open('airport_entrances.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(sorted(list(all_domains))))

if __name__ == "__main__":
    fetch_tg_data()
