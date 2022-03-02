import datetime
import  logging

# Enable logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(thread)d] %(name)s[%(levelname)s]: %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler(f'log.txt', encoding='utf-8')]
)

from echobot import EchoBot
import parsers
import weather

logger = logging.getLogger(__name__)

def main():
    logger.info('\n----------------------------- STARTING ECHO BOT ---------------------------------------------------')
    EchoBot()

    #parser = parsers.SmartParser(0)
    #res = parser.GetTVChannels(None, None)
    #print(res)

    #wthr = weather.Weather()
    #res = wthr.get_weather_by_city("moscow")
    #res = wthr.get_weather_by_lat_long(lat=55.386539, lon=37.40034)
    #print(res)


if __name__ == '__main__':
    main()
