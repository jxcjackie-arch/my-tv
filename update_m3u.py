import asyncio
import aiohttp
import re

# 替换为自带完美分类的高质量电视直播源（范明明IPv4源）
SOURCE_URLS = [
    "https://live.fanmingming.com/tv/m3u/ipv4.m3u"
]
OUTPUT_FILE = "tv_live.m3u"
TIMEOUT = 4  # 超过4秒不响应就淘汰，保证换台速度

async def check_url(session, channel_info, url):
    try:
        # 伪装成普通浏览器，防止被电视台的服务器拦截导致黑屏
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        # 改用 get 请求测活，对视频流更友好
        async with session.get(url, headers=headers, timeout=TIMEOUT) as response:
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
            
            # 精准抓取频道信息（包含 group-title 分类标签）和播放链接
            pattern = re.compile(r'(#EXTINF[^\n]+)\n(http[^\n]+)')
            matches = pattern.findall(text)
            
            # 并发测活
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
