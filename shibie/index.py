import asyncio
import os
from playwright.async_api import async_playwright

STATE_FILE = "state.json"

async def run():
    async with async_playwright() as p:
        executable = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"

        if os.path.exists(STATE_FILE):
            # 有登录信息 → 直接用
            browser = await p.chromium.launch(headless=False, executable_path=executable)
            context = await browser.new_context(storage_state=STATE_FILE)
            print("✅ 已加载登录信息")
        else:
            # 没有登录信息 → 先登录一次
            browser = await p.chromium.launch(headless=False, executable_path=executable)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto("https://www.douyu.com/directory/watchHistory")

            print("⚠️ 请在页面完成登录，15 秒后保存状态")
            await page.wait_for_timeout(15000)

            await context.storage_state(path=STATE_FILE)
            print("💾 登录信息已保存")

        # 不管是否有 state.json，最后都会访问页面
        page = await context.new_page()
        await page.goto("https://www.douyu.com/directory/watchHistory")

        await page.wait_for_timeout(5000)
        await browser.close()

asyncio.run(run())
