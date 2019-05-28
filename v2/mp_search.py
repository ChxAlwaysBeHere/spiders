import os
import re
import time

import demjson
from PIL import Image
from pytesseract import pytesseract
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

resources_path = os.getcwd() + "/../resources/v2/"

driver: WebDriver = None

driver_path = '~/chromedriver/chromedriver'

mp_articles_regex_pattern = re.compile('var\s+?msgList\s*?=\s*?({[\s\S]+})\s*?;')


def init():
    global driver
    option = webdriver.ChromeOptions()
    option.add_argument('headless')
    option.add_argument(
        'User-Agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"')
    driver = webdriver.Chrome(driver_path, options=option)


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

    write_file(keyword, demjson.encode(mps), '_list_json.txt')


def perform_mp(mp_name: str, item: WebElement, main_window_handle=None):
    item.click()
    time.sleep(3)

    if main_window_handle is not None:
        window_handles = driver.window_handles
        for handle in window_handles:
            if handle != main_window_handle:
                driver.switch_to.window(handle)

    if driver.title.strip() != mp_name:
        from selenium.common.exceptions import NoSuchElementException
        try:
            driver.find_element_by_id('seccodeForm')
        except NoSuchElementException as e:
            write_error_file(mp_name, e, {'url': driver.current_url, 'html': driver.page_source})
            return

        image_code = parse_image_code()
        print(image_code)

        """
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
        """

    """
    mp_html = driver.page_source
    write_file(mp_name, mp_html, '_mp_html.txt')

    # 正则提取
    parse_mp_articles(mp_html)
    """

    driver.close()
    if main_window_handle is not None:
        driver.switch_to.window(main_window_handle)


def parse_image_code():
    current_window_size = driver.get_window_size()
    image_code = driver.find_element_by_id('seccodeImage')
    image_location = image_code.location
    image_size = image_code.size
    # region = (int(image_location['x']), int(image_location['y']), int(image_location['x'] + image_size['width']),int(image_location['y'] + image_size['height']))
    # TODO 图片大小、位置不固定
    region = (700, 600, 900, 680)

    image_code_file_name = resources_path + str(int(time.time())) + '_' + str(current_window_size['width']) + '*' + str(current_window_size['height']) + '.png'
    saved = driver.save_screenshot(image_code_file_name)
    if not saved:
        write_error_file('image_code', None, {'url': driver.current_url, 'html': driver.page_source})
        return

    image_code_file = Image.open(image_code_file_name)
    tmp = image_code_file.crop(region)
    tmp_file_path = '_'.join([image_code_file_name, str(image_location['x']), str(image_location['y']), str(image_size['width']) + '*' + str(image_size['height'])]) + '.png'
    tmp.save(tmp_file_path)

    tmp_file = Image.open(tmp_file_path)
    grayed_image_code = image_convert(tmp_file)
    image_to_string = pytesseract.image_to_string(grayed_image_code).strip()

    return image_to_string


def image_convert(image: Image.Image):
    # 传入'L'将图片转化为灰度图像
    image = image.convert('L')
    # 传入'l'将图片进行二值化处理,默认二值化阈值为127
    # 指定阈值进行转化
    count = 90
    table = []
    for i in range(256):
        if i < count:
            table.append(0)
        else:
            table.append(1)
    return image.point(table, '1')


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
        if e is not None:
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
    # try:
    #     init()
    #
    #     driver.get(
    #         'https://weixin.sogou.com/antispider/?from=http%3A%2F%2Fweixin.sogou.com%2Fweixin%3Ftype%3D1%26query%3DPython%E7%88%AC%E8%99%AB%E4%B8%8E%E7%AE%97%E6%B3%95')
    #     image_code = parse_image_code()
    #     print(image_code)
    # finally:
    #     close()
    cropped_image_code = Image.open('../resources/v2/1559010634754801000_800*600.png_353_299_100*40.png')
    converted_image_code = image_convert(cropped_image_code)
    converted_image_code.show()
    code = pytesseract.image_to_string(converted_image_code).strip()
    print(code)
