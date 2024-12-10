import re
import itertools
from cianparser.constants import STREET_TYPES, NOT_STREET_ADDRESS_ELEMENTS, FLOATS_NUMBERS_REG_EXPRESSION


def union_dicts(*dicts):
    return dict(itertools.chain.from_iterable(dct.items() for dct in dicts))


def define_rooms_count(description):
    if "1-комн" in description or "Студия" in description:
        rooms_count = 1
    elif "2-комн" in description:
        rooms_count = 2
    elif "3-комн" in description:
        rooms_count = 3
    elif "4-комн" in description:
        rooms_count = 4
    elif "5-комн" in description:
        rooms_count = 5
    elif "доля" in description.lower():
        rooms_count = "Доля"
    else:
        rooms_count = None

    return rooms_count


def define_deal_url_id(url: str):
    url_path_elements = url.split("/")
    if len(url_path_elements[-1]) > 3:
        return url_path_elements[-1]
    if len(url_path_elements[-2]) > 3:
        return url_path_elements[-2]

    return None


def define_author(block, is_ordinary_page):
    if is_ordinary_page:
        spans = block.select("div[data-name='LinkArea'] span")
    else:
        spans = block.select_one("section[data-name='CardContainer']").select("div span")

    author_data = {
        "author": "",
        "author_type": "",
    }

    for index, span in enumerate(spans):
        if "Собственник" in span:
            author_data["author"] = spans[index + 1].text
            author_data["author_type"] = "homeowner"
            return author_data

        elif "Риелтор" in span:
            author_data["author"] = spans[index + 1].text
            author_data["author_type"] = "realtor"
            return author_data

        elif "Ук・оф.Представитель" in span:
            author_data["author"] = spans[index + 1].text
            author_data["author_type"] = "official_representative"
            return author_data

        elif "Представитель застройщика" in span:
            author_data["author"] = spans[index + 1].text
            author_data["author_type"] = "representative_developer"
            return author_data

        elif "Застройщик" in span:
            author_data["author"] = spans[index + 1].text
            author_data["author_type"] = "developer"
            return author_data

        elif "ID" in span.text:
            author_data["author"] = span.text
            author_data["author_type"] = "unknown"
            return author_data

    return author_data


def parse_location_data(block, is_ordinary_page):

    if is_ordinary_page:
        general_info_sections = block.select(
            "div[data-name='LinkArea'] div[data-name='GeneralInfoSectionRowComponent']"
        )
    else:
        general_info_sections = block.select(
            "div[data-name='OfferGeneralInfoLayout'] div"
        )

    location_data = dict()
    location_data["district"] = ""
    location_data["underground"] = ""
    location_data["street"] = ""
    location_data["house_number"] = ""

    for section in general_info_sections:
        geo_labels = section.select("a[data-name='GeoLabel']")

        # if len(geo_labels) > 1:
            # print("\n\n", location_data["street"] == "",geo_labels[-2].text, "|||", geo_labels[-1].text)

        for index, label in enumerate(geo_labels):
            if "м. " in label.text:
                location_data["underground"] = label.text

            if "р-н" in label.text or "поселение" in label.text:
                location_data["district"] = label.text

            if any(street_type in label.text.lower() for street_type in STREET_TYPES):
                location_data["street"] = label.text

                if len(geo_labels) > index + 1 and any(chr.isdigit() for chr in geo_labels[index + 1].text):
                    location_data["house_number"] = geo_labels[index + 1].text

    return location_data


def define_location_data(block, is_sale, is_ordinary_page):

    if is_ordinary_page:
        elements = block.select(
            "div[data-name='LinkArea'] div[data-name='GeneralInfoSectionRowComponent']"
        )
    else:
        elements = block.select(
            "div[data-name='OfferGeneralInfoLayout'] div"
        )

    location_data = dict()
    location_data["district"] = ""
    location_data["street"] = ""
    location_data["house_number"] = ""
    location_data["underground"] = ""

    if is_sale:
        location_data["residential_complex"] = ""

    for index, element in enumerate(elements):
        if ("ЖК" in element.text) and ("«" in element.text) and ("»" in element.text):
            location_data["residential_complex"] = element.text.split("«")[1].split("»")[0]

        elif "р-н" in element.text and len(element.text) < 250:
            address_elements = element.text.split(",")
            if len(address_elements) < 2:
                continue

            if "ЖК" in address_elements[0] and "«" in address_elements[0] and "»" in address_elements[0]:
                location_data["residential_complex"] = address_elements[0].split("«")[1].split("»")[0]

            if ", м. " in element.text:
                location_data["underground"] = element.text.split(", м. ")[1]
                if "," in location_data["underground"]:
                    location_data["underground"] = location_data["underground"].split(",")[0]

            if (any(chr.isdigit() for chr in address_elements[-1]) and "жк" not in address_elements[-1].lower() and
                not any(street_type in address_elements[-1].lower() for street_type in STREET_TYPES)) and len(
                address_elements[-1]) < 10:
                location_data["house_number"] = address_elements[-1].strip()

            for ind, elem in enumerate(address_elements):
                if "р-н" in elem:
                    district = elem.replace("р-н", "").strip()

                    location_data["district"] = district

                    if "ЖК" in address_elements[-1]:
                        location_data["residential_complex"] = address_elements[-1].strip()

                    if "ЖК" in address_elements[-2]:
                        location_data["residential_complex"] = address_elements[-2].strip()

                    for street_type in STREET_TYPES:
                        if street_type in address_elements[-1]:
                            location_data["street"] = address_elements[-1].strip()
                            if street_type == "улица":
                                location_data["street"] = location_data["street"].replace("улица", "")
                            return location_data

                        if street_type in address_elements[-2]:
                            location_data["street"] = address_elements[-2].strip()
                            if street_type == "улица":
                                location_data["street"] = location_data["street"].replace("улица", "")

                            return location_data

                    for k, after_district_address_element in enumerate(address_elements[ind + 1:]):
                        if len(list(set(after_district_address_element.split(" ")).intersection(
                                NOT_STREET_ADDRESS_ELEMENTS))) != 0:
                            continue

                        if len(after_district_address_element.strip().replace(" ", "")) < 4:
                            continue

                        location_data["street"] = after_district_address_element.strip()

                        return location_data

            return location_data

    if location_data["district"] == "":
        for index, element in enumerate(elements):
            if ", м. " in element.text and len(element.text) < 250:
                location_data["underground"] = element.text.split(", м. ")[1]
                if "," in location_data["underground"]:
                    location_data["underground"] = location_data["underground"].split(",")[0]

                address_elements = element.text.split(",")

                if len(address_elements) < 2:
                    continue

                if "ЖК" in address_elements[-1]:
                    location_data["residential_complex"] = address_elements[-1].strip()

                if "ЖК" in address_elements[-2]:
                    location_data["residential_complex"] = address_elements[-2].strip()

                if (any(chr.isdigit() for chr in address_elements[-1]) and "жк" not in address_elements[
                    -1].lower() and
                    not any(
                        street_type in address_elements[-1].lower() for street_type in STREET_TYPES)) and len(
                    address_elements[-1]) < 10:
                    location_data["house_number"] = address_elements[-1].strip()

                for street_type in STREET_TYPES:
                    if street_type in address_elements[-1]:
                        location_data["street"] = address_elements[-1].strip()
                        if street_type == "улица":
                            location_data["street"] = location_data["street"].replace("улица", "")
                        return location_data

                    if street_type in address_elements[-2]:
                        location_data["street"] = address_elements[-2].strip()
                        if street_type == "улица":
                            location_data["street"] = location_data["street"].replace("улица", "")
                        return location_data

            for street_type in STREET_TYPES:
                if (", " + street_type + " " in element.text) or (" " + street_type + ", " in element.text):
                    address_elements = element.text.split(",")

                    if len(address_elements) < 3:
                        continue

                    if (any(chr.isdigit() for chr in address_elements[-1]) and "жк" not in address_elements[
                        -1].lower() and
                        not any(
                            street_type in address_elements[-1].lower() for street_type in STREET_TYPES)) and len(
                        address_elements[-1]) < 10:
                        location_data["house_number"] = address_elements[-1].strip()

                    if street_type in address_elements[-1]:
                        location_data["street"] = address_elements[-1].strip()
                        if street_type == "улица":
                            location_data["street"] = location_data["street"].replace("улица", "")

                        location_data["district"] = address_elements[-2].strip()

                        return location_data

                    if street_type in address_elements[-2]:
                        location_data["street"] = address_elements[-2].strip()
                        if street_type == "улица":
                            location_data["street"] = location_data["street"].replace("улица", "")

                        location_data["district"] = address_elements[-3].strip()

                        return location_data

    return location_data


def define_price_data(block, is_ordinary_page):
    if is_ordinary_page:
        elements = block.select("div[data-name='LinkArea'] span[data-mark='MainPrice']")
    else:
        elements = block.select("span[data-testid='Price']")

    price_data = {
        "price_per_month": None,
        "commissions": 0,
    }

    for element in elements:
        if "₽/мес" in element.text:
            price_description = element.text
            price_data["price_per_month"] = int(
                "".join(price_description[:price_description.find("₽/мес") - 1].split()))

            if "%" in price_description:
                price_data["commissions"] = int(
                    price_description[price_description.find("%") - 2:price_description.find("%")].replace(" ", ""))

            return price_data

        elif "₽" in element.text and "млн" not in element.text:
            price_description = element.text
            price_data["price"] = int("".join(price_description[:price_description.find("₽") - 1].split()))

            return price_data

    return price_data


def define_specification_data(block, is_ordinary_page):
    specification_data = dict()
    specification_data["floor"] = None
    specification_data["floors_count"] = None
    specification_data["rooms_count"] = None
    specification_data["total_meters"] = None

    if is_ordinary_page:
        title = block.select_one("div[data-name='LinkArea'] div[data-name='GeneralInfoSectionRowComponent']").text
    else:
        title = block.select_one("div[data-name='OfferGeneralInfoLayout'] a[data-name='Features']").text

    if title.find("м²") is not None:
        total_meters = title[: title.find("м²")].replace(",", ".")
        if len(re.findall(FLOATS_NUMBERS_REG_EXPRESSION, total_meters)) != 0:
            specification_data["total_meters"] = float(
                re.findall(FLOATS_NUMBERS_REG_EXPRESSION, total_meters)[-1].replace(" ", "").replace("-", ""))

    if "этаж" in title:
        floor_per = title[title.rfind("этаж") - 7: title.rfind("этаж")]
        floor_properties = floor_per.split("/")

        if len(floor_properties) == 2:
            ints = re.findall(r'\d+', floor_properties[0])
            if len(ints) != 0:
                specification_data["floor"] = int(ints[-1])

            ints = re.findall(r'\d+', floor_properties[1])
            if len(ints) != 0:
                specification_data["floors_count"] = int(ints[-1])

    specification_data["rooms_count"] = define_rooms_count(title)

    return specification_data
