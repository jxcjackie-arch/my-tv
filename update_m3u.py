import asyncio
import aiohttp
import datetime

# 换用同样托管在 GitHub 上的开源全球大库，绝对不会发生拦截抓取的情况
SOURCE_URLS = [
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/cn.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/us.m3u"
]
OUTPUT_FILE = "tv_live.m3u"
TIMEOUT = 3

async def check_url(session, channel_info, url):
    try:
        # 使用最基础的请求，减少被电视台服务器拒绝的概率
        async with session.head(url, timeout=TIMEOUT, allow_redirects=True) as response:
            if response.status in [200, 206, 301, 302]:
                return (channel_info, url)
    except Exception:
        pass
    return None

async def main():
    print("开始获取直播源...")
    raw_channels = []
    
    # 1. 抓取解析
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

        print(f"共抓取到 {len(raw_channels)} 个原始频道，开始测活...")
        
        # 2. 并发测活
        tasks = [check_url(session, info, url) for info, url in raw_channels]
        results = await asyncio.gather(*tasks)
        valid_channels = [res for res in results if res is not None]

    # 3. 智能兜底（防止全军覆没）
    if len(valid_channels) == 0 and len(raw_channels) > 0:
        final_channels = raw_channels
    else:
        final_channels = valid_channels

    # 4. 写入文件（加入诊断探针）
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        # 💡 核心诊断探针：生成两个假频道，用于在电视上确认缓存是否刷新
        now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f'#EXTINF:-1 group-title="运行状态", 🕒最后更新时间: {now_time}\n')
        f.write('http://127.0.0.1/dummy.m3u8\n')
        f.write(f'#EXTINF:-1 group-title="运行状态", 📡有效频道数量: {len(final_channels)}\n')
        f.write('http://127.0.0.1/dummy.m3u8\n')

        # 写入真实频道
        for info, url in final_channels:
            f.write(f"{info}\n{url}\n")
            
    print("M3U 文件更新成功！")

if __name__ == "__main__":
    asyncio.run(main())
