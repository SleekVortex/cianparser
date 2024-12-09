import bs4
import time
import asyncio
import pathlib
import numpy as np
import pandas as pd

from pprint import pprint
from datetime import datetime
from transliterate import translit
from fake_useragent import UserAgent
from curl_cffi.requests import AsyncSession, Session

from cianparser.helpers import (
    union_dicts,
    define_author,
    define_location_data,
    define_specification_data,
    define_deal_url_id,
    define_price_data
)
from cianparser.flat.page import FlatPageParser
from cianparser.base_list import BaseListPageParser
from cianparser.constants import FILE_NAME_FLAT_FORMAT
from cianparser.flat.page import FlatPageParserAsync


class FlatListPageParser(BaseListPageParser):
    def build_file_path(self):
        now_time = datetime.now().strftime("%d_%b_%Y_%H_%M_%S_%f")
        file_name = FILE_NAME_FLAT_FORMAT.format(self.accommodation_type, self.deal_type, self.start_page, self.end_page, translit(self.location_name.lower(), reversed=True), now_time)
        return pathlib.Path(pathlib.Path.cwd(), file_name.replace("'", ""))

    def parse_list_offers_page(self, html, page_number: int, count_of_pages: int, attempt_number: int):
        list_soup = bs4.BeautifulSoup(html, 'html.parser')

        if list_soup.text.find("Captcha") > 0:
            print(f"\r{page_number} page: there is CAPTCHA... failed to parse page...")
            return False, attempt_number + 1, True

        header = list_soup.select("div[data-name='HeaderDefault']")
        if len(header) == 0:
            return False, attempt_number + 1, False

        offers = list_soup.select("article[data-name='CardComponent']")
        print("")
        print(f"\r {page_number} page: {len(offers)} offers", end="\r", flush=True)

        if page_number == self.start_page and attempt_number == 0:
            print(f"Collecting information from pages with list of offers", end="\n")

        for ind, offer in enumerate(offers):
            self.parse_offer(offer=offer)
            self.print_parse_progress(page_number=page_number, count_of_pages=count_of_pages, offers=offers, ind=ind)

        time.sleep(2)

        return True, 0, False

    def parse_offer(self, offer: bs4.BeautifulSoup):
        common_data = dict()
        common_data["url"] = offer.select("div[data-name='LinkArea']")[0].select("a")[0].get('href')
        common_data["location"] = self.location_name
        common_data["deal_type"] = self.deal_type
        common_data["accommodation_type"] = self.accommodation_type

        author_data = define_author(block=offer)
        location_data = define_location_data(block=offer, is_sale=self.is_sale())
        price_data = define_price_data(block=offer)
        specification_data = define_specification_data(block=offer)

        if define_deal_url_id(common_data["url"]) in self.result_set:
            return

        page_data = dict()
        if self.with_extra_data:
            flat_parser = FlatPageParser(session=self.session, url=common_data["url"])
            page_data = flat_parser.parse_page()
            time.sleep(4)

        self.count_parsed_offers += 1
        self.define_average_price(price_data=price_data)
        self.result_set.add(define_deal_url_id(common_data["url"]))
        self.result.append(union_dicts(author_data, common_data, specification_data, price_data, page_data, location_data))

        if self.with_saving_csv:
            self.save_results()


class FlatListPageParserAsync(BaseListPageParser):
    def __init__(self,
                accommodation_type: str, deal_type: str, rent_period_type, location_name: str,
                with_saving_csv=False, with_extra_data=False,
                object_type=None, additional_settings=None, proxies: list = None):
        super().__init__(
                        accommodation_type, deal_type, rent_period_type, location_name,
                        with_saving_csv, with_extra_data,
                        object_type, additional_settings
        )
        self.proxies = proxies if proxies is not None else [None,]

    
    def close_session(self):
        if self.__session__:
            self.__session__.close()
            self.__session__ = None  
    
    def __split_offers_on_proxies__(self, offers):
        """
            Метод разделяет ссылки на прокси для асинхронного парсинга с разных IP.
        """
        offers = list(map(str, offers))

        # Перемешиваем массив случайным образом
        num_groups = len(self.proxies)
        np.random.shuffle(offers)
        # Определяем размер каждой группы
        group_size = len(offers) // num_groups

        groups = np.array_split(offers, num_groups)
        return tuple(zip(self.proxies, groups))


    def build_file_path(self):
        now_time = datetime.now().strftime("%d_%b_%Y_%H_%M_%S_%f")
        file_name = FILE_NAME_FLAT_FORMAT.format(
            self.accommodation_type,
            self.deal_type,
            self.start_page,
            self.end_page,
            translit(self.location_name.lower(), reversed=True),
            now_time
        )
        file_name = file_name.replace("'", "")

        # Create the 'data' directory if it doesn't exist
        data_dir = pathlib.Path.cwd() / 'data'
        data_dir.mkdir(exist_ok=True)

        # Return the path to the new file within the 'data' directory
        return data_dir / file_name
    
    def parse_list_page_ordinary(self, list_soup):
        """
            Метод парсит главную страницу офферов. Когда она стандартная.        
        """
        offers = list_soup.select("article[data-name='CardComponent']")
        return offers

    def parse_list_page_unusual(self, list_soup):
        """
            Метод парсит главную страницу офферов. Когда она нестандартная.        
        """
        offers = list_soup.select("section[data-name='CardContainer']")
        return offers

    def parse_offer_ordinary(self, offer):
        """
            Метод парсит оффер. Когда он стандартный.        
        """
        common_data = dict()
        common_data["url"] = offer.select_one("div[data-name='LinkArea'] a").get('href')
        return common_data

    def parse_offer_unusual(self, offer):
        """
            Метод парсит оффер. Когда он нестандартный.        
        """
        common_data = dict()
        short_url = offer.select_one("div[data-name='LinkArea'] a").get('href')
        full_url = 'https://cian.ru' + short_url
        common_data["url"] = full_url
        return common_data

    def __get_is_ordinary_page__(self, list_soup) -> None:
        """
            Метод проверяет, является ли страница стандартной.
        """
        header = list_soup.select_one("div[data-name='HeaderDefault']")
        if not header:
            self.__is_ordinary_page__ = False
        else:
            self.__is_ordinary_page__ = True

    def __get_parse_functions__(self):
        """
            Метод устанавливает функции парсинга в зависимости от того,
                является ли страница стандартной.
        """
        if self.__is_ordinary_page__:
            self.parse_list_func = self.parse_list_page_ordinary
            self.parse_offer_func = self.parse_offer_ordinary
        else:
            self.parse_list_func = self.parse_list_page_unusual
            self.parse_offer_func = self.parse_offer_unusual
    
    async def parse_list_offers_page(self, html, page_number: int, count_of_pages: int, attempt_number: int):

        list_soup = bs4.BeautifulSoup(html, 'html.parser')

        if list_soup.text.find("Captcha") > 0:
            print(f"\r{page_number} page: there is CAPTCHA... failed to parse page...")
            return False, attempt_number + 1, True
        
        # Определение типа страницы
        self.__get_is_ordinary_page__(list_soup)
        # Определение функци парсинга
        self.__get_parse_functions__()

        # Парсинг офферов в зависимости от типа страницы
        offers = self.parse_list_func(list_soup)

        if not offers:
            print('Страницы закончились')
            return True, 0, True 

        # print("")
        # print(f"\r {page_number} page: {len(offers)} offers", end="\r", flush=True)

        if page_number == self.start_page and attempt_number == 0:
            print(f"Collecting information from pages with list of offers", end="\n")

        # Разделяем объявления по прокси
        proxies_offers = self.__split_offers_on_proxies__(offers)
        # Создаем корутины на парсинг каждой квартиры
        tasks = []
        for ind, proxy_offers in enumerate(proxies_offers):
            tasks.append(
                self.parse_offer(
                    page_number=page_number,
                    count_of_pages=count_of_pages,
                    ind=ind, proxy_offers=proxy_offers,
                    offers=offers
                    ))

        await asyncio.gather(*tasks)
        await asyncio.sleep(2)

        return True, 0, False

    async def parse_offer(self, page_number, count_of_pages, ind, proxy_offers, offers):
        current_proxy = proxy_offers[0]
        offers_to_parse = proxy_offers[1]
        session = AsyncSession()
        session.headers = {
            'Accept-Language': 'en',
            'User-agent': UserAgent().random
        }

        # Парсинг каждого объявления асинхронно
        for offer in offers_to_parse:
            offer = bs4.BeautifulSoup(offer, 'html.parser')

            # Парсинг объявления в зависимости от типа страницы
            common_data = self.parse_offer_func(offer)

            common_data["location"] = self.location_name
            common_data["deal_type"] = self.deal_type
            common_data["accommodation_type"] = self.accommodation_type

            author_data = define_author(block=offer, is_ordinary_page=self.__is_ordinary_page__)
            location_data = define_location_data(
                block=offer, is_sale=self.is_sale(),
                is_ordinary_page=self.__is_ordinary_page__
            )
            price_data = define_price_data(block=offer, is_ordinary_page=self.__is_ordinary_page__)
            specification_data = define_specification_data(
                block=offer, is_ordinary_page=self.__is_ordinary_page__
            )

            if define_deal_url_id(common_data["url"]) in self.result_set:
                return

            page_data = dict()
            if self.with_extra_data:
                flat_parser = FlatPageParserAsync(session=session, url=common_data["url"], proxy=current_proxy)
                try:
                    page_data = await flat_parser.parse_page()
                except Exception as e:
                    print('Ошибка парсинга страницы объявления:', e)

            self.count_parsed_offers += 1
            self.result_set.add(define_deal_url_id(common_data["url"]))
            # self.result.append(union_dicts(author_data, common_data, specification_data, price_data, page_data, location_data))
            self.result.append(union_dicts(author_data, common_data, price_data, page_data, location_data))

            # Выводим результаты
            self.print_parse_progress(page_number=page_number, count_of_pages=count_of_pages, offers=offers, ind=ind)
            
            if self.with_saving_csv:
                self.save_results()

        await session.close()
