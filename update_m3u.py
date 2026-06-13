import asyncio
import aiohttp
import re

# 你想要抓取的上游直播源链接（这里放了两个著名的全球和中国源，你可以自己换掉）
SOURCE_URLS = [
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/cn.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/us.m3u"
]
OUTPUT_FILE = "tv_live.m3u"
TIMEOUT = 5  # 超过5秒不响应的链接就淘汰

async def check_url(session, channel_info, url):
    try:
        async with session.head(url, timeout=TIMEOUT, allow_redirects=True) as response:
            if response.status == 200:
                return f"{channel_info}\n{url}\n"
    except Exception:
        pass
    return None

async def process_m3u(session, source_url):
    valid_channels = []
    try:
        async with session.get(source_url) as response:
            if response.status != 200:
                return []
            text = await response.text()
            pattern = re.compile(r'(#EXTINF[^\n]+)\n(http[^\n]+)')
            matches = pattern.findall(text)
            tasks = [check_url(session, info, url) for info, url in matches]
            results = await asyncio.gather(*tasks)
            valid_channels = [res for res in results if res is not None]
    except Exception as e:
        print(f"读取源失败: {source_url}, 错误: {e}")
    return valid_channels

async def main():
    print("开始获取并测试直播源...")
    async with aiohttp.ClientSession() as session:
        all_valid_channels = []
        for url in SOURCE_URLS:
            channels = await process_m3u(session, url)
            all_valid_channels.extend(channels)
            
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for channel in all_valid_channels:
                f.write(channel)
    print(f"测试完成！共保留 {len(all_valid_channels)} 个有效源。")

if __name__ == "__main__":
    asyncio.run(main())
