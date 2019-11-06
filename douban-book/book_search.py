import re
import urllib

import requests
from bs4 import BeautifulSoup

default_headers = {
    'Host': 'www.douban.com',
    'Referer': 'http://www.douban.com',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'
}

book_search_url = 'https://search.douban.com/book/subject_search?search_text=%s'


# data_regex_pattern = r'window\.__DATA__\s*=\s*"([\s\S]+?)";'


def search_book(book_name: str):
    """
    根据书名搜索，取搜索结果页的第一条数据
    :param book_name: 书名
    :return:
    """
    if book_name is None or len(book_name) == 0:
        raise Exception("书名不能为空")

    response = requests.get(book_search_url % urllib.parse.quote(book_name), headers=default_headers)
    if response.status_code != 200:
        raise Exception("请求失败")

    soup = BeautifulSoup(response.text, 'lxml')
    result_list = soup.select_one('div.result-list')
    results = result_list.select('div.result')

    books = []
    for result in results:
        try:
            anchor = result.select_one('div.pic>a.nbg')
            if anchor is None:
                continue

            title = anchor['title']
            url = urllib.parse.parse_qs(urllib.parse.urlsplit(anchor['href']).query)['url'][0]
            book_id = re.search('/(\d+)/', url).group(1)
            img = result.select_one('div.pic>a.nbg>img')['src']
            author_publish = result.select_one('div.rating-info>span.subject-cast').string.split('/', 1)
            author = author_publish[0].strip()
            publish = author_publish[1].strip()
            rating = result.select_one('div.rating-info>span.rating_nums').string

            books.append({
                'id': int('1' + book_id),
                'douban_id': book_id,
                'title': title,
                'author': author,
                'publish': publish,
                'rating': rating,
                'url': url,
                'img': img
            })
        except Exception:
            pass

    if books:
        return books[0]
    else:
        return None
