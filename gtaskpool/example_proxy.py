#!/usr/bin/env python
# encoding: utf-8

import gtaskpool
from proxymanager.downloadproxylist import get_http_proxies
from proxymanager.downloadualist import get_useragents
from proxymanager.proxymanager import ProxyManager

import gevent
import requests

import random
import logging


def task_retry(url):
    (try_cnt, finish) = (0, False)
    while not (finish or try_cnt >= 10):
        finish = task(url, try_cnt+1)
        try_cnt += 1
    if not finish:
        fleft.write("%s\n" % url)
        fleft.flush()
    logging.info("task_retry(%s): finished", url)

def task(url, try_idx):
    logging.info("task(%s, try=%s): called", url, try_idx)
    proxy = proxymgr.next_proxy(url).proxy
    proxies = {'http': proxy, 'https': proxy}
    headers = {'User-Agent': useragents[random.randint(0, len(useragents)-1)]}
    try:
        with gevent.Timeout(40, Exception("gevent-timeout: %d seconds" % 40)):
            r = requests.get(url, headers=headers, proxies=proxies, timeout=20)
        r.encoding = 'utf-8'
    except Exception, e:
        proxymgr.feedback(proxy, False)
        logging.error("task(%s, %s) - %s" % (url, try_idx, e))
        return False
    else:
        proxymgr.feedback(proxy, True)
        rtext = r.text.encode('utf-8')
        fresult.write("task(%s) - response(len=%s): %s\n" % (url, len(r.text), \
                rtext[:min(400, len(rtext))].replace("\r","").replace("\n","")))
        fresult.flush()
        return True


def task_generator():
    base_url = 'http://www.baidu.com/s?wd=apple&pn='
    task_num = 300
    for i in xrange(task_num):
        yield gtaskpool.Task(task_retry, [base_url+str(i*10)])


if __name__ == "__main__":
    gtaskpool.setlogging(logging.INFO)

    purl1 = ["http://192.168.120.17:8014/proxy/get_http_proxy_list"]
    purl2 = ["http://192.168.1.14:5500/get_http_proxy_list"]
    uurl1 = "http://192.168.120.17:8014/proxy/get_useragent_list"
    uurl2 = "http://192.168.1.14:5500/get_useragent_list"

    # Create a ProxyManager if you need
    limited_urls = [
        ('^http://www\.baidu\.com/s\?wd=apple&pn=\d+$', 1)
    ]
    proxymgr = ProxyManager(get_http_proxies, limited_urls, \
            {'refresh': True, 'interval': 30*60, 'delay': 8*60}, *purl2)
    # Or if you don't want refresh proxies periodcally
    #proxymgr = ProxyManager(get_http_proxies, *purl2, limited_urls, \
    #        {'refresh': False}, *purl2)

    # A useragent list for http request if you need
    useragents = get_useragents(uurl2)
    if useragents == []: useragents = [None]

    fresult = open("result.txt", 'w')
    fleft = open("left.txt", 'w')

    # Optional args:
    #   @max_ongoing_tasks (default to 1000)
    gtaskpool.runtasks(task_generator())

    fresult.close()
    fleft.close()



