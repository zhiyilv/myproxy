import utils
from imp import reload
import redis
from pprint import pprint
from bs4 import BeautifulSoup as bs
from main2 import show_inventory as show
import re
import time
from datetime import datetime


db = redis.StrictRedis(decode_responses=True)
fpl_url = 'https://free-proxy-list.net/'
fpl_res = utils.visit(fpl_url)
# plist = [i for i in utils.parse_fpl_page(fpl_res)]
gurl = 'https://www.google.com'
w_url1 = 'https://whatismyipaddress.com/'
w_url2 = 'http://www.lagado.com/proxy-test'
show()
plist = db.zrange('spool', 0, -1)
pprint(plist)

