# tg-multibot
Multi-purpose Telegram bot

Important! It is not a ready-to-complile project.

Functions:
1. Comiing soon movies list from kinopoisk.ru (Russia specific)
2. TV program (not finished yet) from mail.ru (Russia specific)
3. Shows current weather and forecast by attached geo-location
4. Convert attached videos to gif (may not work well yet =))
6. Converts attached imaged to ascii
7. Get products and prices information by QR link from payed cheque from nalog.ru
8. Some test functions (that may not work well yet =))

Ready to launch from PyCharm IDE or with following command line:
python main.py


Requirements
1. ".env" file in the root (that contains some credential information to login to nalog.ru site) of type:
CLIENT_SECRET=
INN=
PASSWORD=
2. Environment variables:
TOKEN - Telegram bot token
CHAT_ID - Telegram chat id
DATABASE_URL - Test postgres database
OPENWEATHER_TOKEN - Openweather token
