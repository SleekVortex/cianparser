import re
import bs4
import time

from random import randrange
from fake_useragent import UserAgent


class FlatPageParser:
    def __init__(self, session, url):
        self.__session__ = session
        self.url = url
        self.__ua__ = UserAgent()

    def __load_page__(self):
        time.sleep(randrange(5, 8))
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
