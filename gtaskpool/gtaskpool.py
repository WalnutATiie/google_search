#!/usr/bin/env python
# encoding: utf-8

import sys
if 'threading' in sys.modules:
    raise Exception('threading module loaded before patching!')

from gevent import monkey
monkey.patch_all()

import gevent
import gevent.pool

import logging

class Task(object):
    def __init__(self, func, args=None):
        if not hasattr(func, '__call__') or \
                not (args is None or type(args) is list):
            raise Exception("Arguments of gtaskpool.Task are (func[, args_list])")
        self.func = func
        self.args = args

    def print_friendly_args(self):
        return [x.__name__+"[func]" if hasattr(x, '__call__') else str(x) \
                for x in self.args]

def setlogging(level,task_log):
    logging.basicConfig(format="%(asctime)s %(levelname)s - %(message)s", level=level,filename=task_log,filemode='w')

def runtasks(task_generator, max_ongoing_tasks=1000):
    taskpool = gevent.pool.Pool(size=max_ongoing_tasks)
    tidx = 0
    while True:
        try:
            task = task_generator.next()
        except StopIteration:
            logging.info("gtaskpool: Tasks exausted.")
            break
        if task.args is None:
            g = gevent.Greenlet(task.func)
        else:
            g = gevent.Greenlet(task.func, *task.args)
        logging.info("gtaskpool: starting task %s", task.func.__name__)
        taskpool.start(g)

        if (tidx+1)%100 == 0:
            gevent.sleep(0)
        tidx += 1

    taskpool.join()
    logging.info("gtaskpool: Tasks finished.")
