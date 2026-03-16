import os
import time
import random
from googlesearch import search
from urllib.parse import urlparse

# 扩展搜索组合，增加命中率
QUERIES = [
    '(inurl:"/theme/Rocket/assets/" OR intext:"layouts__index.async.js") after:2026-03-12',
    'intitle:"V2Board" (inurl:"/auth/login" OR inurl:"/auth/register") after:2026-03-12',
    'intext:"Powered by V2Board" OR intext:"Powered by XBoard" after:2026-03-12'
]

def get_domain(url):
    try:
        domain = urlparse(url).netloc
        if domain:
            # 移除常见噪音
            if any(x in domain for x in ['github.com', 'google.com', 'youtube.com']):
                return None
            return domain
    except:
        return None

def main():
    new_domains = set()
    
    for q in QUERIES:
        print(f"正在搜索指令: {q}")
        try:
            # 模拟人类随机延迟，防止被 Google 屏蔽
            time.sleep(random.uniform(2, 5))
            # 降低单次抓取量（如 30 条），分批次抓取更稳定
            for url in search(q, num_results=30, lang="zh-CN"):
                domain = get_domain(url)
                if domain:
                    print(f"发现: {domain}")
                    new_domains.add(domain)
        except Exception as e:
            print(f"搜索 {q} 时出错 (可能是 429 频率限制): {e}")

    file_path = 'results.txt'
    existing_domains = set()
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            existing_domains = set(line.strip() for line in f if line.strip())

    # 找出真正的新域名
    unique_new = new_domains - existing_domains
    
    if unique_new:
        print(f"本次发现 {len(unique_new)} 个新域名！")
        final_domains = existing_domains.union(unique_new)
        with open(file_path, 'w') as f:
            for d in sorted(final_domains):
                f.write(f"{d}\n")
    else:
        print("本次未发现库外的新资产。")

if __name__ == "__main__":
    main()
