import os
from googlesearch import search
from urllib.parse import urlparse
import datetime

# 你的搜索指令
QUERY = '(inurl:"/theme/Rocket/assets/" OR intext:"layouts__index.async.js") after:2026-03-12'

def get_domain(url):
    try:
        domain = urlparse(url).netloc
        return domain
    except:
        return None

def main():
    print(f"开始搜索: {QUERY}")
    new_domains = set()
    
    # 抓取前 100 个结果
    try:
        for url in search(QUERY, num_results=100, lang="en"):
            domain = get_domain(url)
            if domain:
                new_domains.add(domain)
    except Exception as e:
        print(f"搜索出错: {e}")

    if not new_domains:
        print("未发现新资产。")
        return

    # 读取旧数据进行去重
    file_path = 'results.txt'
    existing_domains = set()
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            existing_domains = set(line.strip() for line in f)

    # 合并并写入
    final_domains = existing_domains.union(new_domains)
    with open(file_path, 'w') as f:
        for d in sorted(final_domains):
            f.write(f"{d}\n")
    
    print(f"完成！当前共记录 {len(final_domains)} 个域名。")

if __name__ == "__main__":
    main()
