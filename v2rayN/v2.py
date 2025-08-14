import asyncio
from playwright.async_api import async_playwright
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
            return

        page = await self.browser.new_page()
        page.set_default_navigation_timeout(60000)
        try:
            await page.goto(url, timeout=60000)
            if isinstance(sel, list) and len(sel) >= 1:
                if len(sel) == 1:
                    list_el = None
                    el = sel[0]
                else:
                    list_el = sel[0]
                    el = sel[1]

                # 如果需要通过 list_el 先跳转到链接
                if list_el:
                    try:
                        # 先等待元素出现（非阻塞失败会抛出）
                        await page.wait_for_selector(list_el, timeout=10000)
                        element = await page.query_selector(list_el)
                        if element:
                            href = await element.get_attribute('href')
                            if href:
                                # 有时候是相对路径，Playwright 会处理相对链接（基于当前url）
                                await page.goto(href, timeout=60000)
                    except Exception:
                        # 若跳转失败，继续尝试在当前页抓取
                        pass

                # 等主选择器出现并抓取所有元素文本
                await page.wait_for_selector(el, timeout=60000)

                contents = await page.eval_on_selector_all(el, "els => els.map(e => e.textContent || e.value)")

                url_pattern = re.compile(r'https?://[^\s/$.?#].[^\s]*')

                for i, content in enumerate(contents):
                    if not content:
                        continue
                    match = url_pattern.search(content)
                    if match:
                        match_url = match.group(0)
                        convert_target = "mixed" if match_url.endswith(('.yaml', '.yml')) else ""
                        num = id_
                        if i > 0:
                            async with lock:
                                num_add += 1
                                base = len(select['select']) if select and 'select' in select else 0
                                num = base + num_add
                        print(id_, num, match_url)
                        # 保持 remarks 有意义，使用 match_url 作为 remarks
                        up_sub_item(match_url, match_url, num, convert_target)
        finally:
            await asyncio.sleep(1)
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


class SubGet1:
    async def scrape_level(self, page, selectors):
        if not selectors:
            return []

        el = selectors[0]
        await page.wait_for_selector(el, timeout=60000)

        if len(selectors) == 1:
            contents = await page.eval_on_selector_all(el, "els => els.map(e => e.textContent || e.value || '')")
            url_pattern = re.compile(r'https?://[^\s/$.?#].[^\s]*')
            match_urls = []
            for content in contents:
                if content:
                    match = url_pattern.search(content)
                    if match:
                        match_urls.append(match.group(0))
            return match_urls
        else:
            elements = await page.query_selector_all(el)
            all_match_urls = []
            for element in elements:
                href = await element.get_attribute('href')
                if href:
                    full_href = await page.evaluate('(href) => new URL(href, location.href).href', href)
                    new_page = await self.browser.new_page()
                    new_page.set_default_navigation_timeout(60000)
                    try:
                        await new_page.goto(full_href, timeout=60000)
                        sub_match_urls = await self.scrape_level(new_page, selectors[1:])
                        all_match_urls.extend(sub_match_urls)
                    except Exception as e:
                        print(f"Failed to process {full_href}: {e}")
                    finally:
                        await new_page.close()
            return all_match_urls

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
            return

        page = await self.browser.new_page()
        page.set_default_navigation_timeout(60000)
        try:
            await page.goto(url, timeout=60000)
            match_urls = await self.scrape_level(page, sel)
            base = len(select['select']) if select and 'select' in select else 0
            first = True
            for match_url in match_urls:
                convert_target = "mixed" if match_url.endswith(('.yaml', '.yml')) else ""
                if first:
                    num = id_
                    first = False
                else:
                    async with lock:
                        num_add += 1
                        num = base + num_add
                print(id_, num, match_url)
                # 保持 remarks 有意义，使用 match_url 作为 remarks
                up_sub_item(match_url, match_url, num, convert_target)
        finally:
            await asyncio.sleep(1)
            await page.close()



async def main():
    global select, not_clean_arr, num_add

    # 如果你想使用已安装的 Edge，可用 executable 指定 Edge 路径，
    # Playwright 也支持 channel='msedge'（如果你用的是官方支持的 channel）
    executable = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=executable,
                                          args=['--blink-settings=imagesEnabled=false'])
        try:
            if not os.path.isfile('init.json'):
                print('init.json not found')
                return

            with open('init.json', 'r', encoding='utf-8') as f:
                select = json.load(f)
            for i, v in enumerate(select['select']):
                v['id'] = i + 1

            sem = asyncio.Semaphore(6)
            global lock
            lock = asyncio.Lock()

            async def task(v, i):
                async with sem:
                    try:

                        if v.get('sel_all'):

                            await SubGet1(browser).initialize(v['url'], v.get('sel_all'), i + 1)

                        else:
                            await SubGet(browser).initialize(v['url'], v.get('sel'), i + 1)
                    except Exception as e:
                        print(f"{i + 1} failed: {v['url']}", e)

            tasks = [task(v, i) for i, v in enumerate(select['select'])]
            await asyncio.gather(*tasks)

            cleanup_database(sorted(not_clean_arr))
        finally:
            await browser.close()


if __name__ == '__main__':
    asyncio.run(main())