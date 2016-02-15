#!/usr/bin/env python
# encoding: utf-8

from proxymanager import ProxyManager

import gevent

import logging

if __name__ == "__main__":
    LOG_FORMAT = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG)

    # ==This is what you need to construct a ProxyManager==
    proxies = [
        'http://1.1.1.1:80',
        'http://2.2.2.2:80',
        'http://3.3.3.3:80',
        'socks5://4.4.4.4:80']
    # limited_url without prefix 'http://' or 'https://' means
    # there is no difference regarding access rate control
    # between the two.
    limited_urls = [
        ('^https{0,1}://www\.baidu\.com/link', 2),
        ('^https{0,1}://www\.baidu\.com/test', 2),
        ('^https{0,1}://www\.baidu\.com(?!/link|/test)', 2),
        ('^http://www\.csdn\.com', 2)]
    proxymgr = ProxyManager(proxies, limited_urls)
    # ==End==

    # The following performs 20 concurrent tasks
    # that each requests a proxy from $proxymgr
    # to visit a url in $domains
    domain1 = "http://www.baidu.com/test"
    domain2 = "http://www.baidu.com/link"
    domain3 = "http://www.baidu.com"
    domain4 = "http://www.baidu.com/hello"
    domain5 = "https://www.csdn.com"
    domains = [domain1, domain2, domain1, domain1,
               domain1, domain2, domain3, domain2,
               domain2, domain2, domain2, domain2,
               domain2, domain2, domain4, domain3,
               domain1, domain1, domain1, domain2,
               domain5, domain3, domain3, domain4]

    def request_proxy(proxymgr, url):
        # This is how you get a $proxy from $proxymgr
        # $proxy has 3 member variable i.e. 
        #   proxy.proxy(=proxy.type+'://'+proxy.ip+':'+proxy.port)
        #   proxy.type(=http, https, socks4, socks5), 
        #   proxy.ip(='xx.xx.xx.xx'),
        #   proxy.port(=1234)
        # $proxymgr.next_proxy(url) could block due to
        # access rate control that is specified in $limited_urls
        proxy = proxymgr.next_proxy(url)
        logging.debug('%s -> %s', url, proxy.proxy)

    gs = [gevent.spawn(request_proxy, proxymgr, url) for url in domains]
    gevent.joinall(gs)
