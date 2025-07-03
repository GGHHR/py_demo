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
        if proc.info['name'] == 'v2rayN.exe':
            exe_path = proc.info['exe']
            return os.path.dirname(exe_path)
    return None


def up_sub_item(url, remarks, id_, convert_target):
    global not_clean_arr
    if id_ not in not_clean_arr:
        not_clean_arr.add(id_)
    command = get_running_v2rayn_path()
    if command:
        db_path = os.path.join(command, 'guiConfigs', 'guiNDB.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        insert_or_update_sql = '''
            INSERT OR REPLACE INTO SubItem (remarks, url, id, convertTarget, sort)
            VALUES (?, ?, ?, ?, ?)
        '''
        try:
            cursor.execute(insert_or_update_sql, (str(remarks), url, str(id_), convert_target, id_))
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
            up_sub_item(url, id_, id_, convert_target)
        else:
            page = await self.browser.newPage()
            await page.goto(url, {'timeout': 99999})
            if isinstance(sel, list) and len(sel) >= 1:
                if len(sel) == 1:
                    list_el = None
                    el = sel[0]
                else:
                    list_el = sel[0]
                    el = sel[1]
                if list_el:
                    await page.waitForSelector(list_el, {'timeout': 99999})
                    content = await page.evaluate('''(listEl) => {
                        const element = document.querySelector(listEl);
                        return element ? element.href : null;
                    }''', list_el)
                    if content:
                        await page.goto(content, {'timeout': 99999})
                await page.waitForSelector(el, {'timeout': 99999})
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
                            num = len(select['select']) + num_add
                        print(id_, num, match_url)
                        up_sub_item(match_url, num, num, convert_target)
            await page.close()


def cleanup_database(num):
    command = get_running_v2rayn_path()
    if command:
        db_path = os.path.join(command, 'guiConfigs', 'guiNDB.db')
        conn = sqlite3.connect(db_path)
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
    # browser = await launch(headless=True, args=['--blink-settings=imagesEnabled=false'])
    browser = await launch(headless=True, executablePath='C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
                           args=['--blink-settings=imagesEnabled=false'])
    try:
        # try:
        #     response = requests.get('https://raw.githubusercontent.com/GGHHR/py_demo/master/v2rayn/init.json')
        #     content = response.text
        #     select = json.loads(content)
        #     print('Fetched JSON successfully')
        # except Exception as e:
        #     print('Failed to fetch JSON, using local file')
        #     with open('init.json', 'r') as f:
        #         select = json.load(f)
        with open('init.json', 'r') as f:
            select = json.load(f)
        for i, v in enumerate(select['select']):
            v['id'] = i + 1

        sem = asyncio.Semaphore(5)

        async def task(v, i):
            async with sem:
                try:
                    await SubGet(browser).initialize(v['url'], v.get('sel'), i + 1)
                except Exception as e:
                    print(f"{i + 1} failed: {v['url']}", e)

        tasks = [task(v, i) for i, v in enumerate(select['select'])]
        await asyncio.gather(*tasks)

        cleanup_database(sorted(not_clean_arr))
        with open('init.json', 'w') as f:
            json.dump(select, f)
    finally:
        await browser.close()


if __name__ == '__main__':
    asyncio.run(main())