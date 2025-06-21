import asyncio
import sqlite3
import psutil
import os
import json
import aiosqlite
from pyppeteer import launch
from pathlib import Path
from typing import List, Dict, Optional, Tuple

not_clean_arr = []
num_add = 0


def get_running_v2rayn_path() -> Optional[str]:
    """查找正在运行的 v2rayN.exe 路径"""
    for proc in psutil.process_iter(['name', 'exe']):
        if proc.info['name'] == 'v2rayN.exe' and proc.info['exe']:
            return str(Path(proc.info['exe']).parent)
    return None


class SubGet:
    """处理订阅获取的类"""

    def __init__(self, browser):
        self.browser = browser

    async def initialize(self, url: str, sel: List[str], id: int):
        """初始化订阅获取"""
        global not_clean_arr, num_add

        if id not in not_clean_arr:
            not_clean_arr.append(id)

        if not sel:
            convert_target = "mixed" if url.endswith(("yaml", "yml")) else ""
            print(f"{id} {url}")
            return await self.up_sub_item(url, id, id, convert_target)

        self.url = url
        self.list_el = sel[0]
        self.el = sel[1]
        self.id = id

        if len(sel) < 2:
            self.el = sel[0]
            self.list_el = None

        await self.start()

    async def start(self):
        """开始处理订阅"""
        page = await self.browser.newPage()
        await page.goto(self.url, {'timeout': 99999})

        if self.list_el:
            await page.waitForSelector(self.list_el, {'timeout': 99999})
            content = await page.querySelectorEval(self.list_el, 'el => el.href')
            await page.goto(content, {'timeout': 99999})

        await page.waitForSelector(self.el, {'timeout': 99999})
        elements = await page.querySelectorAll(self.el)

        for i, element in enumerate(elements):
            content = await page.evaluate('el => el.textContent', element)

            # 从文本中提取 URL
            url_match = None
            if 'http://' in content or 'https://' in content:
                for word in content.split():
                    if word.startswith('http://') or word.startswith('https://'):
                        url_match = word
                        break

            if not url_match:
                continue

            convert_target = "mixed" if url_match.endswith(("yaml", "yml")) else ""
            num = self.id

            if i > 0:
                global num_add
                num_add += 1
                num = len(select['select']) + num_add

            print(f"{self.id} {num} {url_match}")
            await self.up_sub_item(url_match, num, num, convert_target)

        await page.close()

    async def up_sub_item(self, url: str, remarks: int, id: int, convert_target: str) -> Optional[str]:
        """更新订阅项到数据库"""
        global not_clean_arr

        if id not in not_clean_arr:
            not_clean_arr.append(id)

        try:
            command = get_running_v2rayn_path()
            if command:
                db_path = Path(command) / 'guiConfigs' / 'guiNDB.db'

                async with aiosqlite.connect(str(db_path)) as db:
                    cursor = await db.cursor()
                    await cursor.execute(
                        """INSERT OR REPLACE INTO SubItem 
                        (remarks, url, id, convertTarget, sort) 
                        VALUES (?, ?, ?, ?, ?)""",
                        (str(remarks), url, str(id), convert_target, id)
                    )
                    await db.commit()
                return command
            else:
                print('v2rayN 未在运行')
        except Exception as error:
            print(f'处理路径时出现错误：{error}')
        return None


async def cleanup_database(num_list: List[int]):
    """清理数据库中不在列表中的订阅项"""
    try:
        command = get_running_v2rayn_path()
        if command:
            db_path = Path(command) / 'guiConfigs' / 'guiNDB.db'

            async with aiosqlite.connect(str(db_path)) as db:
                cursor = await db.cursor()
                placeholders = ','.join('?' * len(num_list))
                await cursor.execute(
                    f"DELETE FROM SubItem WHERE sort NOT IN ({placeholders})",
                    num_list
                )
                await db.commit()
                print(f"成功删除排序不在 {num_list} 内的记录。")
            print('已关闭数据库连接。')
        else:
            print('v2rayN 未在运行。')
    except Exception as error:
        print(f'清理操作失败: {error}')


async def main():
    """主函数"""
    global select

    browser = await launch(
        args=['--blink-settings=imagesEnabled=false'],
        headless=True,
        slowMo=0,
    )

    try:
        page = await browser.newPage()
        url = 'https://raw.githubusercontent.com/GGHHR/node_demo/master/v2rayn/init.json'
        print(f'请求json中：{url}')

        await page.goto(url, {'timeout': 99999})
        await page.waitForSelector('pre', {'timeout': 99999})
        content = await page.querySelectorEval('pre', 'el => el.textContent')
        select = json.loads(content)
        await page.close()
        print('请求成功')
    except Exception as e:
        with open('init.json', 'r', encoding='utf-8') as f:
            select = json.load(f)
        print('失败了，用本地的json文件')

    # 设置并发限制
    semaphore = asyncio.Semaphore(5)

    async def run_task(task):
        async with semaphore:
            return await task

    tasks = []
    for i, item in enumerate(select['select']):
        item['id'] = i + 1
        task = run_task(SubGet(browser).initialize(
            item['url'],
            item.get('sel', []),
            i + 1
        ))
        tasks.append(task)

    await asyncio.gather(*tasks)

    # 清理数据库
    sorted_nums = sorted(not_clean_arr)
    await cleanup_database(sorted_nums)

    # 保存更新后的配置
    with open('init.json', 'w', encoding='utf-8') as f:
        json.dump(select, f, ensure_ascii=False, indent=2)

    await browser.close()
    print("程序执行完成")


if __name__ == '__main__':
    select = {'select': []}  # 初始化全局变量
    asyncio.get_event_loop().run_until_complete(main())