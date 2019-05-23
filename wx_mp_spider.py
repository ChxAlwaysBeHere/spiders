from v1 import mp_search as v1_mp_search, mp_article_search as v1_mp_article_search

if __name__ == '__main__':
    kw = '微信'
    v1_mp_search.extract(kw)
    v1_mp_article_search.extract(kw)
