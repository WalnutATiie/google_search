#!/usr/bin/env python
# encoding: utf-8

import requests

import json
import logging

def getproxylist():
    r = requests.get("http://192.168.120.17:8014/proxy/getproxylist")
    return json.loads(r.text)

def get_http_proxy_list(url="http://192.168.120.17:8014/proxy/get_http_proxy_list"):
    logging.info("get_http_proxy_list(%s): downloading proxies...", url)
    r = requests.get(url)
    return json.loads(r.text)

def get_http_proxies(url="http://192.168.120.17:8014/proxy/get_http_proxy_list"):
        res = get_http_proxy_list(url)
        if res['ret'] != 'ok':
            raise Exception("get_http_proxies() failed: %s" % res)
        logging.info("get_http_proxies(): got %s proxies", len(res['proxies']))
        return res['proxies']

def get_socks_proxy_list():
    r = requests.get("http://192.168.120.17:8014/proxy/get_socks_proxy_list")
    return json.loads(r.text)

if __name__ == "__main__":
    print json.dumps(getproxylist(), indent=2)
    print json.dumps(get_http_proxy_list(), indent=2)
    print json.dumps(get_socks_proxy_list(), indent=2)

