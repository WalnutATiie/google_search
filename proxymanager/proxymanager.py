#!/usr/bin/env python
# encoding: utf-8

from gevent import monkey
monkey.patch_all()

import gevent
import gevent.queue

import random
import time
import re
from datetime import datetime, timedelta
import logging
import json

class Proxy(object):
    def __init__(self, proxy, ts=0):
        self.proxy = proxy
        self.ts = ts
        self.type = self.ip = self.port = None
        if proxy:
            self.type = proxy.split("://")[0]
            (self.ip, self.port) = proxy.split("://")[1].split(":")
    def __lt__(self, ipentry2):
        return self.ts < ipentry2.ts
    def __repr__(self):
        return "Proxy('%s', '%s', '%s', %s)" % (self.type, self.ip, self.port, self.ts)

class ProxyStat(object):
    def __init__(self, usecount, failcount):
        self.usecount = usecount
        self.failcount = failcount

    def failratio(self):
        if self.usecount < 8:
            return 0
        else:
            return float(self.failcount)/self.usecount

    def usefeedback(self, ok):
        self.usecount += 1
        if not ok:
            self.failcount += 1

class ProxyPool(object):
    def __init__(self, url_pattern, avg_interval, init_proxy_list):
        self.gen_interval = lambda: random.uniform(avg_interval*(2.0/3), avg_interval*(4.0/3))
        self.url_pattern = re.compile(url_pattern)
        self.proxy_pq = gevent.queue.PriorityQueue()
        for proxy in init_proxy_list:
            self.proxy_pq.put_nowait(proxy)


def greenlet_wrapper(f):
    def inner(*args, **kwargs):
       return gevent.spawn(f, *args, **kwargs)
    return inner

class ProxyManager(object):
    def __init__(self, get_proxies, limited_url_patterns, refreshproxy, *get_proxies_args):
        '''@get_proxies -> func that returns a list of proxys
                in format like"http://xx.xx.xx.xx:xxxx"
           @limited_urls -> [(url, avg_interval), ...]
           @refreshproxy -> {'refresh': True|False, 'interval': 1800, 'delay':480}
                'interval', 'delay' are of unit second
        '''
        if 'refresh' not in refreshproxy \
                or 'interval' not in refreshproxy or 'delay' not in refreshproxy \
                or refreshproxy['delay'] >= refreshproxy['interval'] \
                or (60*60)%refreshproxy['interval'] != 0:
            raise Exception("ProxyManager() constructor: refreshproxy should contain "\
                    + "'refresh', 'interval' and 'delay', and 'interval' should be greater "\
                    + "'delay', and 'interval' should be diveded by 60*60")

        self.get_proxies = get_proxies
        self.get_proxies_args = get_proxies_args
        self.limited_url_patterns = limited_url_patterns
        self.url_proxypools = {}
        self.proxy_stats = {}
        self.first_time_set_proxies = True

        self.setproxies(refreshproxy)

    def setproxies(self, refreshproxy):
        logging.info("ProxyManager.setproxies(): refresh proxies")
        if not self.first_time_set_proxies:
            logging.info("ProxyManager.proxy_stats: %s", json.dumps(self.proxy_stats, default=lambda o: o.__dict__))
        try:
            proxies = self.get_proxies(*self.get_proxies_args)
        except Exception, e:
            logging.error("ProxyManager.setproxies(): get_proxies(%s) failed, set with empty proxies list: %s", self.get_proxies_args, e)
            if self.first_time_set_proxies:
                self.set_proxies_state([])
        else:
            self.set_proxies_state(proxies)

        if refreshproxy['refresh']:
            c = datetime.now()
            start = 0
            while start+refreshproxy['delay'] <= c.minute*60+c.second:
                start += refreshproxy['interval']
            if start == 60*60:
                nexttime = datetime(year=c.year, month=c.month, day=c.day, hour=c.hour) \
                        + timedelta(seconds=60*60) + timedelta(seconds=refreshproxy['delay'])
            else:
                nexttime = datetime(year=c.year, month=c.month, day=c.day, hour=c.hour, \
                        minute=start/60, second=start%60) + timedelta(seconds=refreshproxy['delay'])

            loop = gevent.core.loop(default=True)
            deltatime = nexttime-c
            timer = loop.timer(deltatime.seconds+float(deltatime.microseconds)/1000000)
            timer.start(greenlet_wrapper(self.setproxies), refreshproxy)
            logging.info("ProxyManager.setproxies(): next proxy refreshing at %s...", nexttime)

    def set_proxies_state(self, proxies):
        logging.info("ProxyManager.set_proxies_state()")
        self.url_proxypools = {}
        self.proxy_stats = {}

        now = time.time()
        for (url_pattern, avg_interval) in self.limited_url_patterns:
            proxylist = [Proxy(proxy=proxy, ts=now) for proxy in set(proxies)]
            proxylist.append(Proxy(proxy=None, ts=now)) # Add no-proxy as a proxy

            proxypool = ProxyPool(url_pattern, avg_interval, proxylist)
            self.url_proxypools[url_pattern] = proxypool
        logging.debug("ProxyManager.url_proxypools.keys(): %s", self.url_proxypools.keys())

        for proxy in set(proxies):
            self.proxy_stats[proxy] = ProxyStat(0, 0)
        self.proxy_stats[None] = ProxyStat(0, 0)

        if self.first_time_set_proxies:
            self.first_time_set_proxies = False

    def is_limited_url(self, url):
        for url_pattern,proxypool in self.url_proxypools.iteritems():
            if proxypool.url_pattern.match(url):
                return (True, url_pattern)
        return (False, None)

    def feedback(self, proxy, ok):
        if proxy in self.proxy_stats:
            self.proxy_stats[proxy].usefeedback(ok)
        else:
            logging.warning("ProxyManager.feedback(%s, %s) proxy not in stats", proxy, ok)

    def next_proxy(self, url):
        now = time.time()
        (limited, limurl) = self.is_limited_url(url)
        if limited:
            proxypool = self.url_proxypools[limurl]

            randcnt = 0
            while True:
                proxy = proxypool.proxy_pq.get_nowait()
                pstat = self.proxy_stats[proxy.proxy]
                if randcnt >= 100 or random.random() < 1-pstat.failratio():
                    break
                successor = Proxy(proxy.proxy, max(proxy.ts, now)+proxypool.gen_interval())
                proxypool.proxy_pq.put_nowait(successor)
                randcnt += 1
            logging.debug('url %s choose proxy: %s after %s times random', url, proxy, randcnt)
            if randcnt == 100:
                logging.warning("ProxyManager.next_proxy() random cnt exceeds 100")

            nextproxy = Proxy(proxy.proxy, 0)
            waittime = proxy.ts - now

            successor = Proxy(proxy.proxy, max(proxy.ts, now)+proxypool.gen_interval())
            proxypool.proxy_pq.put_nowait(successor)
            logging.debug('url %s add successor: %s', url, successor)
        else:
            # Do your things without a proxy
            nextproxy = Proxy(None, 0)
            waittime = 0

        if waittime > 0:
           gevent.sleep(waittime)
        return nextproxy

