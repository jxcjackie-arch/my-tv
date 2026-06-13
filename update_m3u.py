import asyncio
import aiohttp
import datetime

# 你的终极私人直播源百宝箱（中文精装 + 全球新闻 + 美国本土频道）
SOURCE_URLS = [
    # 1. 包含央视、卫视的高质量纯净源
    "https://raw.githubusercontent.com/YueChan/Live/main/IPTV.m3u",
    # 2. 专门收集全球主流新闻媒体的开源库（含 Bloomberg, CBS, NBC 等）
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/news.m3u",
    # 3. 专门收集美国本土频道的开源库（含 Fox 系列, ABC 系列等）
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/us.m3u"
]
OUTPUT_FILE = "tv_live.m3u"
TIMEOUT = 4

async def check_url(session, channel_info, url):
    if "127.0.0.1" in url or "localhost" in url:
        return None
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        async with session.head(url, headers=headers, timeout=TIMEOUT, allow_redirects=True) as response:
            if response.status in [200, 206, 301, 302]:
                return (channel_info, url)
    except Exception:
        pass
    return None

async def main():
    print("开始获取带分类的高质量直播源...")
    raw_channels = []
    
    async with aiohttp.ClientSession() as session:
        for source_url in SOURCE_URLS:
            try:
                async with session.get(source_url, timeout=10) as response:
                    if response.status == 200:
                        text = await response.text()
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

        print(f"抓取完成，开始测活...")
        tasks = [check_url(session, info, url) for info, url in raw_channels]
        results = await asyncio.gather(*tasks)
        valid_channels = [res for res in results if res is not None]

    # 兜底机制：如果全军覆没，保留全部
    final_channels = raw_channels if len(valid_channels) == 0 and len(raw_channels) > 0 else valid_channels

    # 写入最终的 M3U 文件
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        # 写入运行状态探针
        now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f'#EXTINF:-1 group-title="💡 系统信息", 🕒最新更新时间: {now_time}\n')
        f.write('http://127.0.0.1/dummy.m3u8\n')
        f.write(f'#EXTINF:-1 group-title="💡 系统信息", 📡当前有效频道: {len(final_channels)}个\n')
        f.write('http://127.0.0.1/dummy.m3u8\n')

        # 写入真实频道
        for info, url in final_channels:
            f.write(f"{info}\n{url}\n")
            
    print("大功告成！")

if __name__ == "__main__":
    asyncio.run(main())
