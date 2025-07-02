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
        if 'yaml' in obj['url']:
            print(obj['url'])


# 获取json
result = first()

for item in result['select']:
    find(item)


