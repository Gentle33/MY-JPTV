import urllib.request
import re

SOURCE_URL = "https://gitflic.ru/project/utako/utako/blob/raw?file=jp.m3u&branch=main"

def get_latest_data():
    mapping = {}
    try:
        # 加上伪装头，防止机器人被拦截
        req = urllib.request.Request(SOURCE_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            content = response.read().decode('utf-8')
            lines = content.split('\n')
            for i in range(len(lines)):
                if lines[i].startswith("#EXTINF"):
                    id_match = re.search(r'tvg-id="([^"]+)"', lines[i])
                    group_match = re.search(r'group-title="([^"]+)"', lines[i])
                    
                    if id_match and i + 1 < len(lines):
                        tvg_id = id_match.group(1)
                        group_title = group_match.group(1) if group_match else ""
                        url = lines[i+1].strip()
                        
                        if url and not url.startswith("#"):
                            # 只要 utako 官方源，抛弃无效备用源
                            if "utako.moe" in url:
                                # 👇 修复致命空格：把 URL 里的空格变成合法的 %20
                                url = url.replace(" ", "%20")
                                
                                if tvg_id not in mapping:
                                    mapping[tvg_id] = {
                                        "url": url,
                                        "group": group_title
                                    }
    except Exception as e:
        print(f"抓取最新源出错: {e}")
    return mapping

def update_playlist(mapping):
    try:
        with open("base.m3u", "r", encoding="utf-8") as f:
            lines = f.read().split('\n')
    except FileNotFoundError:
        print("找不到 base.m3u 文件！")
        return

    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith("#EXTINF"):
            match = re.search(r'tvg-id="([^"]+)"', line)
            if i + 1 < len(lines):
                next_line = lines[i+1].strip()
                if next_line and not next_line.startswith("#"):
                    original_url = next_line
                    tvg_id = match.group(1) if match else None
                    
                    if tvg_id and tvg_id in mapping:
                        new_group = mapping[tvg_id]["group"]
                        new_url = mapping[tvg_id]["url"]
                        
                        if new_group:
                            if 'group-title=' in line:
                                line = re.sub(r'group-title="[^"]*"', f'group-title="{new_group}"', line)
                            else:
                                line = line.replace('#EXTINF:-1', f'#EXTINF:-1 group-title="{new_group}"')
                        
                        new_lines.append(line)
                        
                        # 👇 采用 APTV 最稳定的专属防盗链 JSON 格式写法
                        if "utako.moe" in new_url:
                            ext_http = '#EXTHTTP:{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36","Referer":"https://web.utako.moe/"}'
                            new_lines.append(ext_http)
                            
                        new_lines.append(new_url)
                    else:
                        new_lines.append(line)
                        new_lines.append(original_url)
                    i += 2
                    continue
        
        if line: 
            new_lines.append(line)
        i += 1

    with open("live.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")
    print("🎉 更新成功！空格修复完成，APTV 防盗链格式注入成功！")

if __name__ == "__main__":
    mapping = get_latest_data()
    if mapping:
        update_playlist(mapping)
