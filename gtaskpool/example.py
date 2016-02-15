#!/usr/bin/env python
# encoding: utf-8

import gtaskpool

import requests

import logging

def task(n1, n2):
    logging.info("task(%s, %s): called", n1, n2)
    r = requests.get("http://www.baidu.com")
    print "task(%s, %s): response (len=%s): %s..." % \
            (n1, n2, len(r.text), r.text[:min(100, len(r.text))])
    logging.info("task(%s, %s): finished", n1, n2)


def task_generator():
    task_num = 10
    for i in xrange(1, task_num+1):
        yield gtaskpool.Task(task, [i, i])

if __name__ == "__main__":
    gtaskpool.setlogging(logging.INFO)
    gtaskpool.runtasks(task_generator())
