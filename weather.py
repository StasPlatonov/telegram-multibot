import os
import requests
import datetime

import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s [%(thread)d] %(name)s[%(levelname)s]: %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


class Weather(object):
    def __init__(self):
        self.token = os.environ["OPENWEATHER_TOKEN"]
    # -----------------------------------------------------------------

    @staticmethod
    def get_weather_condition_desc(condition, include_text=True):
        conditions = {
            "Clear": {"icon": "\U00002600", "text": "Ясно"},
            "Clouds": {"icon": "\U00002601", "text": "Облачно"},
            "Rain": {"icon": "\U00002614", "text": "Дождь"},
            "Drizzle": {"icon": "\U00002614", "text": "Дождь"},
            "Thunderstorm": {"icon": "\U000026A1", "text": "Гроза"},
            "Snow": {"icon": "\U0001F328", "text": "Снег"},
            "Mist": {"icon": "\U0001F32B", "text": "Туман"}
        }

        if condition in conditions:
            desc = conditions[condition]
            return desc["icon"] + " " + desc["text"] if include_text else desc["icon"]

        return condition
    # -----------------------------------------------------------------

    @staticmethod
    def get_wind_direction(degrees):
        if degrees <= 22.5 or degrees > 360 - 22.5:
            return "в"
        if degrees <= 22.5 + 45:
            return "cв"
        if degrees <= 90 + 22.5:
            return "c"
        if degrees <= 22.5 + 90 + 45:
            return "сз"
        if degrees <= 180 + 22.5:
            return "з"
        if degrees <= 180 + 22.5 + 45:
            return "юз"
        if degrees <= 270 + 22.5:
            return "ю"
        if degrees <= 270 + 22.5 + 45:
            return "юв"
        return degrees
    # -----------------------------------------------------------------

    def get_current_weather(self, latitude=None, longitude=None, city=None):
        try:
            rq_str = f"http://api.openweathermap.org/data/2.5/weather"
            params = {'APPID': self.token, 'units': 'metric', 'lang': 'ru'}
            #params['cnt'] = 10
            if latitude is not None:
                params['lat'] = latitude
            if longitude is not None:
                params['lon'] = longitude
            if city is not None:
                params['q'] = city

            response = requests.get(rq_str, params=params)
            if response.status_code != 200:
                logger.error("Get weather error: " + str(response.status_code) + ":" + response.text)
                return "Ошибка получения метеоданных"

            data = response.json()

            city = data["name"]
            cur_weather = data["main"]["temp"]

            condition = Weather.get_weather_condition_desc(data["weather"][0]["main"])

            humidity = data["main"]["humidity"]
            pressure = data["main"]["pressure"]
            wind = data["wind"]["speed"]
            wind_deg = data["wind"]["deg"]
            sunrise_timestamp = datetime.datetime.fromtimestamp(data["sys"]["sunrise"])
            sunset_timestamp = datetime.datetime.fromtimestamp(data["sys"]["sunset"])
            length_of_the_day = sunset_timestamp - sunrise_timestamp

            current_date = datetime.datetime.now()
            result = f"<b>Сегодня</b> {current_date.strftime('%Y-%m-%d %H:%M')}\n" \
                     f"Город: {city}\n" \
                     f"Температура: {cur_weather}C° {condition}\n" \
                     f"Влажность: {humidity}%\n" \
                     f"Давление: {pressure} мм.рт.ст\n" \
                     f"Ветер: {wind} м/с {Weather.get_wind_direction(wind_deg)}\n" \
                     f"Восход солнца: {sunrise_timestamp.strftime('%H:%M')}\n" \
                     f"Закат солнца: {sunset_timestamp.strftime('%H:%M')}\n" \
                     f"Продолжительность дня: {length_of_the_day}\n"

            response = requests.get("http://api.openweathermap.org/data/2.5/forecast", params=params)
            if response.status_code != 200:
                logger.error("Get forecast error: " + str(response.status_code) + ":" + response.text)
                return result

            data = response.json()

            days_list = data["list"]

            logger.info(f'Received {len(days_list)} forecasts')

            result += '<b>Завтра</b>\n'
            result += '     День: ' + Weather.get_forecast_day_weather(days_list, current_date.day + 1, 12) + '\n'
            result += '   Вечер: ' + Weather.get_forecast_day_weather(days_list, current_date.day + 1, 21) + '\n'
            result += '<b>Послезавтра</b>\n'
            result += '     День: ' + Weather.get_forecast_day_weather(days_list, current_date.day + 2, 12) + '\n'
            result += '   Вечер: ' + Weather.get_forecast_day_weather(days_list, current_date.day + 2, 21)
            return result

        except Exception as e:
            logger.error('Weather error: ' + str(e))

        return "Ошибка получения метеоданных"
    # -----------------------------------------------------------------

    @staticmethod
    def get_forecast_day_weather(days_weather, day, hour):
        for day_weather in days_weather:
            date_time = datetime.datetime.fromtimestamp(day_weather['dt'])

            # get only once per day at 12:00
            if date_time.day == day and date_time.hour == hour:
                day_temp = day_weather["main"]["temp"]
                day_condition = Weather.get_weather_condition_desc(day_weather["weather"][0]["main"],
                                                                   include_text=False)
                day_wind = day_weather["wind"]["speed"]
                day_wind_deg = day_weather["wind"]["deg"]
                return f'{day_temp}C° {day_condition} {day_wind}м/с {Weather.get_wind_direction(degrees=day_wind_deg)}'
        return "Данные не найдены"
    # -----------------------------------------------------------------

    def get_weather_by_city(self, city):
        return self.get_current_weather(city=city)
    # -----------------------------------------------------------------

    def get_weather_by_lat_long(self, lat, lon):
        return self.get_current_weather(latitude=lat, longitude=lon)
    # -----------------------------------------------------------------
