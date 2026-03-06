import requests
from concurrent.futures import ThreadPoolExecutor

def check_url(url):
    url = url.strip()
    if not url:
        return None
    try:
        # 设置 5 秒超时，允许重定向
        response = requests.get(url, timeout=5, allow_redirects=True)
        if response.status_code < 400:
            print(f"[SUCCESS] {url}")
            return url
    except Exception as e:
        print(f"[FAILED] {url} - Error: {e}")
    return None

def main():
    file_path = 'trial.cfg'
    
    # 读取原始链接
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print("Error: trial.cfg not found.")
        return

    # 提取第一行 header (如果有的话)
    header = lines[0] if lines and 'link' in lines[0].lower() else ""
    urls = lines[1:] if header else lines

    # 使用线程池加速检测
    print(f"Starting to check {len(urls)} URLs...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(check_url, urls))

    # 过滤掉失败的链接
    valid_urls = [url for url in results if url is not None]

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        if header:
            f.write(header.strip() + '\n')
        for url in valid_urls:
            f.write(url + '\n')
    
    print(f"Check finished. {len(valid_urls)} valid links saved to {file_path}.")

if __name__ == "__main__":
    main()
