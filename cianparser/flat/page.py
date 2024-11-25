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
        time.sleep(randrange(5, 8))
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
            "kitchen_meters": None,
            "floor": None,
            "floors_count": None,
            "phone": "",
            "images": [],
            "description": "",
        }

        spans = self.offer_page_soup.select("span")
        for index, span in enumerate(spans):
            if "Тип жилья" == span.text:
                page_data["object_type"] = spans[index + 1].text

            if "Тип дома" == span.text:
                page_data["house_material_type"] = spans[index + 1].text

            if "Отопление" == span.text:
                page_data["heating_type"] = spans[index + 1].text

            if "Отделка" == span.text:
                page_data["finish_type"] = spans[index + 1].text

            if "Площадь кухни" == span.text:
                page_data["kitchen_meters"] = spans[index + 1].text

            if "Жилая площадь" == span.text:
                page_data["living_meters"] = spans[index + 1].text

            if "Год постройки" in span.text:
                page_data["year_of_construction"] = spans[index + 1].text

            if "Год сдачи" in span.text:
                page_data["year_of_construction"] = spans[index + 1].text

            if "Этаж" == span.text:
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
