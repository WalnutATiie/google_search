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
import re
import random
import types
import os
from dependency.search_result import SearchResult


class GoogleSearch:

    def __init__(self):
        self.results_per_page = 10
        self.results_num = 500
        self.search_mirror_site_num = 10
        self.base_urls = None
        self.keywords_num = 0

    def get_results_num(self):
        return self.results_num

    def get_keywords_num(self):
        return self.keywords_num

    def get_results_per_page(self):
        return self.results_per_page

    @staticmethod
    def get_mirror_site(self):
        '''
        Get google mirror sites from file. This function is used to
        fight against google's anti-crawler.
        '''
        mirror_sites = list()
        try:
            site_file = open('./resourcefile/mirror_sites.txt', 'rb')
            for line in site_file:
                mirror_sites.append(line.strip('\n'))
            site_file.close()
        except IOError as e:
            logging.error('file error:%s', e)
        finally:
            return (mirror_sites, len(mirror_sites))

    @staticmethod
    def get_base_urls(self):
        '''
        Get base_urls.Every time we choose N mirror sites arbitrarily
        to make sure that we can get enough search results.

        $search_mirror_site_num: number of mirror sites to be used.
        '''
        base_urls = list()
        (total_base_urls, num_of_base_url) = self.get_mirror_site(self)
        try:
            self.search_mirror_site_num > 0
        except AssertionError:
            logging.error(
                'Parameter search_mirror_site_num error.Program Aborted')
            sys.exit()
        try:
            assert num_of_base_url > 0
        except AssertionError:
            logging.error('Fail to get base_urls.Program Aborted.')
            sys.exit()
        else:
            for i in xrange(self.search_mirror_site_num):
                base_urls.append(
                    total_base_urls[
                        random.randint(
                            0, num_of_base_url - 1)])
            raw_sites = [
                'https://www.google.ca/'
               ]
            base_urls.append(raw_sites[random.randint(0, len(raw_sites) - 1)])
            return base_urls

    def extractDomain(self, url):
        '''
        The funciton is designed to extract Domain from the RAW html code
        '''
        domain = ''
        pattern = re.compile(r'http[s]?://([^/]+)/', re.U | re.M)
        url_match = pattern.search(url)
        if(url_match and url_match.lastindex > 0):
            domain = url_match.group(1)

        return domain

    @staticmethod
    def extractUrl(self, href):
        '''
        The funciton is designed to extract url from the RAW html code
        '''
        url = ''
        pattern = re.compile(r'(http[s]?://[^&]+)&', re.U | re.M)
        url_match = pattern.search(href)
        if(url_match and url_match.lastindex > 0):
            url = url_match.group(1)

        return url

    @staticmethod
    def extractSearchResults(self, html):
        '''
        The funciton is designed to extract every search result from the
        RAW html code
        '''
        results = list()
        soup = BeautifulSoup(html)
        div = soup.find('div', id='search')
        if (not isinstance(div, types.NoneType)):
            lis = div.findAll('li', {'class': 'g'})
            if(len(lis) > 0):
                for li in lis:
                    result = SearchResult()
                    h3 = li.find('h3', {'class': 'r'})
                    if(isinstance(h3, types.NoneType)):
                        continue
                    link = h3.find('a')
                    if (isinstance(link, types.NoneType)):
                        continue
                    url = link['href']
                    url = self.extractUrl(self, url)
                    if(cmp(url, '') == 0):
                        continue
                    title = link.renderContents()
                    result.setURL(url)
                    result.setTitle(title)

                    span = li.find('span', {'class': 'st'})
                    if (not isinstance(span, types.NoneType)):
                        content = span.renderContents()
                        result.setContent(content)
                    results.append(result)
        return results

    @staticmethod
    def get_search_keywords(self):
        '''
        Get search keywords from file:keywords_google.txt
        '''
        keywords = list()
        try:
            search_file = open('./resourcefile/keywords_google.txt', 'r')
            for line in search_file:
                keywords.append(line.strip('\n'))
            self.keywords_num = len(keywords)
            search_file.close()
        except IOError as e:
            logging.error('file error:%s', e)
        finally:
            return keywords

    @staticmethod
    def url_generator(self, base_url, query, num, lang='en'):
        '''
        To generate the url request by the number of pages.
        '''
        try:
            assert num > 0 and self.results_per_page > 0
        except AssertionError:
            logging.error(
                'Parameter error,please check the parameters.Program Aborted')
            sys.exit()
        else:
            query = urllib2.quote(query)
            urls = list()
            if(num % self.results_per_page == 0):
                pages = num / self.results_per_page
            else:
                pages = num / self.results_per_page + 1
            for p in range(0, pages):
                start = p * self.results_per_page
                url = '%ssearch?hl=en&num=%d&start=%s&q=%s&filter=0' % (
                    base_url, self.results_per_page, start, query)
                urls.append(url)
            return urls

    '''
    A single Gevent task.
    '''
    @staticmethod
    def task(self, url):
        try_idx = 0
        search_results = list()
        logging.info("task(%s, try=%s): called", url, try_idx)
        proxy = proxymgr.next_proxy(url).proxy
        proxies = {'http': proxy, 'https': proxy}
        headers = {
            'User-Agent': useragents[random.randint(0, len(useragents) - 1)]}
        try:
            with gevent.Timeout(300, Exception("gevent-timeout: %d seconds" % 300)):
                opener = urllib2.build_opener(urllib2.ProxyHandler(
                    {'http': proxy}), urllib2.HTTPHandler(debuglevel=1))
                urllib2.install_opener(opener)  # add exception here
                request = urllib2.Request(url)
                request.add_header(
                    'User-Agent',
                    useragents[
                        random.randint(
                            0,
                            len(useragents) -
                            1)])
                request.add_header('connection', 'keep-alive')
                request.add_header('Accept-Encoding', 'gzip')
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
            results = self.extractSearchResults(self, html)
            search_results.extend(results)
            save_file = "results_google/" + \
                url.split('&')[3].split('=')[1] + "_" + \
                url.split('&')[2].split('=')[1] + ".json"
            try:
                assert os.path.exists("results_google") == True
            except AssertionError:
                os.makedirs("results_google")
            for r in search_results:
                r.writeFile_json(save_file)
            return True

    '''
    Task Generator.Every keyword,base_url and page generates one gevent task.
    '''
    @staticmethod
    def task_generator(self):
        keywords = self.get_search_keywords(self)
        try:
            assert len(keywords) > 0
        except AssertionError:
            logging.error('Fail to get keywords.Program Aborted.')
            sys.exit()
        else:
            base_urls = self.get_base_urls(self)
            for keyword in keywords:
                for base_url in base_urls:
                    search_urls = self.url_generator(
                        self, base_url, keyword, self.results_num, lang='en')
                    for search_url in search_urls:
                        yield gtaskpool.Task(self.task, [self, search_url])

    def gtaskmanager(self):
        task_log = None
        gtaskpool.setlogging(logging.INFO,task_log)
        purl1 = ["http://192.168.120.185:5500/get_google_http_proxy_list"]
        uurl1 = "http://192.168.120.17:8014/proxy/get_useragent_list"
        limited_urls = [
            ('^https{0,1}://', 1)
        ]
        global proxymgr
        proxymgr = ProxyManager(get_http_proxies, limited_urls,
                                {'refresh': True, 'interval': 30 * 60, 'delay': 8 * 60}, *purl1)
        global useragents
        useragents = get_useragents(uurl1)
        if useragents == []:
            useragents = [None]
        gtaskpool.runtasks(self.task_generator(self))
if __name__ == "__main__":

    G = GoogleSearch()
    G.gtaskmanager()
