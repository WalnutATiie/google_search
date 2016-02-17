#!/usr/bin/env python
# encoding: utf-8
import gtaskpool
from proxymanager.downloadproxylist import get_http_proxies
from proxymanager.downloadualist import get_useragents
from proxymanager.proxymanager import ProxyManager
from bs4 import BeautifulSoup
import logging
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import gevent
import urllib2
import gzip
import StringIO
import random
import os
from dependency.bloom_filter import BloomFilter
from dependency.search_result import SearchResult


class BingSearch:

    def __init__(self):
        self.BASE_URL = 'https://search.disconnect.me/'
        self.RESULTS_PER_PAGE = 10
        self.RESULTS_NUM = 500
        self.KEYWORDS_NUM = 0

    def get_KEYWORDS_NUM(self):
        return self.KEYWORDS_NUM

    def get_RESULTS_NUM(self):
        return self.RESULTS_NUM

    def get_RESULTS_PER_PAGE(self):
        return self.RESULTS_PER_PAGE

    @staticmethod
    def extractSearchResults(self, html, url):
        search_results = list()
        soup = BeautifulSoup(html)
        try:
            ul = soup.find_all('ul',id='normal-results')
            lis = ul[0].find_all('li')
        except:
            logging_error("fail to extract the page:%s", url)
        else:
            for li in lis:
                search_result = SearchResult()
                search_result.setURL(li.find('a')['href'])
                search_result.setContent(li.find('p').text)
                search_result.setTitle(li.find('a').text)
                if bloom_filter.is_not_contained(search_result.getURL()):
                    bloom_filter.bf_add(search_result.getURL())
                    search_results.append(search_result)
            return search_results

    @staticmethod
    def get_search_keywords(self):
        keywords = list()
        try:
            search_file = open('./resourcefile/keywords_google.txt', 'r')
            for line in search_file:
                keywords.append(line.strip('\n'))
            self.KEYWORDS_NUM = len(keywords)
            search_file.close()
        except IOError as e:
            logging.error('file error:%s', e)
        finally:
            return keywords

    @staticmethod
    def url_google_generator(self, query, num):
        try:
            assert num > 0 and self.RESULTS_PER_PAGE > 0
        except AssertionError:
            logging.error(
                'Parameter error,please check the parameters.Program Aborted')
            sys.exit()
        else:
            query = urllib2.quote(query)
            urls = list()
            if(num % self.RESULTS_PER_PAGE == 0):
                pages = num / self.RESULTS_PER_PAGE
            else:
                pages = num / self.RESULTS_PER_PAGE + 1
            for p in range(0, pages):
                first = p * self.RESULTS_PER_PAGE 
                url = 'https://search.disconnect.me/searchTerms/search?start=nav&option=Web&query='+query+'&ses=Google&location_option=US&nextDDG=%2Fsearch%3Fq%3D%26hl%3Den%26start%3D'+str(first)+'%26sa%3DN&showIcons=false&filterIcons=none&js_enabled=1&source=None'
                urls.append(url)
            return urls
    
    @staticmethod
    def url_bing_generator(self, query, num):
        try:
            assert num > 0 and self.RESULTS_PER_PAGE > 0
        except AssertionError:
            logging.error(
                'Parameter error,please check the parameters.Program Aborted')
            sys.exit()
        else:
            query = urllib2.quote(query)
            urls = list()
            if(num % self.RESULTS_PER_PAGE == 0):
                pages = num / self.RESULTS_PER_PAGE
            else:
                pages = num / self.RESULTS_PER_PAGE + 1
            for p in range(0, pages):
                first = p * self.RESULTS_PER_PAGE+1 
                url = 'https://search.disconnect.me/searchTerms/search?start=nav&option=Web&query='+query+'&ses=Bing&location_option=US&nextDDG=%2Fsearch%3Fq%3D'+query+'%26setmkt%3Den-US%26setplang%3Den-us%26setlang%3Den-us%26first%3D'+str(first)+'%26FORM%3DPERE&showIcons=false&filterIcons=none&js_enabled=1&source=None'
                urls.append(url)
            return urls

    @staticmethod
    def task(self, url,engine_type):
        try_idx = 0
        search_results = list()
        logging.info("task(%s, try=%s): called", url, try_idx)
        proxy = proxymgr.next_proxy(url).proxy
        print proxy
        try:
            with gevent.Timeout(100, Exception("gevent-timeout: %d seconds" % 100)):
                opener = urllib2.build_opener(urllib2.ProxyHandler(
                    {'http': proxy}), urllib2.HTTPHandler(debuglevel=1))
                urllib2.install_opener(opener)  # add exception here
                request = urllib2.Request(url)
                ua = useragents[random.randint(0,len(useragents)-1)]
                #ua =useragents[19]
                request.add_header(
                    'User-Agent',ua
                            )
                logging.info("task(%s):%s",url,proxy)
                request.add_header('connection', 'keep-alive')
                request.add_header('Accept-Encoding', 'gzip')
                request.add_header('referer', self.BASE_URL)
                response = urllib2.urlopen(request)
                html = response.read()
        except Exception as e:
            proxymgr.feedback(proxy, False)
            logging.error("task(%s, %s) - %s" % (url, try_idx, e))
            return False
        else:
            proxymgr.feedback(proxy, True)
            if(response.headers.get('content-encoding', None) == 'gzip'):
                html = gzip.GzipFile(fileobj=StringIO.StringIO(html)).read()
            results = self.extractSearchResults(self, html, url)
            search_results.extend(results)
            if engine_type =='google':
                save_file = "results_disconnect/" + \
                    engine_type+"_"+url.split('?')[1].split('&')[2].split('=')[1] + "_" + url.split('%')[7] + ".json"
            if engine_type == 'bing':
                save_file = "results_disconnect/" + \
                    engine_type+"_"+url.split('?')[1].split('&')[2].split('=')[1] + "_" + url.split('%')[11] + ".json"
            try:
                assert os.path.exists("results_disconnect") == True
            except AssertionError:
                os.makedirs("results_disconnect")
            for r in search_results:
                r.writeFile_json(save_file)
            return True

    @staticmethod
    def task_generator(self,engine_type):
        keywords = self.get_search_keywords(self)
        try:
            assert len(keywords) > 0
        except AssertionError:
            logging.error('Fail to get keywords.Program Aborted.')
            sys.exit()
        else:
            global bloom_filter
            bloom_filter = BloomFilter(
                (self.RESULTS_NUM + 1) * self.RESULTS_NUM, 0.01)
            for keyword in keywords:
                if engine_type == 'google':
                    search_urls = self.url_google_generator(
                        self, keyword, self.RESULTS_NUM)
                if engine_type == 'bing':
                    search_urls = self.url_bing_generator(
                        self, keyword, self.RESULTS_NUM)
                for search_url in search_urls:
                    yield gtaskpool.Task(self.task, [self, search_url,engine_type])

    def gtaskmanager(self,engine_type):
        #task_log = 'task_log.log'
        task_log = None
        gtaskpool.setlogging(logging.INFO,task_log)
        purl1 = ["http://192.168.120.185:5500/get_google_http_proxy_list"]
        uurl1 = "http://192.168.120.17:8014/proxy/get_useragent_list"
        limited_urls = [
            ('^https://search\.disconnect\.me', 1)
        ]
        global proxymgr

        proxymgr = ProxyManager(get_http_proxies, limited_urls,
                                {'refresh': True, 'interval': 30 * 60, 'delay': 8 * 60}, *purl1)
        global useragents
        useragents = get_useragents(uurl1)
        if useragents == []:
            useragents = [None]

        gtaskpool.runtasks(self.task_generator(self,engine_type))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.stderr.write("Usage: ./batch_socks.py create|run|stop [args]\n") 
        exit(1)
    engine_type = sys.argv[1]
    if engine_type == 'google':
        pass
    elif engine_type == 'bing':
        pass
    else:
        sys.stderr.write("Usage: python disconnect_search.py google|bing\n")
        exit(1)
    B = BingSearch()
    B.gtaskmanager(engine_type)
