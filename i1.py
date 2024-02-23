import os
import sqlite3
import json
import re
import subprocess
import asyncio
from pyppeteer import launch

async def get_running_v2rayn_path():
    command = 'v2rayn.exe'
    process_list = subprocess.run(['tasklist', '/fo', 'csv', '/nh'], capture_output=True, text=True)
    if command in process_list.stdout:
        return os.path.dirname(process_list.stdout.split(command)[0].split('"')[1])
    else:
        print('v2rayn is not running.')
        return None

class SubGet:
    def __init__(self, browser):
        self.browser = browser

    async def initialize(self, url, sel, remarks, id):
        if sel is None:
            convert_target = ""
            if url.endswith("yaml") or url.endswith("yml"):
                convert_target = "mixed"
            print(id, url)
            await UpSubItem(url, remarks, id, convert_target)
            return

        self.url = url
        self.list_el = sel[0]
        self.el = sel[1]
        self.remarks = remarks
        self.id = id

        await self.start()

    async def start(self):
        page = await self.browser.newPage()
        await page.goto(self.url, {'timeout': 99999})
        content = ""
        if self.list_el:
            await page.waitForSelector(self.list_el, {'timeout': 99999})
            content = await page.evaluate('(el) => el.href', await page.querySelector(self.list_el))
            await page.goto(content, {'timeout': 99999})
        await page.waitForSelector(self.el, {'timeout': 99999})
        content = await page.evaluate('(el) => el.textContent', await page.querySelector(self.el))
        url_pattern = re.compile(r'https?://[^\s/$.?#].[^\s]*', re.IGNORECASE)
        match = url_pattern.search(content)
        match = match.group(0) if match else None
        convert_target = "mixed" if match and (match.endswith("yaml") or match.endswith("yml")) else ""
        print(self.remarks, match)
        await UpSubItem(match, self.remarks, self.id, convert_target)
        await page.close()

async def UpSubItem(url, remarks, id, convert_target):
    try:
        command = await get_running_v2rayn_path()
        if command:
            output_value = os.path.join(command, 'guiConfigs/guiNDB.db')
            db = sqlite3.connect(output_value)
            cursor = db.cursor()
            cursor.execute('INSERT OR REPLACE INTO SubItem (remarks, url, id, convertTarget, sort) VALUES (?, ?, ?, ?, ?)',
                           (remarks, url, id, convert_target, id))
            db.commit()
            db.close()
        else:
            print('v2rayn is not running.')
        return command
    except Exception as e:
        print(f'Error while processing path: {e}')

async def main():
    try:
        browser = await launch(headless=False, slowMo=250, executablePath='C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe')
        print('Requesting remote json...')
        page = await browser.newPage()
        url = 'https://raw.githubusercontent.com/GGHHR/node_demo/master/v2rayn%E8%AE%A2%E9%98%85/init.json'
        await page.goto(url, {'timeout': 99999})
        await page.waitForSelector('pre', {'timeout': 99999})
        content = await page.evaluate('(el) => el.textContent', await page.querySelector('pre'))
        select = json.loads(content)
        await page.close()
        print('Request successful.')
    except Exception as e:
        select = json.loads(open('./init.json', 'r', encoding='utf-8').read())
        print('Request failed, using local json file.')

    for i, v in enumerate(select['select']):
        v['id'] = i + 1
        try:
            await SubGet(browser).initialize(v['url'], v['sel'], i + 1, i + 1)
        except Exception as e:
            print(f'Error at {i + 1}: {v["url"]}')

    await cleanup_database(len(select['select']))
    await open('./init.json', 'w', encoding='utf-8').write(json.dumps(select))
    await browser.close()
    await asyncio.sleep(0)

async def cleanup_database(num):
    try:
        command = await get_running_v2rayn_path()
        if command:
            output_value = os.path.join(command, 'guiConfigs/guiNDB.db')
            db = sqlite3.connect(output_value)
            cursor = db.cursor()
            cursor.execute(f'DELETE FROM SubItem WHERE sort > {num}')
            db.commit()
            db.close()
            print(f'Successfully deleted records with sort greater than {num}.')
        else:
            print('v2rayn is not running.')
    except Exception as e:
        print(f'Cleanup operation failed: {e}')

if __name__ == '__main__':
    asyncio.run(main())
