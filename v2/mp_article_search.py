"""
搜狗公众号文章搜索：http://mp.weixin.qq.com/profile?src=3&timestamp=1558319409&ver=1&signature=pZq4saj68C6akulKCjQR9GdMksJszjvOKxYYlq0EymtjetlJM7h5hVtgo1W-D53sZEHBJjsL5V8tGtLgZcd5zQ==
"""

import os
import random
import time

import demjson
import requests

from v1 import constants


def load_seeds(seeds_file):
    if not os.path.exists(seeds_file):
        print("file not exists: " + seeds_file)
        return

    with open(seeds_file) as file:
        mp_list_str = file.read()
        return demjson.decode(mp_list_str)


def get_html(url, headers=constants.headers, cookies=None):
    cookies['SUV'] = ''.join([str(int(time.time() * 1000000) + random.randint(0, 1000))])
    response = requests.get(url, headers=headers, cookies=cookies, verify=False)
    print(response.cookies)
    if response.status_code != 200:
        print('response exception: url=' + url)
        return None

    if response.apparent_encoding is None:
        response.encoding = 'utf-8'
    else:
        response.encoding = response.apparent_encoding

    return response.text


def write_html(name, data):
    if data is None or not isinstance(data, str) or data.isspace():
        return

    with open(name + '_article.txt', 'w') as file:
        file.write(data)


def extract(keyword):
    seeds_file = keyword + '_mp.txt'
    seeds = load_seeds(seeds_file)
    for seed in seeds['mps']:
        content = get_html(seed['link'], cookies=seeds['cookies'])
        write_html(seed['name'], content)
        break
