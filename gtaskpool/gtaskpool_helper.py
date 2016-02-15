#!/usr/env python
# encoding: utf-8

import gtaskpool

import random
from datetime import datetime
import json

class Interface(object):
    def __init__(self, get_proxy, proxy_feedback, get_useragent):
        self.get_proxy = get_proxy
        self.proxy_feedback = proxy_feedback
        self.get_useragent = get_useragent

def get_useragent_wrapper(useragents):
    def get_useragent():
        if len(useragents) == 0:
            return None
        idx = random.randint(0, len(useragents)-1)
        return useragents[idx]
    return get_useragent

def get_proxy_wrapper(next_proxy):
    def get_proxy(url):
        return next_proxy(url).proxy
    return get_proxy

def get_interfaces(proxymgr, useragents):
    return Interface(
            get_proxy = get_proxy_wrapper(proxymgr.next_proxy), 
            proxy_feedback = proxymgr.feedback,
            get_useragent = get_useragent_wrapper(useragents))


def retry_task(task, task_log, max_try):
    trycnt = 0
    while trycnt != max_try:
        res = task()
        res['try_idx'] = trycnt + 1
        if trycnt+1 == max_try or res['finish']:
            res['last_try'] = True
        else:
            res['last_try'] = False
            
        log_task_result(res, task_log)
        if res['finish']:
            return
        trycnt += 1

def log_task_result(result, filehandle):
    result['ts'] = str(datetime.now())
    jstr = json.dumps(result, ensure_ascii=False).encode('utf-8')
    filehandle.write(jstr + "\n")

def runtasks(task_generator, task_log, max_try=10):
    def gen_task():
        while True:
            try:
                task = task_generator.next()
            except StopIteration, e:
                return
            yield gtaskpool.Task(retry_task, [task, task_log, max_try])

    gtaskpool.runtasks(gen_task())


