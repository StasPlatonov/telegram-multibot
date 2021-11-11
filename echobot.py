#!/usr/bin/env python
# pylint: disable=W0613, C0116
# type: ignore[union-attr]

import logging
import os
import sys

import requests

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import parsers

from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram import ParseMode
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import CallbackQueryHandler
from telegram.ext.dispatcher import run_async
from telegram import TelegramError
from telegram import ChatAction

from storage import SmartStorage
from acquiring import AcquiringModule

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

from pytube import YouTube

from moviepy.editor import *

import messages as texts

from ascii import AsciiProcessor
from nalog import NalogRuPython
from common import Common
import weather

import json
import random
'''
Limitations:
    Messages can be sent to the same chat with frequency of not more than 20 messages per minute
    Messages can be sent to different chats with frequency of not more than 30 messages per second 
'''

# Enable logging
logging.basicConfig(
    format='%(asctime)s [%(thread)d] %(name)s[%(levelname)s]: %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)
# ----------------------------------------------------------------------------


class EchoBot(object):
    def __init__(self):
        self.updater = Updater(os.environ["TOKEN"], use_context=True, workers=32)

        # Get the dispatcher to register handlers
        self.dispatcher = self.updater.dispatcher
        self.bot = self.dispatcher.bot

        self.storage = SmartStorage(os.environ["DATABASE_URL"])
        self.scheduler = BackgroundScheduler()

        self.acquiring = AcquiringModule(self.bot)

        self.weather = weather.Weather()

        self.button_handlers = {'bt_rus': self.bt_rus_handler,
                                'bt_eng': self.bt_eng_handler,
                                'bt_subscribe': self.bt_subscribe_handler,
                                'bt_unsubscribe': self.bt_unsubscribe_handler,
                                'bt_settings': self.bt_settings_handler,
                                'bt_back': self.bt_back_handler,
                                'bt_close_menu': self.bt_close_menu_handler,
                                'bt_acquiring_menu': self.bt_acquiring_menu_handler,
                                'bt_psdb_stat_menu': self.bt_psdb_stat_menu_handler,
                                'bt_psdb_stat_menu_current': self.bt_psdb_stat_menu_current_handler,
                                'bt_psdb_stat_menu_hour': self.bt_psdb_stat_menu_hour_handler,
                                'bt_psdb_stat_menu_day': self.bt_psdb_stat_menu_day_handler,
                                'bt_psdb_stat_menu_week': self.bt_psdb_stat_menu_week_handler,
                                'bt_psdb_stat_menu_month': self.bt_psdb_stat_menu_month_handler,
                                'bt_psdb_stat_menu_year': self.bt_psdb_stat_menu_year_handler,
                                }
        self.run()
    # ----------------------------------------------------------------------------

    @staticmethod
    def get_error_message():
        return Common.fail_mark + 'Ошибка выполнения команды'
    # ----------------------------------------------------------------------------

    @staticmethod
    def get_help_text(lang) -> str:

        result = f'{texts.HELP_TITLE[lang]}:\r\n'
        result += f'<b>/help</b> - {texts.HELP_TITLE[lang]}\r\n'
        result += f'<b>/menu</b> - {texts.MENU_MENU[lang]}\r\n'
        result += f'<b>/subscribe</b> - {texts.MENU_SUBSCRIBE[lang]}\r\n'
        result += f'<b>/unsubscribe</b> - {texts.MENU_UNSUBSCRIBE[lang]}\r\n'
        result += f'<b>/cs</b> - {texts.MENU_COMING_SOON[lang]}\r\n'
        result += f'<b>/cse</b> - {texts.MENU_COMING_SOON_EX[lang]}\r\n'
        result += f'<b>/tv</b> - {texts.MENU_TV[lang]}\r\n'

        return result
    # ----------------------------------------------------------------------------

    def help_command(self, update: Update, context: CallbackContext) -> None:
        existing = self.storage.get_user(update.message.from_user.id)
        lang = texts.LANG_EN if ((existing is None) or (existing.language is None)) else existing.language

        update.message.reply_html(EchoBot.get_help_text(lang))
    # ----------------------------------------------------------------------------

    def menu_command(self, update: Update, context: CallbackContext) -> None:
        existing = self.storage.get_user(update.message.from_user.id)
        lang = texts.LANG_EN if ((existing is None) or (existing.language is None)) else existing.language

        main_menu = self.get_main_menu(update, context)
        update.message.reply_html(text=texts.MSG_MAIN_MENU[lang], reply_markup=main_menu)
    # ----------------------------------------------------------------------------

    def youtube_buttons_handler(self, update: Update, context: CallbackContext) -> None:
        userid = update.effective_chat.id
        existing = self.storage.get_user(userid)
        lang = texts.LANG_EN if ((existing is None) or (existing.language is None)) else existing.language

        query = update.callback_query

        # CallbackQueries need to be answered, even if no notification to the user is needed
        # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
        query.answer()  # required for inline keyboard !!!!

        params = query.data.split("_")
        chat = params[1]
        resolution = params[2]
        if resolution == 'cancel':
            update.callback_query.edit_message_text(text=texts.MSG_CANCELED[lang])
            return

        link = params[3]
        try:
            logger.info('Downloading video of quality ' + resolution)

            # Download video
            yt = YouTube(link)
            stream = yt.streams.filter(progressive=True, subtype='mp4', resolution=resolution).first()
            stream.download(filename=f'{chat}_video')

            # Send video
            update.callback_query.edit_message_text(text=texts.MSG_YOUTUBE_SENDING[lang])
            logger.info(f'Sending video to {chat}...')
            with open(f'{chat}_video.mp4', 'rb') as f:
                self.bot.send_video(chat_id=chat, caption='',
                                    video=f,
                                    timeout=1000)
            logger.info(f'Video sent to {chat}...')
        except Exception as e:
            logger.error("Failed to send video: " + str(e))
            update.callback_query.edit_message_text(text=texts.MSG_YOUTUBE_ERROR[lang])
    # ----------------------------------------------------------------------------

    @run_async
    def youtube_link_handler(self, update: Update, context: CallbackContext):
        userid = update.effective_chat.id
        #existing = self.storage.get_user(userid)
        #lang = texts.LANG_EN if ((existing is None) or (existing.language is None)) else existing.language
        lang = texts.LANG_EN

        # Send waiting message to user
        msg = self.bot.send_message(chat_id=userid, text=texts.MSG_PLEASE_WAIT[lang], parse_mode=ParseMode.HTML)

        try:
            # Get available streams
            yt = YouTube(update.message.text)
            filtered_streams = yt.streams.filter(progressive=True, subtype='mp4').order_by('resolution').desc()

            if len(filtered_streams) == 0:
                msg.edit_text(text=texts.MSG_YOUTUBE_ERROR[lang])
                return

            # Create menu with available resolutions
            quality_keyboard_buttons = []
            for stream in filtered_streams:
                cb_data = f'ybt_{userid}_{stream.resolution}_{update.message.text}'
                quality_keyboard_buttons += [InlineKeyboardButton(stream.resolution,
                                                                  callback_data=cb_data)]

            # Add cancel option
            cb_data = f'ybt_{userid}_cancel'
            quality_keyboard_buttons += [InlineKeyboardButton(texts.MSG_CANCEL[lang],
                                                              callback_data=cb_data)]
            # Create menu
            quality_menu = InlineKeyboardMarkup(inline_keyboard=[quality_keyboard_buttons],
                                                resize_keyboard=True,
                                                one_time_keyboard=True)

            # Send reply
            msg.edit_text(text=texts.MSG_YOUTUBE_SELECT_QUALITY[lang], reply_markup=quality_menu)
        except Exception as e:
            logger.error("Youtube handler error: " + str(e))
    # ----------------------------------------------------------------------------

    def handle_message_from_chat(self, chat_id, update: Update, context: CallbackContext) -> None:
        logger.info(f'Message from chat {chat_id} will not be handled')
    # ----------------------------------------------------------------------------

    def handle_qr_code(self, update: Update, context: CallbackContext) -> None:
        client = NalogRuPython()
        # QR link is like "t=20200709T2008&s=7273.00&fn=9282440300688488&i=14186&fp=1460060363&n=1"

        qr_code = update.message.text[5:]

        ticket_json = client.get_ticket(qr_code)

        #with open('tmp.txt', 'w') as outfile:
        #    json.dump(ticket, outfile, indent=4, ensure_ascii=False)
        '''
        ticket = ''
        with open('cheque.txt') as json_file:
            ticket = json.load(json_file)
        '''
        #print(json.dumps(ticket, indent=4, ensure_ascii=False))

        responses = parsers.SmartParser(0).ParseNalogTicket(ticket_json)

        for response in responses:
            update.message.reply_html(response)
    # ----------------------------------------------------------------------------

    def handle_text(self, update: Update, context: CallbackContext) -> None:
        if update.message is None:
            if update.effective_chat is not None:
                self.handle_message_from_chat(update.effective_chat.id, update, context)
            return

        user = update.message.from_user
        logger.info('Message from user %s (id:%d, bot:%d): %s', user.first_name, user.id, user.is_bot, update.message.text)
        logger.info('Chat info: %d/%s', update.message.chat.id, update.message.chat.type)

        if update.message.text.startswith('https://youtu.be') or update.message.text.startswith('https://youtube.com'):
            self.youtube_link_handler(update, context)
            return

        if update.message.text.startswith('qr://'):
            self.handle_qr_code(update, context)
            return

        #logger.info(f'Result size: {len(result)}')
        # Just echo
        update.message.reply_text(update.message.text)
    # ----------------------------------------------------------------------------

    def convert_to_ascii_and_send(self, update: Update, context: CallbackContext, in_file_name, text, lang) -> None:
        user = update.message.from_user
        out_file_name = f'{user.id}_out.jpg'

        ascii_processor = AsciiProcessor()
        ascii_processor.convert_to_ascii(in_file_name, out_file_name, text)

        emoji = u'\U0001F63B'

        caption = texts.MSG_ASCII_FINAL[lang] + emoji

        # Send image file with caption
        with open(out_file_name, 'rb') as img:
            context.bot.send_photo(
                user.id,
                photo=img,
                caption=caption,
                parse_mode=ParseMode.HTML
            )
            img.close()
        os.remove(out_file_name)
    # ----------------------------------------------------------------------------

    #@run_async
    def handle_photo(self, update: Update, context: CallbackContext) -> None:
        user = update.message.from_user
        existing = self.storage.get_user(user.id)
        lang = texts.LANG_EN if ((existing is None) or (existing.language is None)) else existing.language

        logger.info('Photo from user %s (id:%d, bot:%d)', user.first_name, user.id, user.is_bot)

        if not update.message.photo:
            update.message.reply_text(update.message.caption)

        try:
            logger.info("Photo attached")
            photo = update.message.photo[-1]  # photo is array of photos, so get the biggest one,

            file = self.bot.getFile(photo.file_id)

            in_file_name = f'{user.id}_in.jpg'
            msg = self.bot.send_message(chat_id=user.id, text=texts.MSG_DOWNLOADING[lang], parse_mode=ParseMode.HTML)

            file.download(in_file_name)
            msg.edit_text(texts.MSG_PROCESSING[lang], parse_mode=ParseMode.HTML)

            # convert to ascii
            self.convert_to_ascii_and_send(update, context, in_file_name, update.message.caption, lang)

            os.remove(in_file_name)
        except ValueError as e:
            update.message.reply_text('Error')
    # ----------------------------------------------------------------------------

    def handle_voice(self, update: Update, context: CallbackContext) -> None:
        user = update.message.from_user
        logger.info('Message from user %s (id:%d, bot:%d)', user.first_name, user.id, user.is_bot)

        if update.message.voice:
            logger.info("Voice attached")
            voice_file = update.message.voice.get_file()
            voice_file.download('voice.ogg')

        update.message.reply_text(update.message.caption)
    # ----------------------------------------------------------------------------

    def handle_audio(self, update: Update, context: CallbackContext) -> None:
        user = update.message.from_user
        logger.info('Message from user %s (id:%d, bot:%d)', user.first_name, user.id, user.is_bot)

        if update.message.audio:
            logger.info("Audio attached")
            audio_file = update.message.audio.get_file()
            audio_file.download('audio.ogg')

        update.message.reply_text(update.message.caption)
    # ----------------------------------------------------------------------------

    def time_symetrize(self, clip):
        """ Returns the clip played forwards then backwards. In case
        you are wondering, vfx (short for Video FX) is loaded by
        >>> from moviepy.editor import * """
        return concatenate([clip, clip.fx(vfx.time_mirror)])

    @run_async
    def handle_video(self, update: Update, context: CallbackContext) -> None:
        user = update.message.from_user
        existing = self.storage.get_user(user.id)
        lang = texts.LANG_EN if ((existing is None) or (existing.language is None)) else existing.language

        video_duration_limit = 5

        logger.info('Message from user %s (id:%d, bot:%d)', user.first_name, user.id, user.is_bot)

        if not update.message.video:
            update.message.reply_text('No video found')
            return

        # Send waiting message to user
        msg = self.bot.send_message(chat_id=user.id, text=texts.MSG_DOWNLOADING[lang], parse_mode=ParseMode.HTML)

        sz = update.message.video.file_size
        logger.info(f'Attached video size: {sz} bytes')
        try:
            video_file = update.message.video.get_file()
            in_file_name = f'{user.id}_{update.message.video.file_name}'
            video_file.download(in_file_name)

            logger.info('Video received')

            clip = VideoFileClip(in_file_name, audio=False).resize(0.25)
            logger.info(f'Video dimensions: {clip.size}, duration: {clip.duration}')

            if clip.duration > video_duration_limit:
                logger.info(f'Too long video({clip.size})')
                clip.close()
                msg.edit_text(text=texts.MSG_GIF_DURATION_LIMIT[lang] + ' ' + video_duration_limit)
                return

            edited_clip = clip.fx(self.time_symetrize)

            msg.edit_text(text=texts.MSG_PROCESSING[lang])
            out_file_name = f'{user.id}_out.gif'
            edited_clip.write_gif(out_file_name, fps=10)

            clip.close()
            edited_clip.close()
            logger.info(f'Gif {out_file_name} written')

            anim_icon = u'\U0001F3AC'
            clap_hands_icon = u'\U0001F44F'
            with open(out_file_name, 'rb') as file:
                caption = anim_icon + texts.MSG_GIF_FINAL[lang] + '\r\n'
                caption += texts.MSG_GIF_SHARE[lang] + clap_hands_icon
                self.bot.send_animation(chat_id=update.effective_chat.id, caption=caption,
                                        animation=file,
                                        timeout=1000, parse_mode=ParseMode.HTML)
                file.close()
            os.remove(in_file_name)
            os.remove(out_file_name)

        except ValueError as e:
            logger.info('Failed to download video: ' + str(e))
    # ----------------------------------------------------------------------------

    def quotes_command(self, update: Update, context: CallbackContext) -> None:
        try:
            parser = parsers.SmartParser(0)

            result = parser.ParseQuotes(requests.get('https://quotes.toscrape.com/'))

            update.message.reply_text(result)

        except Exception as e:
            print("ERROR: Parser error: " + str(e))
    # ----------------------------------------------------------------------------

    def prices_command(self, update: Update, context: CallbackContext) -> None:
        try:
            parser = parsers.SmartParser(0)

            result = parser.ParsePrices('https://scrapingclub.com/exercise/list_basic/')

            update.message.reply_text(result)

        except Exception as e:
            print("ERROR: Parser error: " + str(e))
    # ----------------------------------------------------------------------------

    def comingsoon_command(self, update: Update, context: CallbackContext) -> None:
        try:
            self.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

            parser = parsers.SmartParser(0)

            result = parser.ParseComingSoonMovies()

            update.message.reply_html(result)

        except Exception as e:
            print("ERROR: Parser error: " + str(e))
    # ----------------------------------------------------------------------------

    def comingsoon_ex_command(self, update: Update, context: CallbackContext) -> None:
        try:
            self.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
            parser = parsers.SmartParser(0)

            result = parser.ParseComingSoonExMovies(context.bot, update.message.chat_id)

            # update.message.reply_html(result)

            # context.bot.send_media_group(chat_id=update.message.chat_id, media=result)
            # update.message.reply_html("OK")

        except Exception as e:
            print("ERROR: Parser error: " + str(e))
    # ----------------------------------------------------------------------------

    def tv_command(self, update: Update, context: CallbackContext) -> None:
        try:
            self.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
            parser = parsers.SmartParser(0)

            result = parser.ParseTVProgram(context.bot, update.message.chat_id)

        except Exception as e:
            print("ERROR: Parser error: " + str(e))
    # ----------------------------------------------------------------------------

    def post_command(self, update: Update, context: CallbackContext) -> None:
        chat_id = os.environ["CHAT_ID"]
        # user = update.message.from_user

        # context.bot.send_message(chat_id=chat_id, text='<b>Repost:</b><i>' + update.message.text + '</i>', parse_mode=ParseMode.HTML)

        emoji = u'\U0001F63B'

        caption = "<b>Meow!</b><a href='https://somelink.com'> More cats here!</a> " + emoji
        context.bot.send_photo(
            chat_id,
            photo='https://www.fresher.ru/wp-content/uploads/2018/03/1.jpg',
            caption=caption,
            parse_mode=ParseMode.HTML
        )

        '''
        # Send image file with caption
        with open('test.jpg', 'rb') as img:
            caption = "<b>Repost</b><a href='https://somelink.com'>More cats</a>"
            context.bot.send_photo(
                chat_id, 
                photo=img, 
                caption=caption,
                parse_mode=ParseMode.HTML
            )
        '''

        # update.message.reply_text(update.message.text)
    # ----------------------------------------------------------------------------

    def do_subscribe(self, tg_user):
        if tg_user.is_bot:
            logger.error("Bot can not subscribe")
            return None

        user = self.storage.get_user(tg_user.id)

        if user is not None:
            logger.warning('Already subscribed')
        else:
            user = self.storage.add_user(tg_user.id, tg_user.username, tg_user.first_name, tg_user.last_name)

        return user
    # ----------------------------------------------------------------------------

    def do_unsubscribe(self, tg_user):
        if tg_user.is_bot:
            logger.error("Bot can not unsubscribe")
            return

        existing = self.storage.get_user(tg_user.id)

        if existing is None:
            logger.warning('Already unsubscribed')
            return

        self.storage.delete_user(tg_user.id)
    # ----------------------------------------------------------------------------

    def subscribe_command(self, update: Update, context: CallbackContext) -> None:
        user = self.do_subscribe(update.message.from_user)
        lang = texts.LANG_EN if ((user is None) or (user.language is None)) else user.language
        update.message.reply_text(texts.MSG_SUBSCRIBED[lang])
    # ----------------------------------------------------------------------------

    def unsubscribe_command(self, update: Update, context: CallbackContext) -> None:
        # store user to use its language in reply
        existing = self.storage.get_user(update.message.from_user.id)

        self.do_unsubscribe(update.message.from_user)

        lang = texts.LANG_EN if ((existing is None) or (existing.language is None)) else existing.language
        update.message.reply_text(texts.MSG_UNSUBSCRIBED[lang])
    # ----------------------------------------------------------------------------

    def bt_rus_handler(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        user = self.storage.get_user(update.effective_chat.id)
        if user is None:
            query.edit_message_text(text=f'Subscribe first')
            return
        user.language = texts.LANG_RU

        self.storage.update_user(update.effective_chat.id, user)

        logger.info(f'Language of {user.id} changed to {user.language}')

        # show settings again to refresh data
        self.bt_settings_handler(update, context)
    # ----------------------------------------------------------------------------

    def bt_eng_handler(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        user = self.storage.get_user(update.effective_chat.id)
        if user is None:
            query.edit_message_text(text=f'Subscribe first')
            return

        user.language = texts.LANG_EN

        self.storage.update_user(update.effective_chat.id, user)

        logger.info(f'Language of {user.id} changed to {user.language}')

        # show settings again to refresh data
        self.bt_settings_handler(update, context)
    # ----------------------------------------------------------------------------

    def bt_subscribe_handler(self, update: Update, context: CallbackContext) -> None:
        user = self.do_subscribe(update.effective_user)

        lang = texts.LANG_EN if ((user is None) or (user.language is None)) else user.language
        update.callback_query.edit_message_text(text=texts.MSG_SUBSCRIBED[lang])
    # ----------------------------------------------------------------------------

    def bt_unsubscribe_handler(self, update: Update, context: CallbackContext) -> None:
        # store user to use its language in reply
        existing = self.storage.get_user(update.effective_user.id)

        self.do_unsubscribe(update.effective_user)

        lang = texts.LANG_EN if ((existing is None) or (existing.language is None)) else existing.language
        update.callback_query.edit_message_text(text=texts.MSG_UNSUBSCRIBED[lang])
    # ----------------------------------------------------------------------------

    def get_main_menu(self, update: Update, context: CallbackContext):
        user = self.storage.get_user(update.effective_chat.id)
        lang = texts.LANG_EN if ((user is None) or (user.language is None)) else user.language

        inline_keyboard = [
            [
                InlineKeyboardButton(texts.MENU_SUBSCRIBE[lang], callback_data='bt_subscribe'),
                InlineKeyboardButton(texts.MENU_UNSUBSCRIBE[lang], callback_data='bt_unsubscribe')
            ],
            [InlineKeyboardButton(Common.card_icon + 'Эквайринг', callback_data='bt_acquiring_menu')],
            [InlineKeyboardButton(Common.settings_icon + ' ' + texts.MENU_SETTINGS[lang], callback_data='bt_settings')],
            [InlineKeyboardButton(Common.close_icon + ' ' + texts.MENU_CLOSE[lang], callback_data='bt_close_menu')],
        ]
        main_menu = InlineKeyboardMarkup(inline_keyboard, resize_keyboard=True, one_time_keyboard=True)

        return main_menu
    # ----------------------------------------------------------------------------

    def bt_acquiring_menu_handler(self, update: Update, context: CallbackContext) -> None:
        #user = self.storage.get_user(update.effective_chat.id)
        #lang = texts.LANG_EN if ((user is None) or (user.language is None)) else user.language
        lang = texts.LANG_RU

        acquiring_caption, acquiring_menu = AcquiringModule.get_menu(lang=lang)
        update.callback_query.edit_message_text(text=acquiring_caption, reply_markup=acquiring_menu,
                                                parse_mode=ParseMode.HTML)
    # ----------------------------------------------------------------------------

    def bt_psdb_stat_menu_handler(self, update: Update, context: CallbackContext) -> None:
        #user = self.storage.get_user(update.effective_chat.id)
        #lang = texts.LANG_EN if ((user is None) or (user.language is None)) else user.language

        #self.psdb_command(update, context)
        lang = texts.LANG_RU

        psdb_menu_caption, psdb_stat_menu = AcquiringModule.get_psdb_stat_menu(lang=lang)
        update.callback_query.edit_message_text(text=psdb_menu_caption, reply_markup=psdb_stat_menu,
                                                parse_mode=ParseMode.HTML)
    # ----------------------------------------------------------------------------

    def bt_psdb_stat_menu_current_handler(self, update: Update, context: CallbackContext) -> None:
        if self.acquiring.psdb_command(user=update.effective_user, hours=0) is True:
            update.callback_query.edit_message_text(text=Common.pass_mark + 'Выполнено')
        else:
            update.callback_query.edit_message_text(text=EchoBot.get_error_message(), parse_mode=ParseMode.HTML)
    # ----------------------------------------------------------------------------

    def bt_psdb_stat_menu_hour_handler(self, update: Update, context: CallbackContext) -> None:
        if self.acquiring.psdb_command(user=update.effective_user, hours=1) is True:
            update.callback_query.edit_message_text(text=Common.pass_mark + 'Выполнено')
        else:
            update.callback_query.edit_message_text(text=EchoBot.get_error_message(), parse_mode=ParseMode.HTML)
    # ----------------------------------------------------------------------------

    def bt_psdb_stat_menu_day_handler(self, update: Update, context: CallbackContext) -> None:
        if self.acquiring.psdb_command(user=update.effective_user, hours=24) is True:
            update.callback_query.edit_message_text(text=Common.pass_mark + 'Выполнено')
        else:
            update.callback_query.edit_message_text(text=EchoBot.get_error_message(), parse_mode=ParseMode.HTML)
    # ----------------------------------------------------------------------------

    def bt_psdb_stat_menu_week_handler(self, update: Update, context: CallbackContext) -> None:
        if self.acquiring.psdb_command(user=update.effective_user, hours=7 * 24) is True:
            update.callback_query.edit_message_text(text=Common.pass_mark + 'Выполнено')
        else:
            update.callback_query.edit_message_text(text=EchoBot.get_error_message(), parse_mode=ParseMode.HTML)
    # ----------------------------------------------------------------------------

    def bt_psdb_stat_menu_month_handler(self, update: Update, context: CallbackContext) -> None:
        if self.acquiring.psdb_command(user=update.effective_user, hours=30 * 24) is True:
            update.callback_query.edit_message_text(text=Common.pass_mark + 'Выполнено')
        else:
            update.callback_query.edit_message_text(text=EchoBot.get_error_message(), parse_mode=ParseMode.HTML)
    # ----------------------------------------------------------------------------

    def bt_psdb_stat_menu_year_handler(self, update: Update, context: CallbackContext) -> None:
        if self.acquiring.psdb_command(user=update.effective_user, hours=365 * 24) is True:
            update.callback_query.edit_message_text(text=Common.pass_mark + 'Выполнено')
        else:
            update.callback_query.edit_message_text(text=EchoBot.get_error_message(), parse_mode=ParseMode.HTML)
    # ----------------------------------------------------------------------------

    def bt_close_menu_handler(self, update: Update, context: CallbackContext) -> None:
        user = self.storage.get_user(update.effective_chat.id)
        lang = texts.LANG_EN if ((user is None) or (user.language is None)) else user.language

        update.callback_query.edit_message_text(text=texts.MSG_MENU_CLOSED[lang])
    # ----------------------------------------------------------------------------

    def bt_back_handler(self, update: Update, context: CallbackContext) -> None:
        user = self.storage.get_user(update.effective_chat.id)
        lang = texts.LANG_EN if ((user is None) or (user.language is None)) else user.language

        main_menu = self.get_main_menu(update, context)
        update.callback_query.edit_message_text(text=texts.MSG_MAIN_MENU[lang], reply_markup=main_menu)
    # ----------------------------------------------------------------------------

    def bt_settings_handler(self, update: Update, context: CallbackContext) -> None:
        user = self.storage.get_user(update.effective_chat.id)
        lang = texts.LANG_EN if ((user is None) or (user.language is None)) else user.language

        inline_keyboard = [
            [
                InlineKeyboardButton((Common.check_icon if lang == texts.LANG_RU else '') + 'Русский {}'.format(b'\xF0\x9F\x87\xB7\xF0\x9F\x87\xBA'.decode()),
                                     callback_data='bt_rus'),
                InlineKeyboardButton((Common.check_icon if lang == texts.LANG_EN else '') + 'English {}'.format(b'\xF0\x9F\x87\xAC\xF0\x9F\x87\xA7'.decode()),
                                     callback_data='bt_eng')
            ],
            [InlineKeyboardButton(Common.back_icon + texts.MENU_BACK[lang], callback_data='bt_back')],
        ]
        settings_menu = InlineKeyboardMarkup(inline_keyboard)
        update.callback_query.edit_message_text(text=Common.settings_icon + texts.MENU_SETTINGS[lang], reply_markup=settings_menu, parse_mode=ParseMode.HTML)
    # ----------------------------------------------------------------------------

    def ask_frequency_question(self, bot, chat_id):
        user = self.storage.get_user(chat_id)
        lang = texts.LANG_EN if ((user is None) or (user.language is None)) else user.language

        frequency_markup = InlineKeyboardMarkup([[
            InlineKeyboardButton(texts.FREQUENCY_NONE[lang], callback_data='none'),
            InlineKeyboardButton(texts.FREQUENCY_DAILY[lang], callback_data='daily'),
            InlineKeyboardButton(texts.FREQUENCY_WEEKLY[lang], callback_data='weekly')]])
        bot.send_message(text=texts.FREQUENCY_QUESTION[lang], reply_markup=frequency_markup, chat_id=chat_id)
    # ----------------------------------------------------------------------------

    def buttons_handler(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query

        # CallbackQueries need to be answered, even if no notification to the user is needed
        # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
        query.answer()  # required for inline keyboard !!!!

        if self.button_handlers.get(query.data) is None:
            logger.error(f'No action defined for button {query.data}')
            query.edit_message_text(text=EchoBot.get_error_message(), parse_mode=ParseMode.HTML)
            return

        self.button_handlers[query.data](update, context)
    # ----------------------------------------------------------------------------

    def is_user_admin(self, chatid, userid):
        try:
            admins = self.bot.get_chat_administrators(chatid)
            return True if userid in admins else False
        except TelegramError as e:
            logger.error(e)
        except Exception as e:
            logger.error(e)
        return False
    # ----------------------------------------------------------------------------

    def start_command(self, update: Update, context: CallbackContext) -> None:
        # user = self.storage.get_user(update.effective_chat.id)
        user = self.storage.get_user(update.effective_user.id)
        lang = texts.LANG_EN if ((user is None) or (user.language is None)) else user.language

        is_admin = self.is_user_admin(update.effective_chat.id, user.id)
        logger.info(f'User is admin: {is_admin}')

        greeting = texts.GREETING[lang] + '\r\n'
        greeting += EchoBot.get_help_text(lang)

        # Send help commands first
        update.message.reply_html(greeting)

        # Then open menu
        main_menu = self.get_main_menu(update, context)
        self.bot.send_message(update.message.from_user.id, texts.MSG_MAIN_MENU[lang], reply_markup=main_menu)
    # ----------------------------------------------------------------------------

    def scheduler_handler(self):
        current_time = datetime.now()
        print('Execute scheduler at %s' % current_time)

        #subscribers = self.storage.enum_subscribers()
        #for subscriber in subscribers:
        #    self.bot.send_message(subscriber.userid, "Notification")

        # Request some data to another URL
        url = f'https://quoters.apps.pcfone.io/api/random'
        '''request = {
            'request': 'rq_id',
            'client_secret': os.getenv('CLIENT_SECRET'),
            'password': os.getenv('PASSWORD')
        }
        headers = {
            'Host': '1.1.1.1'
        }
        resp = requests.post(url, json=request, headers=headers)
        '''
        resp = requests.get(url)
        response = resp.json()
        resp_value = response['value']

        # Send response to group channel
        channel_chat_id = os.environ["CHAT_ID"]
        msg = '<b>Обновление</b>\r\n'
        msg += 'от ' + datetime.now().strftime('%d.%m.%Y %H:%M') + '\r\n'
        msg += 'Цитата: "' + resp_value['quote'] + '"'
        self.bot.send_message(channel_chat_id, msg, ParseMode.HTML)
    # ----------------------------------------------------------------------------

    def send_greeting(self):
        # Send response to group channel
        channel_chat_id = os.environ["CHAT_ID"]
        msg = '<b>Bot started</b>\r\n'
        msg += 'at ' + datetime.now().strftime('%d.%m.%Y %H:%M') + '\r\n'
        self.bot.send_message(channel_chat_id, msg, ParseMode.HTML)
    # ----------------------------------------------------------------------------

    def handle_location(self, update: Update, context: CallbackContext) -> None:
        user = update.message.from_user
        logger.info('Location from user %s (id:%d, bot:%d)', user.first_name, user.id, user.is_bot)

        if update.message.location:
            logger.info(f"Location attached"
                        f"(lat:{update.message.location.latitude}, lon:{update.message.location.longitude})")

            result = self.weather.get_weather_by_lat_long(update.message.location.latitude,
                                                          update.message.location.longitude)
            update.message.reply_text(result, parse_mode=ParseMode.HTML)
            return

        update.message.reply_text("No location")
    # ----------------------------------------------------------------------------

    def run(self):
        current_time = datetime.now()
        logger.info('Starting bot at %s' % current_time)

        users = self.storage.enum_users()
        logger.info(f'Total users: {len(users)}')

        self.dispatcher.add_handler(CommandHandler("start", self.start_command))
        self.dispatcher.add_handler(CommandHandler("help", self.help_command))
        self.dispatcher.add_handler(CommandHandler("menu", self.menu_command))
        self.dispatcher.add_handler(CommandHandler("quotes", self.quotes_command))
        self.dispatcher.add_handler(CommandHandler("prices", self.prices_command))
        self.dispatcher.add_handler(CommandHandler("cs", self.comingsoon_command))
        self.dispatcher.add_handler(CommandHandler("cse", self.comingsoon_ex_command))
        self.dispatcher.add_handler(CommandHandler("post", self.post_command))
        self.dispatcher.add_handler(CommandHandler("subscribe", self.subscribe_command))
        self.dispatcher.add_handler(CommandHandler("unsubscribe", self.unsubscribe_command))
        self.dispatcher.add_handler(CommandHandler("tv", self.tv_command))

        self.dispatcher.add_handler(CallbackQueryHandler(self.buttons_handler, pattern=r'^bt_'))
        self.dispatcher.add_handler(CallbackQueryHandler(self.youtube_buttons_handler, pattern=r'^ybt_'))

        self.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_text))
        self.dispatcher.add_handler(MessageHandler(Filters.photo, self.handle_photo))
        self.dispatcher.add_handler(MessageHandler(Filters.voice, self.handle_voice))
        self.dispatcher.add_handler(MessageHandler(Filters.audio, self.handle_audio))
        self.dispatcher.add_handler(MessageHandler(Filters.video, self.handle_video, run_async=True))
        self.dispatcher.add_handler(MessageHandler(Filters.location, self.handle_location))

        #self.scheduler.add_job(self.scheduler_handler, 'cron', day_of_week='mon-sun', hour=22)
        #self.scheduler.add_job(self.scheduler_handler, 'interval', minutes=2)

        #self.scheduler.start()

        # Start the Bot
        self.updater.start_polling()

        # self.send_greeting()

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        self.updater.idle()

        self.scheduler.shutdown()
    # ----------------------------------------------------------------------------
