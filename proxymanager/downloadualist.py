#!/usr/bin/env python
# encoding: utf-8

import requests

import json
import logging

def getualist(url="http://192.168.120.17:8014/proxy/get_useragent_list"):
    logging.info("getualist(%s): downloading useragents...", url)
    r = requests.get(url)
    return json.loads(r.text)

def get_useragents(url="http://192.168.120.17:8014/proxy/get_useragent_list"):
    res = getualist(url)
    if res['ret'] != 'ok':
        raise Exception("get_useragents(): failed: %s" % res)
    logging.info("get_useragents(): got %s useragents", len(res['agents']))
    return res['agents']


if __name__ == "__main__":
    print json.dumps(getualist(), indent=2)

