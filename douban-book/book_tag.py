"""
豆瓣读书
"""
import logging
import random
import time
import urllib

import requests
from bs4 import BeautifulSoup

domain = 'http://www.douban.com'
search_url = 'http://www.douban.com/tag/{tag_name}/book?start={start_index}'
default_headers = {
    'Host': 'www.douban.com',
    'Referer': 'http://www.douban.com',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'
}

logger = logging.getLogger('main')


def parse_book_list_by_page(tag_name: str, page_num: int = 0, page_size: int = 15):
    """
    分页爬取，解析
    :param page_size:
    :param tag_name:
    :param page_num:
    :return:
    """
    search_page_url = search_url.replace('{tag_name}', urllib.parse.quote(tag_name)).replace('{start_index}',
                                                                                             str(page_num * page_size))
    response = requests.get(search_page_url, headers=default_headers)
    if response.status_code != 200:
        logger.warning('url=' + search_page_url + ', status_code=' + str(response.status_code))
        return None
    elif response.text.strip() == '':
        logger.warning('url=' + search_page_url + ', content is empty')
        return None

    # 解析
    book_list = []
    soup = BeautifulSoup(response.text, 'lxml')
    items = soup.find('div', {'class': 'mod book-list'})
    for item in items.findAll('dd'):
        try:
            title = item.find('a', {'class': 'title'}).string.strip()

            href = item.find('a', {'class': 'title'}).get('href')
            url = href.split('?')[0]
            if url.endswith('/'):
                url = url[0:-1]
            book_id = int(url.split('/')[-1])

            rating_nums = item.find('span', {'class': 'rating_nums'})
            if rating_nums:
                rating = float(rating_nums.string.strip())
            else:
                rating = 0.0

            descriptions = item.find('div', {'class': 'desc'}).string.strip().split('/')
            author = '/'.join(descriptions[0:-3]).strip()
            publish = '/'.join(descriptions[-3:]).strip()

            book_list.append({
                'id': book_id,
                'title': title,
                'author': author,
                'publish': publish,
                'rating': rating,
                'url': url,
                'tag': tag_name
            })
        except Exception as e:
            logger.warning(e)

    # 下一页
    has_next = False
    try:
        next_link = soup.find('div', {'class': 'paginator'}).find('span', {'class': 'next'})
        has_next = (next_link is not None)
    except:
        pass

    return {'url': search_page_url, 'book_list': book_list, 'has_next': has_next}


def perform(tag_name: str, max_page=20):
    """
    爬取--解析--存储
    :param tag_name:
    :param max_page:
    :return:
    """
    count = 0
    for i in range(max_page):
        book_list_dict = parse_book_list_by_page(tag_name, i)
        if book_list_dict:
            logger.warning('tag=%s, url=%s, count=%d', tag_name, book_list_dict['url'],
                           len(book_list_dict['book_list']))

            count += len(book_list_dict['book_list'])
            if not book_list_dict['has_next']:
                break
        else:
            break

        time.sleep(random.randint(1, 3))

    return count
