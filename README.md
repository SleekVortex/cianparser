### Сбор данных с сайта объявлений об аренде и продаже недвижимости Циан

Cianparser - это библиотека Python 3 для парсинга сайта  [Циан](http://cian.ru).
С его помощью можно получить достаточно подробные и структурированные данные по краткосрочной и долгосрочной аренде, продаже квартир, домов, танхаусов итд.

### Установка
```bash
pip install cianparser
```

### Использование
```python
>>> import cianparser
    
>>> data = cianparser.parse(offer="rent_long", accommodation="flat", location="Казань", rooms="all", start_page=1, end_page=2, save_csv=False)

>>> print(data[0])
```

```
                  Collecting information from pages..
Setting [=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>] 100%
1 page: [=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>] 100%
2 page: [=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>=>] 100%

{'accommodation': 'flat',
 'all_floors': 29,
 'author': 'ID 579515',
 'comm_meters': 51,
 'commissions': 0,
 'district': 'Vahitovskij',
 'floor': 11,
 'how_many_rooms': 2,
 'kitchen_meters': 18,
 'link': 'https://kazan.cian.ru/rent/flat/260751194/',
 'price_per_month': 25000,
 'square_meters': 51,
 'street': ' Scherbakovskij pereulok',
 'year_of_construction': 2014}
```

### Конфигурация
Функция *parse* имеет следующий аргументы:
* offer - тип объявления, к примеру, долгосрочная, краткосрочная аренда, продажа ("rent_long", "rent_short", "sale")
* accommodation - вид жилья, к примеру, квартира, комната, дом, часть дома, таунхаус ("flat", "room", "house", "house-part", "townhouse")
* location - локация объявления, к примеру, Казань (для просмотра доступных мест используйте cianparser.list_cities())
* rooms - количество комнат, к примеру, 1, (1,3, "studio"), "studio, "all"; по умолчанию любое ("all")
* start_page - страница, с которого начинается сбор данных, по умолчанию, 1
* end_page - страница, с которого заканчивается сбор данных, по умолчанию, 10
* save_csv - необходимо ли сохранять данные (в реальном времени в процессе сбора данных) или нет, по умолчанию False

#### В настоящее время функция *parse* принимает *offer* и *accommodation* только с значениями "rent_long" и "flat", соответственно

### Признаки, получаемые в ходе сбора данных с предложений по долгосрочной аренде.
* Link - ссылка на это объявление
* District - район, в которой расположена квартира
* Price per month - стоимость аренды в месяц
* Commissions - коммиссиия, взымаемая в ходе первичной аренды
* Kitchen meters - количество квадратных метров кухни
* How many rooms - количество комнат, от 1 до 5и (студия приравнивается к 1-ой квартире)
* Floor - этаж, на котором расположена квартира
* Square meters - общее количество квадратных метров
* Street - улица, в которой расположена квартира
* Author - автор объявления
* All floors - общее количество этажей в здании, на котором расположена квартира
* Year of construction - год постройки здания, на котором расположена квартира

В процессе парсинга любая кириллица переводится в латиницу при помощи использования библиотеки __transliterate__.

В некоторых объявлениях отсутсвуют данные по некоторым признакам (год постройки, жилые кв метры, кв метры кухни).
В этом случае проставляется значение -1.

### Сохранение данных
Имеется возможность сохранения собирающихся данных в режиме реального времени. Для этого необходимо подставить в аргументе 
__save_csv__ значение __True__.

Пример получаемого файла:

```bash
parsing_result_1_3_4618_2023-02-02 06:34:40.217322.csv
```

### Примечание
Данный парсер не будет работать в таком инструменте как [Google Colaboratory](https://colab.research.google.com/). 
См. [подробности](https://github.com/lenarsaitov/cianparser/issues/1)

### Пример исследования получаемых данных
В данном проекте можно увидеть некоторые результаты анализа полученных данных на примере сведений об объявленияъ по аренде недвижимости в городе Казань:

https://github.com/lenarsaitov/cian-data-analysis
