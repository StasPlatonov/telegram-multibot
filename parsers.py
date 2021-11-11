from bs4 import BeautifulSoup
import requests

from telegram import InputMediaPhoto
from telegram import ParseMode

from datetime import datetime
import json
from common import Common

# -------------------------------------------------------------------------------

import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s [%(thread)d] %(name)s[%(levelname)s]: %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

html_doc = """
<html><head><title>The Dormouse's story</title></head>
<body>
<p class="title"><b>The Dormouse's story</b></p>

<p class="story">Once upon a time there were three little sisters; and their names were
<a href="http://example.com/elsie" class="sister" id="link1">Elsie</a>,
<a href="http://example.com/lacie" class="sister" id="link2">Lacie</a> and
<a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
and they lived at the bottom of a well.</p>

<p class="story">...</p>
""" 


class SmartParser(object):
    def __init__(self, delay = 0):
        self.delay = delay
    # ----------------------------------------------------------------------------
    
    def Test(self):
        soup = BeautifulSoup(html_doc, 'html.parser')
        for link in soup.find_all('a'):
            print(link.get('href'))
        print(soup.get_text())
    # ----------------------------------------------------------------------------

    def ParseQuotes(self, response):
        soup = BeautifulSoup(response.text, 'lxml')
        
        quotes = soup.find_all('span', class_='text')
        authors = soup.find_all('small', class_='author')

        result = ""
        
        for i in range(0, len(quotes)):
            #print(quotes[i].text)
            #print('--' + authors[i].text)
            result += authors[i].text + ':\r\n' + quotes[i].text + '\r\n'
            
        return result
    # ----------------------------------------------------------------------------
    
    def ParsePrices(self, url):
        params = {'page': 1}
        
        # greater than first page to start parsing
        pages = 2
        n = 1

        result = 'Товары и цены:\r\n'

        while params['page'] <= pages:
            response = requests.get(url, params=params)
            soup = BeautifulSoup(response.text, 'lxml')
            items = soup.find_all('div', class_='col-lg-4 col-md-6 mb-4')
            
            pageNum = params['page']
            print(f'Processing page {pageNum}');
            
            for n, i in enumerate(items, start=n):
                itemName = i.find('h4', class_='card-title').text.strip()
                itemPrice = i.find('h5').text
                #print(f'{n}:  {itemPrice} за {itemName}')
                result += f'{n}:  {itemPrice} за {itemName}\r\n'

            # [-2] предпоследнее значение, потому что последнее "Next"
            last_page_num = int(soup.find_all('a', class_='page-link')[-2].text)
            
            pages = last_page_num if pages < last_page_num else pages
            params['page'] += 1
            
        return result
    # ----------------------------------------------------------------------------
    
    def ParseMovies(self):
        user_id = 50828424
        url = 'http://www.kinopoisk.ru/user/%d/votes' % (user_id)

        headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'no-cache',
        'Cookie': 'pcssspb=1; pcs3=1; afpix=1; gdpr=0; _ym_uid=1610569480230596189; _ym_d=1610569481; _ym_isad=1',
        'Pragma':'no-cache',
        'Referer': 'https://www.kinopoisk.ru/',
        'sec-fetch-dest': 'script',
        'sec-fetch-mode': 'no-cors',
        'sec-fetch-site': 'cross-site',
        'upgrade-insecure-requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36'
        }
      
        response = requests.get(url, headers = headers)
        soup = BeautifulSoup(response.text, 'lxml')
        #print(soup)

        filmsList = soup.find('div', class_="profileFilmsList")
        #print(filmsList)
        items = filmsList.find_all("div", class_="item")
        #print(items)
        result = 'Фильмы, которые вы оценили:\r\n'
        for item in items:
            nameEng = item.find("div", {"class": "nameEng"})
            
            itemRef = item.find("div", {"class": "nameRus"}).find("a");
            nameRus = itemRef.text
            filmLink = itemRef.get('href') # link to movie
            
            rating = item.find("div", {"class": "rating"}).find("b").text
            
            date = item.find("div", {"class": "date"}).text
            vote = item.find("div", {"class": "vote"}).text
            
            result += f'{nameRus}(*{rating}) : <b>{vote}</b> ({date})\r\n'
            
        return result
    # ----------------------------------------------------------------------------

    def ParseComingSoonMovies(self):
        url = 'https://www.kinopoisk.ru/comingsoon/sex/all/period/halfyear/'

        headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'no-cache',
        'Cookie': 'pcssspb=1; pcs3=1; afpix=1; gdpr=0; _ym_uid=1610569480230596189; _ym_d=1610569481; _ym_isad=1',
        'Pragma':'no-cache',
        'Referer': 'https://www.kinopoisk.ru/',
        'sec-fetch-dest': 'script',
        'sec-fetch-mode': 'no-cors',
        'sec-fetch-site': 'cross-site',
        'upgrade-insecure-requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36'
        }
      
        response = requests.get(url, headers = headers)
        soup = BeautifulSoup(response.text, 'lxml')
        #print(soup)

        filmsList = soup.find('div', class_="coming_films")
        #print(filmsList)
        items = filmsList.find_all("div", class_="item")
        #print(items)
        result = 'Фильмы, которые скоро выйдут:\r\n'
        
        emojiPlay = u'\U000025B6'
        emojiCinema = u'\U0001F3A6'
        emojiCalendar = u'\U0001F4C5'
        emojiLink = u'\U0001F517'
        
        for item in items:
            info = item.find("div", class_="info")
            
            link = info.find("div", class_="name").find("a")
            nameRus = link.text
            linkValue = link.get('href')
            
            rating = info.find("div", class_="bar").find("div", class_="bar_statistics").text
            
            dateNew = item.find("div", class_="dateNew")
            dayElem = dateNew.find("div", class_="day")
            day_classes = dayElem.get('class')
            day = 0
            for day_class in day_classes:
                if day_class.startswith('day_'):
                    day = day_class[4:]
            
            month = dateNew.find("div", class_="month").text
            year = dateNew.find("div", class_="year").text

            result += emojiCinema + f' <b>{nameRus}</b>' + '\r\n'
            result += f'Рейтинг: (*{rating})' + '\r\n'

            result += emojiLink + "<a href='https://fakekinopoisk.ru/" + linkValue + "'>Перейти</a>" + '\r\n'
            result += emojiCalendar + f' Дата выхода: <b>{day}.{month}.{year}</b>' + '\r\n'
            result += "---------------------------------------" + '\r\n'
            result += '\r\n'
            
        return result
    # ----------------------------------------------------------------------------
    
    def ParseComingSoonExMovies(self, bot, chat_id):
        url = 'https://www.kinopoisk.ru/comingsoon/sex/all/period/halfyear/'

        headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'no-cache',
        'Cookie': 'pcssspb=1; pcs3=1; afpix=1; gdpr=0; _ym_uid=1610569480230596189; _ym_d=1610569481; _ym_isad=1',
        'Pragma':'no-cache',
        'Referer': 'https://www.kinopoisk.ru/',
        'sec-fetch-dest': 'script',
        'sec-fetch-mode': 'no-cors',
        'sec-fetch-site': 'cross-site',
        'upgrade-insecure-requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36'
        }
      
        response = requests.get(url, headers = headers)
        soup = BeautifulSoup(response.text, 'lxml')
        #print(soup)

        filmsList = soup.find('div', class_="coming_films")
        #print(filmsList)
        items = filmsList.find_all("div", class_="item")
        #print(items)
        result = 'Фильмы, которые скоро выйдут:\r\n'
        
        emojiPlay = u'\U000025B6'
        emojiCinema = u'\U0001F3A6'
        emojiCalendar = u'\U0001F4C5'
        emojiLink = u'\U0001F517'
        
        media_group = list()

        for item in items:
            info = item.find("div", class_="info")
            
            link = info.find("div", class_="name").find("a")
            nameRus = link.text
            linkValue = link.get('href')
            
            rating = info.find("div", class_="bar").find("div", class_="bar_statistics").text
            
            dateNew = item.find("div", class_="dateNew")
            dayElem = dateNew.find("div", class_="day")
            day_classes = dayElem.get('class')
            day = 0
            for day_class in day_classes:
                if day_class.startswith('day_'):
                    day = day_class[4:]
            
            month = dateNew.find("div", class_="month").text
            year = dateNew.find("div", class_="year").text

            url = emojiCinema + "<a href='https://kinopoisk.ru/" + linkValue + "'><b>" + nameRus + "</b></a>"
            url += '\r\n'
            url += f'Рейтинг: *{rating}' + '\r\n'
            url += emojiCalendar + f' Дата выхода:     <b>{day}.{month}.{year}</b>'
            
            #picURL = 'https://st.kp.yandex.net/images/sm_' + item.find("div", class_="pic").find("a").get('href')[1:-1] + '.jpg'
            
            #print(picURL)

            #caption = emojiCinema + f' <b>{nameRus}</b>' + '\r\n'
            #caption += f'Рейтинг: {rating}' + '\r\n'
            #caption += emojiCalendar + f' Дата выхода: <b>{day}.{month}.{year}</b>'
            
            #media_group.append(InputMediaPhoto(media=picURL, caption=caption, parse_mode=ParseMode.HTML))
            
            '''
            bot.send_photo(
                chat_id, 
                photo=picURL, 
                caption=caption,
                parse_mode=ParseMode.HTML
            )
            '''
            bot.send_message(chat_id=chat_id, text=url, parse_mode=ParseMode.HTML)

        #return media_group
        #return result
    # ----------------------------------------------------------------------------

    def ParseNalogTicket(self, ticket):

        ticket_icon = u'\U0001F3AB'
        calendar_icon = u'\U0001F4C5'
        money_icon = u'\U0001F4B0'
        oper_icon = u'\U0001F468'
        card_icon = u'\U0001F4B3'

        results = []

        result = '          ' + ticket_icon + 'Информация о чеке\r\n'
        result += '<code>'
        result += calendar_icon + f' Дата операции: <b>{ticket["operation"]["date"]}</b>\r\n'
        result += f'Организация: {ticket["organization"]["name"]}\r\n'
        result += f'ИНН:         {ticket["organization"]["inn"]}\r\n'
        result += f'Продавец:    {ticket["seller"]["name"]}\r\n'
        result += f'ИНН:         {ticket["seller"]["inn"]}\r\n'
        result += '</code>'

        op_price_rb = ticket["operation"]["sum"] / 100
        result += money_icon + f' <b>ИТОГ:             {op_price_rb}р.</b>\r\n\r\n'

        receipt = ticket["ticket"]["document"]["receipt"]

        result += '<code>'
        result += '  ------- ' + ticket_icon + f' Чек № <b>{receipt["requestNumber"]}</b> -------\r\n'

        receipt_nds_rb = receipt["nds18"] / 100
        result += f'Сумма НДС:              <b>{receipt_nds_rb}р.</b>\r\n'

        receipt_e_cash_rb = receipt["ecashTotalSum"] / 100
        result += card_icon + f' Безналичными:        <b>{receipt_e_cash_rb}р.</b>\r\n'

        receipt_sum_rb = receipt["totalSum"] / 100
        result += money_icon + f' Получено:            <b>{receipt_sum_rb}р.</b>\r\n'

        result += f'{receipt["user"]}\r\n'

        result += oper_icon + f' Кассир: <b>{receipt["operator"]}</b>\r\n'
        result += f'Смена:        <b>{receipt["shiftNumber"]}</b>\r\n'
        result += f'Чек:          <b>{receipt["requestNumber"]}</b>\r\n'
        result += f'ИНН           <b>{receipt["userInn"]}</b>\r\n'
        result += f'ФН№           <b>{receipt["fiscalDriveNumber"]}</b>\r\n'
        result += f'ФД№           <b>{receipt["fiscalDocumentNumber"]}</b>\r\n'
        result += f'ФП            <b>{receipt["fiscalSign"]}</b>\r\n'
        result += '</code>'

        items = receipt["items"]
        for item in items:
            result += '<code>'
            result += '    ---------------------------------\r\n'
            item_price_rb = item["price"] / 100
            item_sum_rb = item["sum"] / 100

            result += '</code><b>'
            result += f'{item["name"]}\r\n'
            result += '</b><code>'

            result += f'Стоимость:          {item_price_rb}р.\r\n'
            result += f'Кол-во:             {item["quantity"]}\r\n'
            result += f'Сумма:              </code><b>{item_sum_rb}р.</b>\r\n'

            if len(result) > 2000:
                result += 'Ожидайте продолжения...'
                results.append(result)
                result = ''

        results.append(result)

        return results
    # ----------------------------------------------------------------------------

    def ParseTVProgram(self, bot, chat_id):

        # quoted = re.compile('"[^"]*"')

        favorites = ["СТС", "РЕН ТВ", "Че", "ТВ-3", "ТНТ", "МИР", "Пятница!", "2x2"]
        favorites_genres = ["боевик", "комедия", "триллер", "ужасы", "фантастика", "приключения"]
        favorite_min_rating = 5.0

        countries_icons = {'Россия': u'\U0001F1F7' + u'\U0001F1FA',
                           'США': u'\U0001F1FA' + u'\U0001F1F8',
                           'Италия': u'\U0001F1EE' + u'\U0001F1F9',
                           'Испания': u'\U0001F1EA' + u'\U0001F1F8',
                           'Франция': u'\U0001F1EB' + u'\U0001F1F7',
                           'Германия': u'\U0001F1E9' + u'\U0001F1EA',
                           'Япония': u'\U0001F1EF' + u'\U0001F1EA',
                           'Китай': u'\U0001F1E8' + u'\U0001F1F3',
                           'Великобритания': u'\U0001F1EC' + u'\U0001F1E7'
                           }

        genres_icons = {'комедия': u'\U0001F602',
                        'ужасы': u'\U0001F480',
                        'драма': u'\U0001F622',
                        'фантастика': u'\U0001F47D',
                        'фэнтези': u'\U0001F393',
                        'приключения': u'\U0001F30D',
                        'боевик': u'\U0001F52B',
                        'триллер': u'\U0001F630',
                        'роман': u'\U0001F495',
                        'мюзикл': u'\U0001F3B5'
                        }

        current_time = datetime.now()
        current_hour = current_time.time().hour
        current_min = current_time.time().min
        logger.debug(f'Retrieving TV program at {current_hour}:{current_min}')

        url = 'https://tv.mail.ru/moskva/'

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36'
        }

        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'lxml')

        channels = soup.find('div', class_="p-channels__items")
        channel_items = channels.find_all("div", class_="p-channels__item")
        logger.info(f'Found {len(channel_items)} channels on the page')

        result = "Избранное на ТВ:\n"

        for ch_item in channel_items:
            try:
                ch_id = ch_item.get('data-id')
                ch_name = ch_item.find("a", class_="p-channels__item__info__title__link").contents[0]

                if ch_name not in favorites:
                    logger.debug(f'Skip non favorite channel {ch_name}')
                    continue

                logger.info(f'Канал: {ch_name}')

                ch_image = ch_item.find("img", class_="p-picture__image")
                ch_image_src = ch_image.get("src")

                channel_result = ""

                ch_program_items = ch_item.find_all("div", class_="p-programms__item")
                for prg_item in ch_program_items:
                    prg_start = prg_item.find('span', class_='p-programms__item__time-value').text

                    prg_item_name = prg_item.find('span', class_='p-programms__item__name')

                    # Skip items that has no sub item with title 'Фильм'
                    prg_icon = prg_item_name.find("i", class_="p-programms__item__icon")
                    if prg_icon is None:
                        continue
                    if prg_icon.get("title") != "Фильм":
                        continue

                    prg_name = prg_item_name.find('span', class_='p-programms__item__name-link').text

                    data_id = prg_item.get('data-id')
                    program_url = 'https://tv.mail.ru/ajax/event/?id=' + data_id + '&region_id=70'

                    program_response = requests.get(program_url, headers=headers)
                    prg_json = json.loads(program_response.text)

                    # Get rating and check
                    imdb = prg_json["tv_event"]["afisha_event"]["imdb_rating"]
                    if float(imdb) < favorite_min_rating:
                        continue

                    # Get genres text and check genre is matched
                    genres = prg_json["tv_event"]["genre"]

                    genre_is_matched = False
                    genres_text = ""
                    for genre in genres:
                        genre_name = genre["title"]

                        genres_img = "" if genres_icons.get(genre_name) is None else genres_icons.get(genre_name)
                        genres_text += f'{genres_img}{genre_name} '

                        if genre_name in favorites_genres:
                            genre_is_matched = True

                    if not genre_is_matched:
                        continue

                    genres_text = genres_text.strip(" ")

                    logger.info(f'{prg_start} : {prg_name} (*{imdb}) ({genres_text})')

                    channel_result += f'  <b>{prg_start}</b> {Common.cinema_icon} <b>{prg_name}</b>'
                    channel_result += '\n'

                    channel_result += f'        Рейтинг: {Common.star_icon}{imdb}'
                    channel_result += '\n'

                    country = prg_json["tv_event"]["country"][0]["title"]
                    country_img = "" if countries_icons.get(country) is None else countries_icons.get(country)
                    channel_result += f'        Страна: {country_img}{country}'
                    channel_result += '\n'

                    year = prg_json["tv_event"]["year"]["title"]
                    channel_result += f'        Год: {year}'
                    channel_result += '\n'

                    channel_result += f'        Жанр: {genres_text}'
                    channel_result += '\n'

                    link_value = prg_json["tv_event"]["url"]
                    channel_result += "<a href='https://tv.mail.ru" + link_value + "'><b>" + "        Подробнее" + "</b></a>"
                    channel_result += '\n'

                    # descr = prg_json["tv_event"].get("descr")
                    # descr.replace("<p>", "")
                    # descr.replace("</p>", "")
                    # channel_result += descr
                    # channel_result += '\n'

                if len(channel_result) != 0:
                    result += f'{Common.tv_icon}       <b>{ch_name}</b>'
                    result += '\n'
                    result += channel_result
                    result += '\n'

            except Exception as e:
                logger.error('Failed to process item: ' + str(e))
        print(result)
        bot.send_message(chat_id=chat_id, text=result, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    # ----------------------------------------------------------------------------

    def GetTVChannels(self, bot, chat_id):
        current_time = datetime.now()
        current_hour = current_time.time().hour
        current_min = current_time.time().min
        logger.debug(f'Retrieving TV channels at {current_hour}:{current_min}')

        prev_channels_count = 0

        url = 'https://tv.mail.ru/ajax/index'

        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36',
            'Referer': 'https://tv.mail.ru/moskva/',
            'Content-Type': 'multipart/form-data; boundary=----WebKitFormBoundaryYzc1l9tbSVCtetkh'
        }

        data = {'region_id': 70, 'channel_type': 'all', 'period': 'now', 'date': '2021-10-24', 'appearance': 'grid'}

        response = requests.post(url, headers=headers, data=data)
        json_response = json.loads(response.text)

        channels = json_response["schedule"]

        page_size = len(channels)
        logger.info(f'Received {page_size} channels')

        channel_ids_arr = []
        channel_ids_arr2 = ""
        for channel in channels:
            ch_id = channel["channel"]["id"]
            channel_ids_arr.append(int(ch_id))
            channel_ids_arr2 += ch_id + ','
        logger.info('Received channels: ' + str(channel_ids_arr))
        channel_ids_arr2 = channel_ids_arr2[:-1]

        while prev_channels_count != len(channels):
            prev_channels_count = len(channels)

            #files = {
            #    'ex': (None, json.dumps(data), 'application/json'),
            #}
            # data['ex'] = channel_ids_arr2 # channel_ids_arr

            rq = requests.Request('POST',
                                  url,
                                  files={
                                      'ex': (None, channel_ids_arr2),
                                      'region_id': (None, 70)
                                  }).prepare()
            rq_str = rq.body.decode('utf8')
            print(rq_str)

            session = requests.Session()
            response = session.send(rq)
            '''
            response = requests.post(url,
                                     headers=headers,
                                     data={
                                         'ex': (None, channel_ids_arr2),
                                         'region_id': (None, 70)
                                     })
            '''
            json_response = json.loads(response.text)

            channels = json_response["schedule"]

            page_size = len(channels)
            logger.info(f'Received {page_size} channels')

            channel_ids_arr = []
            for channel in channels:
                ch_id = channel["channel"]["id"]
                channel_ids_arr.append(int(ch_id))
            logger.info('Received channels: ' + str(channel_ids_arr))

        logger.info(f'All {len(channels)} channels received')
        # soup = BeautifulSoup(response.text, 'lxml')

        #ex: '1112,1148,2068,1091,1671,1049,796,1334,1362,800,1063,1266,1396,1122,888,1229,1249,1968,2007,850,1271,2060,1395,948'


        # channels = soup.find('div', class_="p-channels__items")
        # channel_items = channels.find_all("div", class_="p-channels__item")
        # logger.info(f'Found {len(channel_items)} channels on the page')
