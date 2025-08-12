import asyncio
from pyppeteer import launch
import psutil
import os
import sqlite3
import json
import re

not_clean_arr = set()
num_add = 0
select = None


def get_running_v2rayn_path():
    for proc in psutil.process_iter(['name', 'exe']):
        try:
            if proc.info['name'] and proc.info['name'] == 'v2rayN.exe':
                exe_path = proc.info['exe']
                return os.path.dirname(exe_path)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


def up_sub_item(url, remarks, id_, convert_target):
    global not_clean_arr
    if id_ not in not_clean_arr:
        not_clean_arr.add(id_)
    command = get_running_v2rayn_path()
    if command:
        db_path = os.path.join(command, 'guiConfigs', 'guiNDB.db')
        try:
            conn = sqlite3.connect(db_path)
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return
        cursor = conn.cursor()
        insert_or_update_sql = '''
            INSERT OR REPLACE INTO SubItem (remarks, url, id, convertTarget, sort)
            VALUES (?, ?, ?, ?, ?)
        '''
        try:
            cursor.execute(insert_or_update_sql, (str(id_), url, str(id_), convert_target, id_))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            conn.close()
    else:
        print('v2rayn is not running')


class SubGet:
    def __init__(self, browser):
        self.browser = browser

    async def initialize(self, url, sel, id_):
        global not_clean_arr, num_add, select
        if id_ not in not_clean_arr:
            not_clean_arr.add(id_)
        if sel is None:
            convert_target = "mixed" if url.endswith(('.yaml', '.yml')) else ""
            print(id_, url)
            # 保持 remarks 有意义，使用 url 作为 remarks
            up_sub_item(url, url, id_, convert_target)
        else:
            page = await self.browser.newPage()
            try:
                await page.goto(url, {'timeout': 30000})
                if isinstance(sel, list) and len(sel) >= 1:
                    if len(sel) == 1:
                        list_el = None
                        el = sel[0]
                    else:
                        list_el = sel[0]
                        el = sel[1]
                    if list_el:
                        try:
                            await page.waitForSelector(list_el, {'timeout': 30000})
                            content = await page.evaluate('''(listEl) => {
                                const element = document.querySelector(listEl);
                                return element ? element.href : null;
                            }''', list_el)
                            if content:
                                await page.goto(content, {'timeout': 30000})
                        except Exception:
                            # 若跳转失败，继续尝试在当前页抓取
                            pass
                    await page.waitForSelector(el, {'timeout': 30000})
                    contents = await page.evaluate('''(el) => {
                        const elements = document.querySelectorAll(el);
                        return Array.from(elements).map(element => element.textContent);
                    }''', el)
                    url_pattern = re.compile(r'https?://[^\s/$.?#].[^\s]*')
                    for i, content in enumerate(contents):
                        match = url_pattern.search(content)
                        if match:
                            match_url = match.group(0)
                            convert_target = "mixed" if match_url.endswith(('.yaml', '.yml')) else ""
                            num = id_
                            if i > 0:
                                num_add += 1
                                # 如果 select 存在则按原逻辑用 len(select['select']) + num_add
                                base = len(select['select']) if select and 'select' in select else 0
                                num = base + num_add
                            print(id_, num, match_url)
                            # 保持 remarks 有意义，使用 match_url 作为 remarks
                            up_sub_item(match_url, match_url, num, convert_target)
            finally:
                await page.close()


def cleanup_database(num):
    command = get_running_v2rayn_path()
    if command:
        if not num:
            # 为避免误删，当传入空 iterable 时不执行删除（保持安全）
            print(f'Successfully deleted records not in {num}. Deleted rows: 0')
            return
        db_path = os.path.join(command, 'guiConfigs', 'guiNDB.db')
        try:
            conn = sqlite3.connect(db_path)
        except sqlite3.Error as e:
            print(f'Delete error: {e}')
            return
        cursor = conn.cursor()
        placeholders = ', '.join('?' for _ in num)
        delete_sql = f'DELETE FROM SubItem WHERE sort NOT IN ({placeholders})'
        try:
            cursor.execute(delete_sql, num)
            conn.commit()
            print(f'Successfully deleted records not in {num}. Deleted rows: {cursor.rowcount}')
        except sqlite3.Error as e:
            print(f'Delete error: {e}')
        finally:
            conn.close()
    else:
        print('v2rayn is not running')


async def main():
    global select, not_clean_arr, num_add

    executable = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
    browser = await launch(headless=True, executablePath=executable, args=['--blink-settings=imagesEnabled=false'])

    try:
        if not os.path.isfile('init.json'):
            print('init.json not found')
            return

        with open('init.json', 'r', encoding='utf-8') as f:
            select = json.load(f)
        for i, v in enumerate(select['select']):
            v['id'] = i + 1

        sem = asyncio.Semaphore(6)

        async def task(v, i):
            async with sem:
                try:
                    await SubGet(browser).initialize(v['url'], v.get('sel'), i + 1)
                except Exception as e:
                    # 恢复原始输出格式
                    print(f"{i + 1} failed: {v['url']}", e)

        tasks = [task(v, i) for i, v in enumerate(select['select'])]
        await asyncio.gather(*tasks)

        cleanup_database(sorted(not_clean_arr))
    finally:
        await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
