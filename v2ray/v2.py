import subprocess
import os
import json
import re
import sqlite3
import urllib.request
import threading
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser

# Global variables with thread-safe access
not_clean_arr = []
num_add = 0
not_clean_lock = threading.Lock()
num_add_lock = threading.Lock()
select = None

def get_running_v2rayn_path():
    """Get the directory path of the running v2rayN.exe process using wmic."""
    try:
        output = subprocess.check_output(
            ['wmic', 'process', 'where', 'name="v2rayN.exe"', 'get', 'ExecutablePath'],
            universal_newlines=True
        )
        lines = [line.strip() for line in output.split('\n') if line.strip()]
        return os.path.dirname(lines[1]) if len(lines) > 1 else None
    except subprocess.CalledProcessError:
        print('v2rayn 未在运行')
        return None

class SimpleHTMLParser(HTMLParser):
    """Parse HTML to extract href attributes or text content."""
    def __init__(self):
        super().__init__()
        self.results = []
        self.current_tag = None
        self.target_tag = None
        self.target_attr = None

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        if self.target_tag == tag:
            for attr, value in attrs:
                if attr == self.target_attr:
                    self.results.append(value)

    def handle_data(self, data):
        if self.current_tag == self.target_tag and not self.target_attr:
            self.results.append(data.strip())

def fetch_url(url, selector=None, is_list=False):
    """Fetch and parse URL content using urllib and HTMLParser."""
    try:
        with urllib.request.urlopen(url, timeout=99999) as response:
            content = response.read().decode('utf-8')
            parser = SimpleHTMLParser()
            if selector:
                parser.target_tag = selector.split(':')[0] if ':' in selector else selector
                parser.target_attr = 'href' if is_list else None
                parser.feed(content)
                return parser.results
            return content
    except Exception as e:
        print(f'请求失败: {url}, 错误: {e}')
        return None

class SubGet:
    """Class to process subscription URLs."""
    def initialize(self, url, sel, id):
        """Initialize subscription processing."""
        global not_clean_arr, num_add, select
        with not_clean_lock:
            if id not in not_clean_arr:
                not_clean_arr.append(id)
        if not sel:
            convert_target = "mixed" if url.endswith(("yaml", "yml")) else ""
            print(id, url)
            up_sub_item(url, id, id, convert_target)
            return
        self.url = url
        self.list_el = sel[0] if sel and len(sel) > 1 else None
        self.el = sel[1] if sel and len(sel) > 1 else sel[0] if sel else None
        self.id = id
        self.start()

    def start(self):
        """Extract and process URLs."""
        global num_add, select
        content_url = self.url
        if self.list_el:
            links = fetch_url(self.url, self.list_el, is_list=True)
            content_url = links[0] if links else self.url
        contents = fetch_url(content_url, self.el) or []
        for i, content in enumerate(contents):
            url_pattern = r'https?://[^\s/$.?#].[^\s]*'
            match = re.search(url_pattern, content)
            if match:
                url = match.group(0)
                convert_target = "mixed" if url.endswith(("yaml", "yml")) else ""
                num = self.id
                if i > 0:
                    with num_add_lock:
                        num_add += 1
                        num = len(select['select']) + num_add
                print(self.id, num, url)
                up_sub_item(url, num, num, convert_target)

def up_sub_item(url, remarks, id, convert_target):
    """Insert or update subscription item in SQLite database."""
    global not_clean_arr
    with not_clean_lock:
        if id not in not_clean_arr:
            not_clean_arr.append(id)
    try:
        command = get_running_v2rayn_path()
        if command:
            db_path = os.path.join(command, 'guiConfigs', 'guiNDB.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO SubItem (remarks, url, id, convertTarget, sort)
                VALUES (?, ?, ?, ?, ?)
            ''', (str(remarks), url, str(id), convert_target, id))
            conn.commit()
            conn.close()
        else:
            print('v2rayn 未在运行')
    except Exception as e:
        print(f'处理路径时出现错误：{e}')

def cleanup_database(num):
    """Remove database entries not in the current list."""
    print(num)
    try:
        command = get_running_v2rayn_path()
        if command:
            db_path = os.path.join(command, 'guiConfigs', 'guiNDB.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            placeholders = ', '.join('?' for _ in num)
            cursor.execute(f'DELETE FROM SubItem WHERE sort NOT IN ({placeholders})', num)
            conn.commit()
            print(f'成功删除排序不在 {num} 内的记录。已删除记录数: {cursor.rowcount}')
            conn.close()
        else:
            print('v2rayn 未在运行。')
    except Exception as e:
        print(f'清理操作失败: {e}')

def main():
    """Main function to manage subscriptions."""
    global select, not_clean_arr, num_add
    try:
        url = 'https://raw.githubusercontent.com/GGHHR/node_demo/master/v2rayn/init.json'
        print(f'请求json中：{url}')
        with urllib.request.urlopen(url, timeout=99999) as response:
            select = json.loads(response.read().decode('utf-8'))
        print('请求成功')
    except Exception:
        with open('./init.json', 'r', encoding='utf-8') as f:
            select = json.load(f)
        print('失败了，用本地的json文件')

    def worker(v, i):
        try:
            v['id'] = i + 1
            SubGet().initialize(v['url'], v.get('sel'), i + 1)
        except Exception as e:
            print(f'{i + 1} 失败：{v["url"]} 错误：{e}')

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(worker, v, i) for i, v in enumerate(select['select'])]
        for future in futures:
            future.result()

    cleanup_database(sorted(not_clean_arr))
    with open('./init.json', 'w', encoding='utf-8') as f:
        json.dump(select, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    main()