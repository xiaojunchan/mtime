#-*- coding:utf-8 -*-

import os
import re
import time
import httplib
import urllib2
import urlparse
import logging
import chardet
import utils
from config import HEADERS, PING_STEP
from sinaimg import SinaImg

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


def movie_info():
    url = 'http://movie.mtime.com/150658/'
    #a = utils.get_resp_body(utils.get_socket_resp(url))
    #utils.save_text_file('150658.html', a)
    filename = '150658.html'
    filename = os.path.join(os.getcwd(), filename)
    with open(filename, 'r') as fh:
        data = fh.read()
    encoding = chardet.detect(data)['encoding']
    data = data.decode(encoding)

    ptn_name = ur'(?iu)px28 bold hei c_000"(?: property="v:itemreviewed")?>(.*?)</span>'
    regex = re.compile(ptn_name)
    name = regex.findall(data)[0]
    print name

    ptn_alias = ur'(?iu)ml9 px24">(.*?)</span>'
    regex = re.compile(ptn_alias)
    alias = regex.findall(data)[0]
    print alias

    ptn_rank = ur'(?iu)v:average">(.*?)</span>'
    regex = re.compile(ptn_rank)
    rank = regex.findall(data)[0]
    print rank

    ptn_cover_origin = ur'(?iu)src="(.*?)" class="movie_film_img fl"'
    regex = re.compile(ptn_cover_origin)
    cover_origin = regex.findall(data)[0]
    print cover_origin

    pr = urlparse.urlparse(cover_origin)
    filename = os.path.basename(pr.path)
    fn, fe = os.path.splitext(filename)
    cover_thumb = urlparse.urljoin(cover_origin, fn + '_180x270' + fe)
    print cover_thumb
    cover = urlparse.urljoin(cover_origin, fn + '_300x450' + fe)
    print cover
    
if __name__ == '__main__':
    movie_info()
    '''
    si = SinaImg()
    si.login()
    si.upload_batch([cover, cover_thumb])
    '''

    '''
    resp = ping('img31.mtime.cn', '/mt/518/136518/136518.jpg', method='GET')
    print dir(resp)
    print resp.status
    print resp.reason
    print resp.length
    print resp.length==3946
    '''

    '''
    resp = utils.get_socket_resp('http://img31.mtime.cn/mt/231/12231/12231_300x450.jpg')
    data = utils.get_resp_body(resp)
    utils.save_binary_file('111.jpg',data)
    '''

