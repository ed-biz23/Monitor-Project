import math, pytz, datetime
from pytz import timezone
from http import  cookiejar
from currency_converter import CurrencyConverter

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'}

class BlockAll(cookiejar.CookiePolicy):
    return_ok = set_ok = domain_return_ok = path_return_ok = lambda self, *args, **kwargs: False
    netscape = True
    rfc2965 = hide_cookie2 = False

def parseProxies():
    proxiesLines = [line.rstrip('\n') for line in open('parseProxies.txt', 'r')]
    return proxiesLines

def proxies():
    proxiesLines = [line.rstrip('\n') for line in open('proxies.txt', 'r')]
    return proxiesLines

def getInfoProxy():
    proxiesLines = [line.rstrip('\n') for line in open('infoProxies.txt', 'r')]
    return proxiesLines

def convertCurrency(price, currency):
    try:
        c = CurrencyConverter('http://www.ecb.europa.eu/stats/eurofxref/eurofxref.zip')
        convCurrenPrice = '{}{} ({} {})'.format('$', math.ceil(c.convert(price, currency, 'USD')), price, currency)
    except Exception as e:
        print(getDatetime(), e)
        convCurrenPrice = price + ' ' + currency
    return convCurrenPrice

def getDatetime():
    return '[{}]'.format(str(datetime.datetime.now())[:-3])

def getDate():
    date_format = '%Y-%m-%d'
    date = datetime.datetime.now(tz=pytz.utc)
    date = (date.astimezone(timezone('US/Pacific'))).strftime(date_format)
    return date
