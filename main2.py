import redis
import time
import utils
import threading
from multiprocessing.dummy import Pool
from datetime import datetime, timedelta

REFILL_KEY = 'refill'
REFILL_COUNTDOWN = 600
CHECK_INTERVAL = 1200  # proxy after this time will be considered obsolete and checked
LOWEST = 20

db = redis.StrictRedis(decode_responses=True)

vendors = {'free-proxy-list': 'https://free-proxy-list.net/',
           'sslproxies': 'https://www.sslproxies.org/'}


def robust_proxy_visit(url):
    """
    automatically pop a proxy to visit url
    if no proxy left, directly visit url
    :param url:
    :return:
    """
    page = None
    while not page:
        try:
            proxy = db.zrange('spool', -1, -1)[0]
        except:
            proxy = None
        # if not proxy:
        #     print('there is no proxy left, need to refill')
        page = utils.visit(url, proxy)
    if proxy:
        print('successfully visited {} via proxy {}, add it back'.format(url, proxy))
        db.zadd('spool', time.time(), proxy)
    else:
        print('directly visited {}'.format(url))
    return page, proxy


def refill():
    db.setex(REFILL_KEY, 7200, True)  # avoid refill process to act
    print('\n||||||||{}|||||||||'.format(refill.__name__))
    print('start filling in proxies')
    print('Fetching from https://free-proxy-list.net/')
    from_fpl()

    # add more sources

    print('(ﾉ>ω<)ﾉ finished refilling, setting refill count down to 600s')
    db.setex(REFILL_KEY, REFILL_COUNTDOWN, True)
    show_inventory()


def from_fpl():
    """
    https://free-proxy-list.net/
    :return:
    """
    url = 'https://free-proxy-list.net/'
    page, _ = robust_proxy_visit(url)

    p_list = utils.parse_fpl_page(page)
    deal_proxies(10, p_list)

    print('\n {}: exit. current number of proxies: {}'.format(from_fpl.__name__, db.zcard('spool')))


def deal_proxies(thread_count, proxy_list):
    """
    using thread_count threads to process a list of proxies
    :param thread_count:
    :param proxy_list:
    :return:
    """
    pool = Pool(thread_count)
    print('using {} threads to check {} proxies'.format(thread_count, len(proxy_list)))
    pool.map(deal_with_new_proxy, proxy_list)
    pool.close()
    pool.join()


def deal_with_new_proxy(proxy):
    print('\n(✪ω✪) {}: deal with {}'.format(threading.current_thread().getName(), proxy))
    if utils.check_proxy(proxy):
        db.zadd('spool', time.time(), proxy)
        print('ლ(╹◡╹ლ) {} is valid and added into database'.format(proxy))
    else:
        if db.zrem('spool', proxy) == 1:
            print('(〒︿〒) {} is removed from database'.format(proxy))


def refill_process():
    while True:
        while db.ttl(REFILL_KEY) > 0:
            time.sleep(min(db.ttl(REFILL_KEY), 600))  # avoid sleeping for too long

        print('\n\n***********refill process start************')
        p_count = db.zcard('spool')
        show_inventory()

        if p_count < LOWEST:
            refill()
        else:
            print('wait for {} secs to check refilling again'.format(REFILL_COUNTDOWN))
            db.setex(REFILL_KEY, REFILL_COUNTDOWN, True)
            print('***********refill process end************\n\n')


def refresh_process():
    check_sleep = CHECK_INTERVAL / 3
    while True:
        print('\n\n***********refresh process start************')
        try:
            oldest = db.zrange('spool', 0, 0, withscores=True)[0][1]
        except:
            print('seems no proxies left... fill up')
            db.delete(REFILL_KEY)
            refill_process()
            try:
                oldest = db.zrange('spool', 0, 0, withscores=True)[0][1]
            except:
                print('something goes wrong')
                return

        interval = time.time() - oldest
        if interval > CHECK_INTERVAL:
            print('(´ﾟдﾟ`) the oldest proxy is added {} ago'.format(timedelta(seconds=interval)))
            check_list = db.zrangebyscore('spool', oldest-1, time.time()-CHECK_INTERVAL+30)  # add range of 30s
            deal_proxies(4, check_list)
            print('\n ヽ(✿ﾟ▽ﾟ)ノ  finished refreshing, will check refreshing again after {} secs.'
                  .format(check_sleep))
            show_inventory()

        if db.zcard('spool') < LOWEST:
            print('(´ﾟдﾟ`) number of proxies is too low, force refilling...')
            refill()

        print('***********refresh process end************\n\n')
        time.sleep(check_sleep)


def show_inventory():
    pivot = time.time()
    try:
        oldest = db.zrange('spool', 0, 0, withscores=True)[0]
        newest = db.zrange('spool', -1, -1, withscores=True)[0]
        print('\n------------( ͡° ͜ʖ ͡°)------------\n'
              'There are {count} proxies.  {timestamp}\n'
              'The oldest is {op}, updated {opi} ago\n'
              'The newest is {np}, updated {npi} ago\n'
              '------------( ͡° ͜ʖ ͡°)------------\n'
              .format(count=db.zcard('spool'), timestamp=datetime.now(),
                      op=oldest[0], opi=timedelta(seconds=pivot-oldest[1]),
                      np=newest[0], npi=timedelta(seconds=pivot-newest[1])))
    except:
        pass


def visit_trigger(url):
    """
    robust visit and if no proxies left,
    trigger refill process
    :param url:
    :return:
    """
    page, proxy = robust_proxy_visit(url)
    if not proxy:
        print('depletion of proxies, refill...')
        refill()


if __name__ == '__main__':
    db.delete(REFILL_KEY)

    refill_thread = threading.Thread(target=refill_process)
    refill_thread.setDaemon(True)
    refill_thread.start()

    refresh_thread = threading.Thread(target=refresh_process)
    refresh_thread.setDaemon(True)
    refresh_thread.start()

    while True:
        if not refill_thread.is_alive():
            print('\n\n(ﾒ ﾟ皿ﾟ)ﾒ\n refill thread is down!')
            refill_thread.start()
        if not refill_thread.is_alive():
            print('\n\n(ﾒ ﾟ皿ﾟ)ﾒ\n refresh thread is down!')
            refill_thread.start()
        time.sleep(60)





