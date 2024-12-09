import re
import bs4
import time
import asyncio

from random import randrange
from fake_useragent import UserAgent


class FlatPageParser:
    def __init__(self, session, url):
        self.__session__ = session
        self.url = url
        self.__ua__ = UserAgent()

    def __load_page__(self):
        time.sleep(randrange(5, 15))
        res = self.__session__.get(self.url)
        if res.status_code == 429:
            time.sleep(randrange(30, 45))
        res.raise_for_status()
        self.offer_page_html = res.text
        self.offer_page_soup = bs4.BeautifulSoup(self.offer_page_html, 'html.parser')

    def __parse_flat_offer_page_json__(self):
        page_data = {
            "year_of_construction": None,
            "object_type": None,
            "house_material_type": None,
            "heating_type": None,
            "finish_type": None,
            "living_meters": None,
            "floor_type": None,
            "parking": None,
            "elevators": None,
            "emergency": None,
            "total_meters": None,
            "bathroom": None,
            "building_status": None,
            "kitchen_meters": None,
            "floor": None,
            "floors_count": None,
            "phone": "",
            "images": [],
            "description": "",
        }

        ps = self.offer_page_soup.select("div[data-name='OfferSummaryInfoLayout'] p")

        for index, p in enumerate(ps):
            if "Тип жилья" == p.text:
                page_data["object_type"] = ps[index + 1].text

            elif "Тип дома" == p.text:
                page_data["house_material_type"] = ps[index + 1].text

            elif "Тип перекрытий" == p.text:
                page_data["floor_type"] = ps[index + 1].text
            
            elif "Парковка" == p.text:
                page_data["parking"] = ps[index + 1].text

            elif "Количество лифтов" == p.text:
                page_data["elevators"] = ps[index + 1].text

            elif "Аварийность" == p.text:
                page_data["emergency"] = ps[index + 1].text != 'Нет'

            elif "Отопление" == p.text:
                page_data["heating_type"] = ps[index + 1].text

            elif "Отделка" == p.text:
                page_data["finish_type"] = ps[index + 1].text
            
            elif "Общая площадь" == p.text:
                page_data["total_meters"] = ps[index + 1].text
            
            elif "Санузел" == p.text:
                page_data["bathroom"] = ps[index + 1].text

            elif "Площадь кухни" == p.text:
                page_data["kitchen_meters"] = ps[index + 1].text

            elif "Жилая площадь" == p.text:
                page_data["living_meters"] = ps[index + 1].text

            elif "Год постройки" in p.text:
                page_data["year_of_construction"] = ps[index + 1].text

        spans = self.offer_page_soup.select("div[data-name='ObjectFactoids'] span")
 
        for index, span in enumerate(spans):

            if "Год сдачи" in span.text:
                page_data["year_of_construction"] = spans[index + 1].text

            elif "Дом" in span.text:
                page_data["building_status"] = spans[index + 1].text

            elif "Этаж" == span.text:
                ints = re.findall(r'\d+', spans[index + 1].text)
                if len(ints) == 2:
                    page_data["floor"] = int(ints[0])
                    page_data["floors_count"] = int(ints[1])


        if "+7" in self.offer_page_html:
            page_data["phone"] = self.offer_page_html[self.offer_page_html.find("+7"): self.offer_page_html.find("+7") + 16].split('"')[0]. \
                replace(" ", ""). \
                replace("-", "")
            
        for img_tag in self.offer_page_soup.select('img.a10a3f92e9--container--KIwW4'):
            img = img_tag['src']
            if '.jpg' in img:
                page_data['images'].append(img)

        desc = self.offer_page_soup.select_one('div.a10a3f92e9--layout--BaqYw span').text
        if desc:
            page_data['description'] = desc

        return page_data

    def parse_page(self):
        self.__load_page__()
        return self.__parse_flat_offer_page_json__()


class FlatPageParserAsync:
    def __init__(self, session, url, proxy):
        self.__session__ = session
        self.__proxy__ = proxy
        self.url = url
        self.__ua__ = UserAgent()

    async def __load_page__(self):
        await asyncio.sleep(randrange(7, 27))
        res = await self.__session__.get(self.url, proxy=self.__proxy__)
        if res.status_code == 429:
            await asyncio.sleep(randrange(30, 60))
        res.raise_for_status()
        self.offer_page_html = res.text
        self.offer_page_soup = bs4.BeautifulSoup(self.offer_page_html, 'html.parser')

    def parse_page_ordinary(self, page_data):
        """
            Функция парсит страницу объявлления, если она обычная.
        """
        # Окно данных о предложении
        ps = self.offer_page_soup.select("div[data-name='OfferSummaryInfoLayout'] p")
        for index, p in enumerate(ps):
                if "Тип жилья" == p.text:
                    page_data["object_type"] = ps[index + 1].text

                elif "Тип дома" == p.text:
                    page_data["house_material_type"] = ps[index + 1].text

                elif "Тип перекрытий" == p.text:
                    page_data["floor_type"] = ps[index + 1].text
                
                elif "Парковка" == p.text:
                    page_data["parking"] = ps[index + 1].text

                elif "Количество лифтов" == p.text:
                    page_data["elevators"] = ps[index + 1].text

                elif "Аварийность" == p.text:
                    page_data["emergency"] = ps[index + 1].text != 'Нет'

                elif "Отопление" == p.text:
                    page_data["heating_type"] = ps[index + 1].text

                elif "Отделка" == p.text:
                    page_data["finish_type"] = ps[index + 1].text
                
                elif "Общая площадь" == p.text:
                    page_data["total_meters"] = ps[index + 1].text
                
                elif "Санузел" == p.text:
                    page_data["bathroom"] = ps[index + 1].text

                elif "Площадь кухни" == p.text:
                    page_data["kitchen_meters"] = ps[index + 1].text

                elif "Жилая площадь" == p.text:
                    page_data["living_meters"] = ps[index + 1].text

                elif "Год постройки" in p.text:
                    page_data["year_of_construction"] = ps[index + 1].text
        
        # Окно со значками
        spans = self.offer_page_soup.select("div[data-name='ObjectFactoids'] span")
        for index, span in enumerate(spans):

            if "Год сдачи" in span.text:
                page_data["year_of_construction"] = spans[index + 1].text

            elif "Дом" in span.text:
                page_data["building_status"] = spans[index + 1].text

            elif "Этаж" == span.text:
                ints = re.findall(r'\d+', spans[index + 1].text)
                if len(ints) == 2:
                    page_data["floor"] = int(ints[0])
                    page_data["floors_count"] = int(ints[1])

        # Изображения
        for img_tag in self.offer_page_soup.select('img.a10a3f92e9--container--KIwW4'):
                img = img_tag['src']
                if '.jpg' in img:
                    page_data['images'].append(img)

        # Описание 
        desc = self.offer_page_soup.select_one("div[data-name='Description']")
        if desc:
            page_data['description'] = desc.get_text(' ', strip=True)
    

    def parse_page_unusual(self, page_data):
        """
            Функция парсит страницу объявлления, если она необычная.
        """
        # Окно данных о предложении
        divs = self.offer_page_soup.select("table div")

        for index, div in enumerate(divs):
            if "Тип жилья" == div.text:
                page_data["object_type"] = divs[index + 1].text

            elif "Тип дома" == div.text:
                page_data["house_material_type"] = divs[index + 1].text

            elif "Тип перекрытий" == div.text:
                page_data["floor_type"] = divs[index + 1].text
            
            elif "Парковка" == div.text:
                page_data["parking"] = divs[index + 1].text

            elif "Количество лифтов" == div.text:
                page_data["elevators"] = divs[index + 1].text

            elif "Аварийность" == div.text:
                page_data["emergency"] = divs[index + 1].text != 'Нет'

            elif "Отопление" == div.text:
                page_data["heating_type"] = divs[index + 1].text

            elif "Отделка" == div.text:
                page_data["finish_type"] = divs[index + 1].text
            
            elif "Общая площадь" == div.text:
                page_data["total_meters"] = divs[index + 1].text
            
            elif "Санузел" == div.text:
                page_data["bathroom"] = divs[index + 1].text

            elif "Площадь кухни" == div.text:
                page_data["kitchen_meters"] = divs[index + 1].text

            elif "Жилая площадь" == div.text:
                page_data["living_meters"] = divs[index + 1].text

            elif "Год постройки" in div.text:
                page_data["year_of_construction"] = divs[index + 1].text

        # Окно со значками
        spans = self.offer_page_soup.select("section[data-name='MainFeatures'] span")

        for index, span in enumerate(spans):

            if "Год сдачи" in span.text:
                page_data["year_of_construction"] = spans[index + 1].text

            elif "Дом" in span.text or "Сдача" in span.text:
                page_data["building_status"] = spans[index + 1].text

            elif re.search(r'\b\d+\s+из\s+\d+\b', span.text):
                ints = re.findall(r'\d+', spans[index].text)
                if len(ints) == 2:
                    page_data["floor"] = int(ints[0])
                    page_data["floors_count"] = int(ints[1])

        # Изображения
        for img_tag in self.offer_page_soup.select("section[data-name='GalleryFragment'] img"):
            # Получение значения атрибута src или data-src
            img = img_tag.get('src')
            if img is None:
                img = img_tag.get('data-src')
            if img and '.jpg' in img:
                page_data['images'].append(img)

        # Описание предложения
        desc = self.offer_page_soup.select_one("section[data-name='Description']")
        if desc:
            page_data['description'] = desc.get_text(' ', strip=True)

    def __parse_flat_offer_page_json__(self):
        page_data = {
            "year_of_construction": None,
            "object_type": None,
            "house_material_type": None,
            "heating_type": None,
            "finish_type": None,
            "living_meters": None,
            "floor_type": None,
            "parking": None,
            "elevators": None,
            "emergency": None,
            "total_meters": None,
            "bathroom": None,
            "building_status": None,
            "kitchen_meters": None,
            "floor": None,
            "floors_count": None,
            "phone": "",
            "images": [],
            "description": "",
        }
        ps = self.offer_page_soup.select_one("div[data-name='OfferSummaryInfoLayout'] p")
        # обработка случая, если html страницы не содержит информации
        # Оказывается иногда страницы имеют другую структуру html
        if ps:
            self.parse_page_ordinary(page_data)
        else:
            self.parse_page_unusual(page_data)

        return page_data

    async def parse_page(self):

        await self.__load_page__()
        page_parsed = self.__parse_flat_offer_page_json__()

        return page_parsed
