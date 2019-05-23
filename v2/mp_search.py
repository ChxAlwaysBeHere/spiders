import os
import re
import time

import demjson
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

resources_path = os.getcwd() + "/../resources/v2/"

driver = None

mp_articles_regex_pattern = re.compile('var\s+?msgList\s*?=\s*?({[\s\S]+})\s*?;')


def init():
    global driver
    option = webdriver.ChromeOptions()
    # option.add_argument('headless')
    option.add_argument(
        'User-Agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"')
    driver = webdriver.Chrome('/Users/chenxi/chromedriver/chromedriver', options=option)


def close():
    if driver:
        driver.quit()


def perform(keyword):
    # 搜狗首页
    driver.get('https://www.sogou.com')
    time.sleep(3)

    # 搜狗微信页
    driver.get('http://weixin.sogou.com/')
    time.sleep(3)

    # 模拟"公众号"搜索点击
    div = driver.find_element_by_css_selector('form#searchForm>div')
    div.find_element_by_css_selector('input#query').send_keys(keyword)
    time.sleep(3)
    div.find_element_by_css_selector('input.swz2').click()
    time.sleep(3)

    # 公众号搜索列表页
    write_file(keyword, driver.page_source, '_list_html.txt')
    main_window = driver.current_window_handle

    # 搜索列表页解析
    items = driver.find_elements_by_css_selector('div.txt-box')
    mps = []
    for item in items:
        item_id = item.find_element_by_css_selector('p.info>label')
        item_name = item.find_element_by_css_selector('p.tit>a')
        item_href = item.find_element_by_css_selector('p.tit>a')

        mp = {
            'id': str(item_id.text),
            'name': str(item_name.text),
            'href': str(item_href.get_attribute('href'))
        }
        mps.append(mp)

        perform_mp(mp['name'], item_href, main_window_handle=main_window)
        break

    write_file(keyword, demjson.encode(mps), '_list_json.txt')


def perform_mp(mp_name: str, item: WebElement, main_window_handle=None):
    item.click()
    time.sleep(3)

    if main_window_handle is not None:
        window_handles = driver.window_handles
        for handle in window_handles:
            if handle != main_window_handle:
                driver.switch_to.window(handle)

    if driver.title.strip() == mp_name:
        mp_html = driver.page_source
        write_file(mp_name, mp_html, '_mp_html.txt')

        # 正则提取
        parse_mp_articles(mp_html)

    else:
        """
        被拦截的情况，需要输入验证码，尝试进行验证码解析（未验证此处理）
        """
        image_code = driver.find_element_by_id('seccodeImage')
        # 移动到该元素
        action = ActionChains(driver).move_to_element(image_code)
        # 右键点击该元素
        action.context_click(image_code)
        # 点击键盘向下箭头
        action.send_keys(Keys.ARROW_DOWN)
        # 键盘输入V保存图
        action.send_keys('v')
        time.sleep(3)
        # 执行保存
        action.perform()

    driver.close()
    if main_window_handle is not None:
        driver.switch_to.window(main_window_handle)


def parse_mp_articles(article_html):
    search_target = mp_articles_regex_pattern.search(article_html)
    if search_target is not None:
        return demjson.decode(search_target.group(1))
    else:
        return None


def write_file(keyword, data, suffix='.txt'):
    if data is None or not isinstance(data, str) or data.isspace():
        return

    with open(resources_path + keyword + suffix, 'w') as file:
        file.write(data)


def write_error_file(keyword: str, e: Exception, data: dict):
    with open(resources_path + 'error.txt', 'a') as file:
        file.write(keyword + '\r\n')
        file.write('-' * 30 + '\r\n')
        file.write(data['url'] + '\r\n')
        file.write('-' * 30 + '\r\n')
        file.write(data['html'] + '\r\n')
        file.write('-' * 30 + '\r\n')
        file.write(str(e) + '\r\n')
        file.write('=' * 30 + '\r\n')


def extract(keyword):
    try:
        init()

        perform(keyword)

    except Exception as e:
        print(e)
        write_error_file(keyword, e, {'url': driver.current_url, 'html': driver.page_source})
    finally:
        close()


if __name__ == '__main__':
    # extract('华为')
    with open(resources_path + 'demo.txt') as file:
        html = file.read()
        parse_mp_articles(html)
