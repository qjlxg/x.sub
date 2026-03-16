import os
import requests
import datetime

# 监控关键词（针对 v2board/xboard 常见的特征域名或关键词）
KEYWORDS = ["v2board", "xboard", "v2-board"]

def get_domains_from_crtsh(keyword):
    print(f"正在从 crt.sh 检索关键词: {keyword}")
    url = f"https://crt.sh/?q={keyword}&output=json"
    new_domains = set()
    try:
        # crt.sh 响应有时较慢，设置 60s 超时
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            data = response.json()
            for item in data:
                # 提取域名，去掉泛域名通配符
                name = item['common_name'].replace("*.", "")
                new_domains.add(name.lower())
    except Exception as e:
        print(f"检索 {keyword} 出错: {e}")
    return new_domains

def main():
    all_found = set()
    for kw in KEYWORDS:
        all_found.update(get_domains_from_crtsh(kw))

    if not all_found:
        print("未发现任何相关域名。")
        return

    file_path = 'results.txt'
    existing = set()
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            existing = {line.strip() for line in f if line.strip()}

    # 发现库外新资产
    unique_new = all_found - existing
    
    if unique_new:
        print(f"发现 {len(unique_new)} 个新域名！")
        # 合并并排序
        final = sorted(existing.union(unique_new))
        with open(file_path, 'w') as f:
            f.write("\n".join(final) + "\n")
    else:
        print("未发现库外新资产。")

if __name__ == "__main__":
    main()
