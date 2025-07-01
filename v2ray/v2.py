import requests
import json


def first():
    url = 'https://raw.githubusercontent.com/GGHHR/node_demo/master/v2rayn/init.json'
    response = requests.get(url)
    response.encoding = 'utf-8'
    # Parse string as JSON and return
    return response.json()
result = first()

# 获取网页指定内容
def find(obj):
    if 'sel' in obj:
        print(obj['sel'])
        return obj['sel']
    else:
        print(obj['url'])

for item in result['select']:
    find(item)


