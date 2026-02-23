import urllib.request
import re

# 这是原作者的原始获取地址
SOURCE_URL = "https://gitflic.ru/project/utako/utako/blob/raw?file=jp.m3u&branch=main"

def get_latest_links():
    mapping = {}
    try:
        req = urllib.request.Request(SOURCE_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            content = response.read().decode('utf-8')
            lines = content.split('\n')
            for i in range(len(lines)):
                if lines[i].startswith("#EXTINF"):
                    match = re.search(r'tvg-id="([^"]+)"', lines[i])
                    if match and i + 1 < len(lines):
                        tvg_id = match.group(1)
                        url = lines[i+1].strip()
                        if url and not url.startswith("#"):
                            # 把找到的最新链接存起来
                            mapping[tvg_id] = url
    except Exception as e:
        print(f"抓取最新源出错: {e}")
    return mapping

def update_playlist(mapping):
    try:
        with open("base.m3u", "r", encoding="utf-8") as f:
            lines = f.read().split('\n')
    except FileNotFoundError:
        print("找不到 base.m3u 文件，请确保文件存在！")
        return

    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith("#EXTINF"):
            new_lines.append(line)
            match = re.search(r'tvg-id="([^"]+)"', line)
            if i + 1 < len(lines):
                next_line = lines[i+1].strip()
                # 如果下一行是链接
                if next_line and not next_line.startswith("#"):
                    original_url = next_line
                    tvg_id = match.group(1) if match else None
                    
                    # 核心魔法：如果这个频道在最新源里有，就用新链接；没有（比如你的 Abema），就保留原样
                    if tvg_id and tvg_id in mapping:
                        new_lines.append(mapping[tvg_id])
                    else:
                        new_lines.append(original_url)
                    i += 2
                    continue
        
        if line: 
            new_lines.append(line)
        i += 1

    # 最终生成一个专属的 live.m3u 给 APTV 用
    with open("live.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")
    print("🎉 更新成功！已生成最新的 live.m3u")

if __name__ == "__main__":
    print("开始获取最新 Token 链接...")
    mapping = get_latest_links()
    if mapping:
        print(f"成功获取到 {len(mapping)} 个频道的最新链接，正在合并...")
        update_playlist(mapping)
    else:
        print("未能获取到最新链接，放弃本次更新。")
