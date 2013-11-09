#-*- coding:utf-8 -*-

import os
import time
import httplib
import urllib2
import logging
from config import HEADERS, PING_STEP

try:
    import cPickle as pickle
except:
    import pickle


def get_logger(logger_name):
    format_string = '%(asctime)s %(levelname)5s %(message)s'
    level = logging.DEBUG
    logging.basicConfig(format=format_string, level=level)
    logger = logging.getLogger(logger_name)
    return logger

L = get_logger(__name__)


def ping(host, path, method='HEAD', headers=HEADERS):
    try:
        conn = httplib.HTTPConnection(host)
        conn.request(method, path, headers=headers)
        res = conn.getresponse()
        return res
    except StandardError:
        return None


def start_ping(start=10001):
    ids = {}
    ids_error = {}
    host = 'movie.mtime.com'
    path = '/%d/'
    for x in xrange(start, start + PING_STEP):
        res = ping(host, path % (x))
        if res:
            L.debug('%s/%d/ %d' % (host, x, res.status))
        if res and res.status == 200:
            ids[x] = {}
        if res and (not res.status == 200):
            ids_error[x] = {}
    filename = repr(start) + '_' + repr(x)
    if ids:
        save_res(data=ids, filename=filename)
    if ids_error:
        save_res(data=ids_error, filename=filename, stuff='.error')


def save_res(data, filename=None, stuff='.stp1'):
    if not filename:
        filename = repr(time.time())[:-3]
    path_save = os.path.join(os.getcwd(), 'res_mtime')
    if not os.path.exists(path_save):
        os.makedirs(path_save)
    filename = os.path.join(path_save, filename + stuff)
    with open(filename, 'wb') as fh:
        pickle.dump(data, fh)


def load_res(path):
    with open(path, 'rb') as fh:
        return pickle.load(fh)


def view_res(error=False):
    res = {}
    import glob
    stuff = '*.stp1'
    if error:
        stuff = '*.error'
    path = os.path.join(os.getcwd(), 'res_mtime', stuff)
    files = glob.glob(path)
    for x in files:
        res.update(load_res(x))
    L.debug('getsource: %d' % (len(res),))
    return res


def deal_res():
    res = view_res()
    res_min = dict(res.items())

    import collections
    od = collections.OrderedDict(sorted(res_min.items()))
    ok_res = dict(od.items())
    filename = os.path.join(os.getcwd(), 'res_mtime', 'res.ok')
    with open(filename, 'wb') as fh:
        pickle.dump(ok_res, fh)


def time_deal_res():
    stime = time.time()
    deal_res()
    print time.time() - stime, 'seconds'

if __name__ == '__main__':
    from database import initDB
    initDB()
