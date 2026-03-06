import requests
import urllib3
from concurrent.futures import ThreadPoolExecutor

# 禁用不安全请求的警告（针对关闭 SSL 验证的情况）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def check_url(url):
    url = url.strip()
    if not url or not url.startswith('http'):
        return None
        
    # 模拟浏览器头部，防止被某些服务器拒绝
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        # 核心逻辑：
        # 1. timeout=(5, 10) 分别是 (连接超时, 读取超时)
        # 2. verify=False 即使证书过期或不匹配也允许通过
        # 3. requests 会自动识别 URL 中的端口（如 :8443）
        response = requests.get(url, timeout=(5, 10), headers=headers, verify=False, allow_redirects=True)
        
        # 状态码小于 400 认为有效（200, 301, 302 等）
        if response.status_code < 400:
            print(f"[SUCCESS] {url}")
            return url
        else:
            print(f"[FAILED] {url} - Status: {response.status_code}")
    except Exception as e:
        # 打印简短错误
        print(f"[FAILED] {url} - Error: {type(e).__name__}")
    
    return None

def main():
    file_path = 'trial.cfg'
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print("Error: trial.cfg not found.")
        return

    # 处理首行 (link)
    header = ""
    urls = []
    if lines:
        if 'link' in lines[0].lower():
            header = lines[0].strip()
            urls = lines[1:]
        else:
            urls = lines

    # 去重并清理空白字符
    urls = list(dict.fromkeys([u.strip() for u in urls if u.strip()]))

    print(f"Total URLs to check: {len(urls)}")

    # 增加并发数到 15 提高速度
    with ThreadPoolExecutor(max_workers=15) as executor:
        results = list(executor.map(check_url, urls))

    # 过滤结果
    valid_urls = [url for url in results if url is not None]

    # 保存
    with open(file_path, 'w', encoding='utf-8') as f:
        if header:
            f.write(header + '\n')
        for url in valid_urls:
            f.write(url + '\n')
    
    print(f"Done! Saved {len(valid_urls)} valid links.")

if __name__ == "__main__":
    main()
