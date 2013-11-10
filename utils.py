# -*- coding: utf-8 -*-
import sys
import codecs
import os
import re
import time
import random
import urlparse
import urllib2
import logging
import chardet
import utils


def log():
    logging.basicConfig(level=logging.DEBUG)
    return logging
#L = log()


def get_logger(logger_name):
    format_string = '%(asctime)s %(levelname)5s %(message)s'
    level = logging.DEBUG
    logging.basicConfig(format=format_string, level=level)
    logger = logging.getLogger(logger_name)
    return logger

L = get_logger(__name__)


def get_socket_resp(url=None, extr_headers=None):
    time.sleep(random.randrange(5, 20, 1))
    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.5',
        'User-Agent':
        'Mozilla/5.0 (Windows NT 5.1; rv:19.0) Gecko/20100101 Firefox/19.0'
    }

    request = urllib2.Request(url=url, headers=headers)

    if extr_headers:
        if hasattr(extr_headers, 'items'):
            extr_headers = extr_headers.items()
        else:
            try:
                if len(extr_headers) and not \
                        isinstance(extr_headers[0], tuple):
                    raise TypeError
            except TypeError:
                f
                L.error('#'*15 + '[get_socket_resp] extr_headers type error')
        for k, v in extr_headers:
            request.add_header(k, v)

    opener = urllib2.build_opener()
    resp = None
    try:
        resp = opener.open(request)
    except urllib2.HTTPError as e:
        L.error('%s %s' % (e.code, url))
    finally:
        return resp


def get_resp_body(resp):
    data = resp.read()
    data_encoding = resp.headers.get('Content-Encoding', None)
    if data_encoding == 'gzip':
        import StringIO
        import gzip
        return gzip.GzipFile(fileobj=StringIO.StringIO(data), mode='rb').read()
    elif data_encoding == 'deflate':
        import zlib
        return zlib.decompressobj(-zlib.MAX_WBITS).decompress(data)
    return data


def get_raw_html(url=None):
    if not url:
        return None
    resp = get_socket_resp(url)
    if not resp:
        return None
    resp = get_resp_body(resp)
    encoding = chardet.detect(resp)['encoding']
    return resp.decode(encoding, 'ignore')


def save_binary_file(filename, data):
    with open(filename, 'wb') as f:
        f.write(data)


def save_text_file(filename, data):
    encoding = chardet.detect(data)['encoding']
    if not encoding:
        encoding = 'utf-8'
    L.debug('#encoding: %s' % encoding)
    data = data.decode(encoding, 'ignore')
    with codecs.open(filename, mode='w', encoding=encoding) as f:
        f.write(data)


if __name__ == '__main__':
    a = get_resp_body(get_socket_resp('http://www.baidu.com/'))[:1000]
    L.info(u'百度内容： %s'.encode('u8'), a)
