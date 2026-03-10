import requests
import re
import os
from urllib.parse import urlparse



CHANNELS = [
    'jichangbaipiao', 
    'Airport_News', 
    'v2board_trial', 
    'baipiaojichang',
    'jichangtuijian',
    'baipiao_ml',
    'AirPort_Survey',
    'jichang_0',
    'v2board_airport'
]

def fetch_from_tg():
    all_domains = set()
    # 匹配标准 http/https 链接
    url_pattern = re.compile(r'https?://[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(?:\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})+')
    # 排除非机场的常见域名
    exclude_list = ['t.me', 'telegram.org', 'google.com', 'github.com', 'baidu.com', 'yandex.com', 'wikipedia.org']

    print("开始从 Telegram 频道采集域名...")
    
    for channel in CHANNELS:
        tg_url = f"https://t.me/s/{channel}"
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            r = requests.get(tg_url, headers=headers, timeout=15)
            if r.status_code == 200:
                found_urls = url_pattern.findall(r.text)
                count = 0
                for fu in found_urls:
                    domain_obj = urlparse(fu)
                    domain = domain_obj.netloc.lower()
                    
                    if domain and not any(ex in domain for ex in exclude_list):
                        # 统一格式化为 https://domain
                        clean_url = f"https://{domain}"
                        if clean_url not in all_domains:
                            all_domains.add(clean_url)
                            count += 1
                print(f"频道 [{channel}]: 采集到 {count} 个有效域名")
        except Exception as e:
            print(f"采集频道 [{channel}] 出错: {e}")

    # 写入结果文件 (不带 link 首行)
    output_file = 'tg_collector.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        # 直接按行写入域名
        domains_list = sorted(list(all_domains))
        f.write('\n'.join(domains_list))
        if domains_list:
            f.write('\n')
            
    print(f"\n采集完成！共提取 {len(all_domains)} 个唯一域名，已保存至 {output_file}")

if __name__ == "__main__":
    fetch_from_tg()
