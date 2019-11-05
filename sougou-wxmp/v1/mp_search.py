import os

import demjson
import requests
from bs4 import BeautifulSoup
from requests.cookies import RequestsCookieJar

from v1 import constants


def get_html(keyword, page=1):
    params_data = {'query': keyword, 'page': str(page), 's_from': 'input', 'ie': 'utf8'}
    response = requests.get(constants.search_url, params=params_data, headers=constants.headers, verify=False)

    if response.status_code != 200:
        return None

    if response.apparent_encoding is None:
        response.encoding = 'utf-8'
    else:
        response.encoding = response.apparent_encoding

    return {'kw': keyword, 'headers': response.headers, 'cookies': response.cookies, 'text': response.text}


def parse_headers(headers):
    return headers


def parse_cookies(cookies):
    if isinstance(cookies, RequestsCookieJar):
        return cookies

    if isinstance(cookies, dict):
        return requests.utils.cookiejar_from_dict(dict)

    if isinstance(cookies, str):
        cookies_dict = {}
        for cookie in cookies.split(';'):
            kv = cookie.split('=', 2)
            cookies_dict[kv[0].strip()] = kv[1].strip()
        return cookies_dict

    return None


def parse_mp(text):
    items = []

    if text is None:
        return items

    soup = BeautifulSoup(text, 'lxml')
    targets = soup.select('div.txt-box')

    for target_item in targets:
        item_info = {}

        link_item = target_item.select('p.tit>a')
        if link_item:
            item_info['link'] = link_item[0]['href']
            if not item_info['link'].startswith('http://') or not item_info['link'].startswith('https://'):
                item_info['link'] = constants.domain + item_info['link']
            item_info['name'] = link_item[0].text

        info_item = target_item.select('p.info>label')
        if info_item:
            item_info['id'] = info_item[0].string

        items.append(item_info)

    return items


def write_html(keyword, data):
    if data is None or not isinstance(data, str) or data.isspace():
        return

    with open(keyword + '_html.txt', 'w') as file:
        file.write(data)


def read_html(keyword):
    file_name = keyword + '_html.txt'
    if not os.path.exists(file_name):
        return None

    with open(file_name) as file:
        return file.read()


def store_mp(kw, mps, headers=None, cookies=None):
    with open(kw + '_mp.txt', 'w') as file:
        data = {}

        if headers is not None:
            data['headers'] = headers
        else:
            data['headers'] = []

        if cookies is not None:
            data['cookies'] = cookies
        else:
            data['cookies'] = []

        if isinstance(mps, list) or isinstance(mps, tuple):
            data['mps'] = mps
        else:
            data['mps'] = []

        file.write(demjson.encode(data))


def extract(keyword):
    data = get_html(keyword)
    write_html(keyword, data['text'])

    mp_search_list = parse_mp(data['text'])
    request_headers = parse_headers(data['headers'])
    cookies = parse_cookies(data['cookies'])

    store_mp(keyword, mp_search_list, headers=request_headers, cookies=cookies)
