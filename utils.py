import requests as r
from bs4 import BeautifulSoup as bs
import re
import time


def parse(proxy):
    """
    proxy is in format 'http(s)://XX.XX.XX.XX:port'
    :param proxy:
    :return:
    """
    try:
        p_type, ip, port = proxy.split(':')
    except:
        return []

    return p_type, ip[2:], port


def visit(url=None, proxy=None, timeout=6):
    """
    leave url blank for checking only
    http proxy can connect both http and https website
    https proxy can only connect https website
    :param url:
    :param proxy:
    :param timeout:
    :return:
    """
    if not url:
        # url = 'http://www.lagado.com/proxy-test'
        # url = 'https://www.sslproxies.org/'
        # url = 'https://www.baidu.com'
        url = 'https://www.google.com'

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
               'Referer': 'https://google.com'}
    if not proxy:
        return r.get(url, headers=headers)

    # p_info = proxy.split(':')
    # proxies = {'http': 'http:' + p_info[1] + p_info[2],
    #            'https': 'https:' + p_info[1] + p_info[2]}
    # print(proxies)
    proxies = {'http': proxy,
               'https': proxy}
    try:
        page = r.get(url, headers=headers, proxies=proxies, timeout=timeout, verify=False)
    except Exception as e:
        print(e)
        return None

    return page


def check_proxy(proxy):
    # print('\n------{}--------'.format(__name__))
    print('check {}'.format(proxy))
    res = visit(proxy=proxy, timeout=6)
    try:
        c = res.status_code
        if c == 200:
            print('proxy {} is good with status code {}'.format(proxy, c))
            return True
    except Exception as e:
        print(e)

    print('proxy {} is bad'.format(proxy))
    return False


def parse_fpl_page(response):
    """
    https://free-proxy-list.net/
    take proxies updated in 10 mins
    :param response:
    :return:
    """
    proxies = []
    if response is not None:
        soup = bs(response.content, 'lxml')
        for line in soup.select('tbody > tr'):
            tds = line('td')
            try:
                ip = tds[0].text
                port = tds[1].text
                p_type = 'https' if tds[-2].text == 'yes' else 'http'
                last_update = tds[7].text.strip()
            except:
                continue
            else:
                if ('minutes' in last_update) and (int(last_update.split(' ')[0]) > 9):
                    break
                else:
                    proxies.append('{}://{}:{}'.format(p_type, ip, port))
    return proxies


def pop_proxy(redis_cli):
    try:
        pro = redis_cli.zrange('spool', -1, -1, withscores=True)[0]
        print('{} updated {} secs ago'
              .format(pro[0], time.time()-pro[1]))
    except:
        print('cannot get a proxy')
        return None
    else:
        redis_cli.zrem('spool', pro[0])
        return pro[0]


def check_http(proxy):
    """
    check the proxy using:
    http://www.lagado.com/proxy-test
    :param proxy:
    :return:
    """
    url = 'http://www.lagado.com/proxy-test'
    try:
        res = visit(url, proxy=proxy, timeout=10)
        soup = bs(res.text, 'lxml')
        ip = soup.find(text=re.compile('address')).split(' ')[-1]
        print('{} identifies us as {}, proxy is {}'.format(url, ip, proxy))
        return soup
    except Exception as e:
        print(e)
        return None


def check_https(proxy):
    """
    'https://whatismyipaddress.com/'
    :param proxy:
    :return:
    """
    url = 'https://whatismyipaddress.com/'
    try:
        res = visit(url, proxy=proxy, timeout=10)
        soup = bs(res.text, 'lxml')
        ip = soup.find(id='section_left')('div')[1].text.strip()
        print('{} identifies us as {}, proxy is {}'.format(url, ip, proxy))
        return soup
    except Exception as e:
        print(e)
        return None



