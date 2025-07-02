import os
import time

import psutil
import requests


def first():
    url = 'https://raw.githubusercontent.com/GGHHR/node_demo/master/v2rayn/init.json'
    response = requests.get(url)
    return response.json()


# 获取网页指定内容
def find(obj):
    if 'sel' in obj:
        return obj['sel']
    else:
        if 'yaml' in obj['url'] or 'yml' in obj['url']:
            print(obj['url'])


# 获取json
# result = first()

# for item in result['select']:
#     find(item)

def get_v2rayN_process():
    for proc in psutil.process_iter(['name', 'exe']):
        if proc.info['name'] == 'v2rayN.exe':
            exe_path = proc.info['exe']
            if exe_path and os.path.exists(exe_path):
                os.path.dirname(exe_path)
                return os.path.dirname(exe_path)
    return None
#获取v2ray路径
print(get_v2rayN_process()+r'\guiConfigs\guiNDB.db')

# time.sleep(5000)