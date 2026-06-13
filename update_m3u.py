import asyncio
import aiohttp

# 收集两个全网最火、更新最频繁的高质量源
SOURCE_URLS = [
    "https://live.fanmingming.com/tv/m3u/ipv4.m3u",
    "https://raw.githubusercontent.com/YueChan/Live/main/APTV.m3u"
]
OUTPUT_FILE = "tv_live.m3u"
TIMEOUT = 3  # 3秒超时，加快测试速度

async def check_url(session, channel_info, url):
    # 过滤掉无法在公网播放的本地内网源
    if "127.0.0.1" in url or "localhost" in url:
        return None
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        # 测试链接是否通畅，允许 301/302 重定向
        async with session.head(url, headers=headers, timeout=TIMEOUT, allow_redirects=True) as response:
            if response.status in [200, 206, 301, 302]:
                return (channel_info, url)
    except Exception:
        pass
    return None

async def main():
    print("开始获取直播源...")
    raw_channels = []
    
    # 1. 抓取并精准解析所有源
    async with aiohttp.ClientSession() as session:
        for source_url in SOURCE_URLS:
            try:
                async with session.get(source_url, timeout=10) as response:
                    if response.status == 200:
                        text = await response.text()
                        # splitlines() 完美解决 Windows/Linux 换行符 (\r\n) 导致的网址损坏问题
                        lines = text.splitlines()
                        current_info = None
                        for line in lines:
                            line = line.strip()
                            if line.startswith("#EXTINF"):
                                current_info = line
                            elif line.startswith("http") and current_info:
                                raw_channels.append((current_info, line))
                                current_info = None
            except Exception as e:
                print(f"抓取源失败: {source_url}, 错误: {e}")

        print(f"共抓取到 {len(raw_channels)} 个原始频道，开始进行云端测活...")
        
        # 2. 并发测试
        tasks = [check_url(session, info, url) for info, url in raw_channels]
        results = await asyncio.gather(*tasks)
        valid_channels = [res for res in results if res is not None]

    # 3. 智能兜底逻辑
    # 如果云端测活全部失败（大概率是GitHub海外机房IP被国内服务器屏蔽），则触发兜底，保留全部原始频道
    if len(valid_channels) == 0 and len(raw_channels) > 0:
        print("⚠️ 警告：云端测活结果为0（GitHub海外机房被电视服务器拦截）。已启动智能兜底，为您保留全部带分类的原始频道！")
        final_channels = raw_channels
    else:
        print(f"🎉 测活完成！成功筛选出 {len(valid_channels)} 个优质活渠道。")
        final_channels = valid_channels

    # 4. 写入 M3U 文件
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for info, url in final_channels:
            f.write(f"{info}\n{url}\n")
    print("M3U 文件更新成功！")

if __name__ == "__main__":
    asyncio.run(main())
