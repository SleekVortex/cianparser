import re
import bs4
import time
import random
import socket
import asyncio
import urllib.error
import urllib.request

from random import choice
from curl_cffi import requests
from curl_cffi.requests import AsyncSession
from fake_useragent import UserAgent


def build_proxy_string(proxy: str) -> str:
    if "@" in proxy:
        assert re.match(r"\w+:\w+@\d+\.\d+\.\d+\.\d+\.:\d+", proxy) is not None
    else:
        assert re.match(r"\d+\.\d+\.\d+\.\d+\.:\d+", proxy) is not None

    return f"http://{proxy}"

class ProxyPool:
    def __init__(self, proxies):
        self.__proxy_pool__ = [] if proxies is None else proxies
        self.__current_proxy__ = None
        self.__page_html__ = None

    def __is_captcha__(self):
        page_soup = bs4.BeautifulSoup(self.__page_html__, "html.parser")
        return page_soup.text.find("Captcha") > 0

    def __is_available_proxy__(self, url, proxy):
        proxy_string = build_proxy_string(proxy)        
        # Use the formatted proxy for both http and https
        proxy_handler = urllib.request.ProxyHandler({
            "http": proxy_string,
            "https": proxy_string
        })

        # Create an opener with the proxy
        opener = urllib.request.build_opener(proxy_handler)
        opener.addheaders = [("User-agent", UserAgent().random)]

        # Install the opener as the default opener for urllib
        urllib.request.install_opener(opener)

        try:
            self.__page_html__ = urllib.request.urlopen(urllib.request.Request(url))
        except Exception as detail:
            print(f"Error: {detail}...")
            return False

        return True

    def is_empty(self):
        return len(self.__proxy_pool__) == 0

    def get_available_proxy(self, url):
        print("The process of checking the proxies... Search an available one among them...")

        socket.setdefaulttimeout(5)
        found_proxy = False
        while len(self.__proxy_pool__) > 0 and found_proxy is False:
            proxy = random.choice(self.__proxy_pool__)

            is_available = self.__is_available_proxy__(url, proxy)
            is_captcha = self.__is_captcha__() if is_available else None

            if not is_available or is_captcha:
                if is_captcha:
                    print(f"proxy {proxy}: there is captcha.. trying another")
                else:
                    print(f"proxy {proxy}: unavailable.. trying another..")
                self.__proxy_pool__.remove(proxy)
                time.sleep(4)
                continue

            print(f"proxy {proxy}: available.. stop searching")
            self.__current_proxy__, found_proxy = proxy, True

        if self.__current_proxy__ is None:
            print(f"there are not available proxies..", end="\n\n")

        return self.__current_proxy__


class ProxyPoolAsync:
    def __init__(self, proxies, use_local_ip=True):
        self.proxy_pool = self.get_proxy_pool(proxies, use_local_ip)
        self.url = 'https://cian.ru/'

    @staticmethod
    def is_captcha(page_html):
        page_soup = bs4.BeautifulSoup(page_html, "html.parser") #Проверка на капчу
        return "Captcha" in page_soup.text
    
    def get_proxy_pool(self, proxies, use_local_ip):
        if proxies:
            pool = [f'http://{proxy}' for proxy in proxies]
        else:
            pool = []
        if use_local_ip:
            pool.append(None) #Добавление отстутствия прокси, то есть локальный адрес
        return pool

    async def is_available_proxy(self, url, proxy):
        headers = {"User-Agent": UserAgent().random}
        try:
            async with AsyncSession() as s:
                response = await s.get(url, headers=headers, proxy=proxy, timeout=15)
                if response.status_code == 200:
                    page_html = response.text
                    return page_html and not self.is_captcha(page_html)
                else:
                    print(f"Proxy {proxy}: Status code {response.status_code}")
                    return False
        except requests.exceptions.RequestException as e: # Более специфичное исключение
            print(f"Proxy {proxy}: Error: {e}")
            return False
        except Exception as e: # Общее исключение на случай других ошибок
            print(f"Proxy {proxy}: Unexpected Error: {e}")
            return False

    async def get_available_proxies(self):
        print('Проверка прокси')
        tasks = [self.is_available_proxy(self.url, proxy) for proxy in self.proxy_pool]
        is_available_proxies = await asyncio.gather(*tasks)
        available_proxies = [proxy for proxy, is_available in zip(self.proxy_pool, is_available_proxies) if is_available]
        if not available_proxies:
            raise Exception("No available ips found.")
        self.proxy_pool = available_proxies
