from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ParseMode

import messages as texts
from common import Common

import random
import requests
import time

import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s [%(thread)d] %(name)s[%(levelname)s]: %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


class AcquiringModule(object):
    def __init__(self, bot):
        self.Bot = bot
        self.PSDB_URL = 'http://192.168.56.1:8888'

    @staticmethod
    def get_menu(lang):
        inline_keyboard = [
            [
                InlineKeyboardButton(Common.bar_chart + 'Статистика АС СУС POS', callback_data='bt_psdb_stat_menu'),
            ],
            [
                InlineKeyboardButton(Common.construction_icon + 'Статистика АС PServer', callback_data='bt_pserver_stat_menu'),
            ],
            [
                InlineKeyboardButton(Common.exclamation_icon + 'Уведомления', callback_data='bt_aquiring_notify_menu'),
            ],
            [InlineKeyboardButton(Common.back_icon + texts.MENU_BACK[lang], callback_data='bt_back')]
        ]

        keyboard = InlineKeyboardMarkup(inline_keyboard)

        return Common.card_icon + 'Эквайринг', keyboard
    # ----------------------------------------------------------------------------

    @staticmethod
    def get_psdb_stat_menu(lang):

        inline_keyboard = [
            [
                InlineKeyboardButton('Текущая статистика', callback_data='bt_psdb_stat_menu_current'),
            ],
            [
                InlineKeyboardButton('Час', callback_data='bt_psdb_stat_menu_hour'),
                InlineKeyboardButton('День', callback_data='bt_psdb_stat_menu_day'),
                InlineKeyboardButton('Неделя', callback_data='bt_psdb_stat_menu_week'),
                InlineKeyboardButton('Месяц', callback_data='bt_psdb_stat_menu_month'),
                InlineKeyboardButton('Год', callback_data='bt_psdb_stat_menu_year'),
            ],
            [InlineKeyboardButton(Common.back_icon + texts.MENU_BACK[lang], callback_data='bt_aquiring_menu')]
        ]

        keyboard = InlineKeyboardMarkup(inline_keyboard)
        return Common.bar_chart + 'Статистика АС СУС POS', keyboard
    # ----------------------------------------------------------------------------

    @staticmethod
    def get_current_time():
        return round(time.time() * 1000)
    # ----------------------------------------------------------------------------


    # ----------------------------------------------------------------------------

    def psdb_command(self, user, hours=24) -> None:
        lang = texts.LANG_EN

        # TODO: check user permissions
        #if not self.is_user_admin(update.effective_chat.id, user.id):
            #update.message.reply_html('Операция запрещена')
        #    self.bot.send_message(chat_id=user.id, text='Операция запрещена', parse_mode=ParseMode.HTML)
        #    return

        #msg = self.bot.send_message(chat_id=user.id, text='Запрос статистики...', parse_mode=ParseMode.HTML)
        #msg.edit_text('Получение графиков...', parse_mode=ParseMode.HTML)

        try:
            # ----------  request current metrics data from psdb service
            current_stat_url = self.PSDB_URL + '/data'
            headers = {
                'Accept': 'application/json',
            }
            response = requests.get(current_stat_url, headers=headers)

            json_data = response.json()

            params = json_data['Params']

            result = Common.bar_chart + '<b>Статистика</b>\r\n'

            for param in params:
                param_id = param['Id']
                param_value = param['Value']
                result += Common.black_small_square
                result += param_id + '\r\n'
                result += Common.pass_mark if (random.randint(0, 10) > 2) else Common.fail_mark
                result += '<b>' + param_value + '</b>\r\n'
                result += '\r\n'

            #update.message.reply_html(result)
            self.Bot.send_message(chat_id=user.id, text=result, parse_mode=ParseMode.HTML)

            chart_width = 1000
            chart_height = 500

            # img_url_charts = self.PSDB_URL + '/tg_charts?days=' + days
            time_to = AcquiringModule.get_current_time()
            time_from = time_to - hours * 60 * 60 * 1000
            #time_from = time_to - 5 * 60 * 1000

            # ------------------------
            img_url_charts = 'http://192.168.100.14:3000/render/d-solo/ZmAv4wN7k/psdb-agent?orgId=1&'
            img_url_charts += 'from=' + str(time_from)
            img_url_charts += '&to=' + str(time_to)
            img_url_charts += '&panelId=2&'
            img_url_charts += 'width=' + str(chart_width)
            img_url_charts += '&height=' + str(chart_height)
            img_url_charts += '&tz=Europe%2FMoscow'

            img_response = requests.get(img_url_charts)
            self.Bot.send_photo(
                user.id,
                photo=img_response.content,
                caption='Интеграционный агент',
                parse_mode=ParseMode.HTML
            )

            # ------------------------
            img_url_charts = 'http://192.168.100.14:3000/render/d-solo/ZmAv4wN7k/psdb-agent?orgId=1&'
            img_url_charts += 'from=' + str(time_from)
            img_url_charts += '&to=' + str(time_to)
            img_url_charts += '&panelId=4&'
            img_url_charts += 'width=' + str(chart_width)
            img_url_charts += '&height=' + str(chart_height)
            img_url_charts += '&tz=Europe%2FMoscow'

            img_response = requests.get(img_url_charts)
            self.Bot.send_photo(
                user.id,
                photo=img_response.content,
                caption='БД СУС POS',
                parse_mode=ParseMode.HTML
            )

            # ------------------------
            img_url_charts = 'http://192.168.100.14:3000/render/d-solo/ZmAv4wN7k/psdb-agent?orgId=1&'
            img_url_charts += 'from=' + str(time_from)
            img_url_charts += '&to=' + str(time_to)
            img_url_charts += '&panelId=14&'
            img_url_charts += 'width=' + str(chart_width)
            img_url_charts += '&height=' + str(chart_height)
            img_url_charts += '&tz=Europe%2FMoscow'

            img_response = requests.get(img_url_charts)
            self.Bot.send_photo(
                user.id,
                photo=img_response.content,
                caption='Терминалы',
                parse_mode=ParseMode.HTML
            )

            # ------------------------
            img_url_charts = 'http://192.168.100.14:3000/render/d-solo/ZmAv4wN7k/psdb-agent?orgId=1&'
            img_url_charts += 'from=' + str(time_from)
            img_url_charts += '&to=' + str(time_to)
            img_url_charts += '&panelId=6&'
            img_url_charts += 'width=' + str(chart_width)
            img_url_charts += '&height=' + str(chart_height)
            img_url_charts += '&tz=Europe%2FMoscow'

            img_response = requests.get(img_url_charts)
            self.Bot.send_photo(
                user.id,
                photo=img_response.content,
                caption='Регистрации',
                parse_mode=ParseMode.HTML
            )



            '''
            img_json_data = img_response.json()
            charts = img_json_data['Charts']

            for chart in charts:
                chart_title = chart['Title']
                chart_img = chart['Image']

                self.Bot.send_photo(
                    user.id,
                    photo=chart_img,
                    caption=chart_title,
                    parse_mode=ParseMode.HTML
                )
            '''

            '''
            with open('stat.png', 'rb') as img:
                self.Bot.send_photo(
                    user.id,
                    photo=img,
                    caption='График 1',
                    parse_mode=ParseMode.HTML
                )
                img.close()
            '''
            return True

        except Exception as e:
            logger.error(e)
            return False
    # ----------------------------------------------------------------------------
