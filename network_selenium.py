# -*- coding: utf-8 -*-
"""
All code involving requests and responses over the http network
must be abstracted in this file.
"""
__title__ = 'newspaper'
__author__ = 'Lucas Ou-Yang'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014, Lucas Ou-Yang'

import logging
import requests

from .configuration import Configuration
from .mthreading import ThreadPool
from .settings import cj

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import copy

log = logging.getLogger(__name__)
#팬텀js가 있는 경로 or 웹드라이버로 경로를 지정해 줄 것
driver = webdriver.PhantomJS('C:/Users/USER/AppData/Local/Programs/Python/Python36-32/Lib/site-packages/newspaper/phantomjs-2.1.1-windows/bin/phantomjs')
# driver = webdriver.Chrome('C:/Users/USER/Desktop/Office/selenium/chromedriver_win32/chromedriver')
FAIL_ENCODING = 'ISO-8859-1'

def get_request_kwargs(timeout, useragent):
    """This Wrapper method exists b/c some values in req_kwargs dict
    are methods which need to be called every time we make a request
    """
    return {
        'headers': {'User-Agent': useragent},
        'cookies': cj(),
        'timeout': timeout,
        'allow_redirects': True
    }


def get_html(url, config=None, response=None):
    """HTTP response code agnostic
    """
    try:
        return get_html_2XX_only(url, config, response)
    except requests.exceptions.RequestException as e:
        log.debug('get_html() error. %s on URL: %s' % (e, url))
        return ''


def get_html_2XX_only(url, config=None, response=None):
    """Consolidated logic for http requests from newspaper. We handle error cases:
    - Attempt to find encoding of the html by using HTTP header. Fallback to
      'ISO-8859-1' if not provided.
    - Error out if a non 2XX HTTP response code is returned.
    """
    config = config or Configuration()
    useragent = config.browser_user_agent
    timeout = config.request_timeout

    if response is not None:
        return _get_html_from_response(response)

    try:
        response = requests.get(
            url=url, **get_request_kwargs(timeout, useragent))
    except requests.exceptions.RequestException as e:
        log.debug('get_html_2XX_only() error. %s on URL: %s' % (e, url))
        return ''

    html = _get_html_from_response(response)

    if config.http_success_only:
        # fail if HTTP sends a non 2XX response
        response.raise_for_status()

    return html


def _get_html_from_response(response):
    if response.encoding != FAIL_ENCODING:
        # return response as a unicode string
        html = response.text
    else:
        # don't attempt decode, return response in bytes
        html = response.content
    return html or ''

def find_real_frame(html):
    global driver
    frames = driver.find_elements_by_xpath('//frame[@src]')
    print(len(frames))
    i = 1
    for frame in frames:
        try:
            driver.switch_to.frame(driver.find_element_by_xpath('//frame[@src][' + str(i) + ']'))
            wait = WebDriverWait(driver, 30)
            try:
                wait.until(lambda driver: driver.execute_script('return jQuery.active == 0'))
            except:
                pass
            c_html = find_real_frame(driver.page_source)
            if len(html) < len(driver.page_source): # 페이지 크기로 비교
                html = driver.page_source
            if len(html) < c_html:
                html = c_html
            driver.switch_to.default_content()
        except:
            pass

        i = i + 1

    return html

def get_html_from_selenium(url):
    html = ''
    global driver
    driver.get(url)
    wait = WebDriverWait(driver, 30)
    try:
        wait.until(lambda driver: driver.execute_script('return jQuery.active == 0'))
    except:
        pass

    html = find_real_frame(driver.page_source)
    print(html)
    return html



class MRequest(object):
    """Wrapper for request object for multithreading. If the domain we are
    crawling is under heavy load, the self.resp will be left as None.
    If this is the case, we still want to report the url which has failed
    so (perhaps) we can try again later.
    """
    def __init__(self, url, config=None):
        self.url = url
        self.config = config
        config = config or Configuration()
        self.useragent = config.browser_user_agent
        self.timeout = config.request_timeout
        self.resp = None

    def send(self):
        try:
            self.resp = requests.get(self.url, **get_request_kwargs(
                                     self.timeout, self.useragent))
            if self.config.http_success_only:
                self.resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            log.critical('[REQUEST FAILED] ' + str(e))


def multithread_request(urls, config=None):
    """Request multiple urls via mthreading, order of urls & requests is stable
    returns same requests but with response variables filled.
    """
    config = config or Configuration()
    num_threads = config.number_threads
    timeout = config.thread_timeout_seconds

    pool = ThreadPool(num_threads, timeout)

    m_requests = []
    for url in urls:
        m_requests.append(MRequest(url, config))

    for req in m_requests:
        pool.add_task(req.send)

    pool.wait_completion()
    return m_requests
