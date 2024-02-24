import asyncio
import sqlite3
from pyppeteer import launch
import psutil
from pathlib import Path
import json

async def get_running_v2rayn_root_path():
    for proc in psutil.process_iter(attrs=['pid', 'name']):
        if 'v2rayN' in proc.info['name']:
            return Path(proc.exe()).parent
    print('V2RayN is not running')
    return None
async def up_sub_item(url, remarks, id, convert_target, command):
    if command:
        output_value = Path(command) / 'guiConfigs/guiNDB.db'
        db = sqlite3.connect(str(output_value))
        insert_or_update_sql = """INSERT OR REPLACE INTO SubItem (remarks, url, id, convertTarget, sort) VALUES (?, ?, ?, ?, ?)"""
        try:
            db.execute(insert_or_update_sql, (remarks, url, id, convert_target, id))
            db.commit()
        except Exception as e:
            print('Error:', e)
        finally:
            db.close()
    else:
        print('v2rayn is not running')

class SubGet:
    def __init__(self, browser):
        self.browser = browser

    async def initialize(self, url, sel, remarks, id):
        if sel is None:
            convert_target = ""
            if url.endswith(("yaml", "yml")):
                convert_target = "mixed"
            print(id, url)
            await up_sub_item(url, remarks, id, convert_target, await get_running_v2rayn_root_path())
        else:
            self.url = url
            self.listEl = sel[0]
            self.el = sel[1]
            self.remarks = remarks
            self.id = id
            await self.start()

    async def start(self):
        page = await self.browser.newPage()
        await page.goto(self.url, {'timeout': 99999})
        content = ''
        if self.listEl:
            await page.waitForSelector(self.listEl, {'timeout': 99999})
            content = await page.evaluate(f'(element) => document.querySelector("{self.listEl}").href')
            await page.goto(content, {'timeout': 99999})

        await page.waitForSelector(self.el, {'timeout': 99999})
        content = await page.evaluate(f'(element) => document.querySelector("{self.el}").textContent')

        url_pattern = r'https?://[^\s/$.?#].[^\s]*'
        match = re.search(url_pattern, content)[0]
        convert_target = ""
        if match.endswith(("yaml", "yml")):
            convert_target = "mixed"
        print(self.remarks, match)
        await up_sub_item(match, self.remarks, self.id, convert_target, await get_running_v2rayn_root_path())
        await page.close()

async def main():
    browser = await launch(headless=True, slowMo=250, executablePath='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe')
    select = []
    try:
        print('Requesting remote json')
        page = await browser.newPage()
        url = 'https://raw.githubusercontent.com/GGHHR/node_demo/master/v2rayn订阅/init.json'
        await page.goto(url, {'timeout': 99999})
        await page.waitForSelector('pre', {'timeout': 99999})
        content = await page.evaluate('(element) => element.textContent', 'pre')
        select = json.loads(content)
        await page.close()
        print('Request successful')
    except Exception as e:
        with open('./init.json', 'r', encoding='utf-8') as f:
            select = json.load(f)
        print('Request failed, using local json file')

    await asyncio.gather(*[SubGet(browser).initialize(v['url'], v.get('sel'), i + 1, i + 1) for i, v in enumerate(select['select'])])

    await browser.close()

asyncio.run(main())