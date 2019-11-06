"""
评论
"""

import requests
from bs4 import BeautifulSoup

default_user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36'


def perform(book_id, book_title, book_url):
    """
    读书评论
    :param book_title:
    :param book_id:
    :param book_url:
    :return:
    """
    with requests.session() as session:
        session.headers['User-Agent'] = default_user_agent
        response = session.get(book_url)
        if response.status_code != 200:
            return None
        elif response.text.strip() == '':
            return None

        comments = parse_book_comments(response.text)
        if comments:
            for comment in comments:
                comment['book_id'] = book_id
                comment['book_title'] = book_title
            return len(comments)
        else:
            return 0


def parse_book_comments(html):
    """
    解析评论
    :param html:
    :return:
    """
    soup = BeautifulSoup(html, 'lxml')

    at_least_one = None
    book_comments = []
    comments = soup.select('div#comments li.comment-item')
    for comment in comments:
        comment_id = int(comment.select_one('span.vote-count')['id'][2:])
        vote_count = int(comment.select_one('span.vote-count').text.strip())
        all_comment = comment.select_one('p.comment-content')
        full_comment = all_comment.select_one('span.full')
        if full_comment:
            content = full_comment.text.strip()
        else:
            content = all_comment.text.strip()
        short_comment = {
            "id": comment_id,
            'vote_count': vote_count,
            'content': content
        }

        if at_least_one:
            if vote_count >= 3:
                at_least_one = short_comment
        else:
            at_least_one = short_comment

        if vote_count >= 3:
            book_comments.append(short_comment)

    if len(book_comments) == 0 and at_least_one is not None:
        book_comments.append(at_least_one)

    return book_comments
