# -*- coding: utf-8 -*-
import os
import re
import time
import urllib
import urllib2
import logging
import HTMLParser
import MultipartPostHandler

from cookielib import CookieJar


def get_logger(logger_name):
    format_string = '%(asctime)s %(levelname)5s %(message)s'
    level = logging.DEBUG
    logging.basicConfig(format=format_string, level=level)
    logger = logging.getLogger(logger_name)
    return logger

L = get_logger(__name__)


class SinaImg():
    def __init__(self):
        self.cookies = None
        self.referer = None
        self.url_login_prepare = 'http://login.weibo.cn/login/'
        self.url_img_add = 'http://weibo.cn/album/photo/add'
        self.url_img_doadd = 'http://weibo.cn/album/photo/doadd'
        self.headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.5',
            'User-Agent':
            'Mozilla/5.0 (Windows NT 5.1; rv:19.0) \Gecko/20100101 \
            Firefox/19.0'
        }

    def decode_resp(self, resp):
        data = resp.read()
        data_encoding = resp.headers.get('Content-Encoding', None)
        if data_encoding == 'gzip':
            import StringIO
            import gzip
            tmp = gzip.GzipFile(fileobj=StringIO.StringIO(data), mode='rb')
            return tmp.read()
        elif data_encoding == 'deflate':
            import zlib
            return zlib.decompressobj(-zlib.MAX_WBITS).decompress(data)
        return data

    def socket_resp(self, url=None, usecookies=False, **kwargs):
        fileds = None
        if 'fileds' in kwargs:
            body = kwargs.pop('fileds')
            fileds = '&'.join([k+'='+v for k, v in body.items()])

        request = urllib2.Request(url=url, data=fileds, headers=self.headers)

        if 'headers' in kwargs:
            extra_headers = kwargs.pop('headers')
            if hasattr(extra_headers, 'items'):
                extra_headers = extra_headers.items()
            else:
                try:
                    if len(extra_headers) and not isinstance(
                        extra_headers[0], tuple
                    ):
                        raise TypeError
                except TypeError:
                    L.error('#'*15 + ' extra_headers type error')
            for k, v in extra_headers:
                request.add_header(k, v)

        if 'cookies' in kwargs:
            self.cookies = kwargs.pop('cookies')

        resp = None
        if usecookies:
            try:
                if not self.cookies:
                    cookies_request = urllib2.Request(
                        url=url, headers=self.headers
                    )
                    response = urllib2.urlopen(cookies_request)
                    self.cookies = CookieJar()
                    self.cookies.extract_cookies(response, cookies_request)
                cookie_handler = urllib2.HTTPCookieProcessor(self.cookies)
                redirect_handler = urllib2.HTTPRedirectHandler()
                opener = urllib2.build_opener(redirect_handler, cookie_handler)
                resp = opener.open(request)
            except urllib2.HTTPError as e:
                L.error('%s %s' % (e.code, url))
            finally:
                return self.decode_resp(resp)
        else:
            opener = urllib2.build_opener()
            try:
                resp = opener.open(request)
            except urllib2.HTTPError as e:
                L.error('%s %s' % (e.code, url))
            finally:
                return self.decode_resp(resp)

    def login_prepare(self, raw):
        form_action = None
        filed_password = None
        filed_vk = None
        filed_backURL = None
        filed_backTitle = None
        filed_submit = None

        pattern = re.compile('form action="([^"]*)"')
        if pattern.search(raw):
            form_action = pattern.search(raw).group(1)

        pattern = re.compile('password" name="([^"]*)"')
        if pattern.search(raw):
            filed_password = pattern.search(raw).group(1)

        pattern = re.compile('name="vk" value="([^"]*)"')
        if pattern.search(raw):
            filed_vk = pattern.search(raw).group(1)

        pattern = re.compile('name="backURL" value="([^"]*)"')
        if pattern.search(raw):
            filed_backURL = pattern.search(raw).group(1)

        pattern = re.compile('name="backTitle" value="([^"]*)"')
        if pattern.search(raw):
            filed_backTitle = pattern.search(raw).group(1)

        pattern = re.compile('name="submit" value="([^"]*)"')
        if pattern.search(raw):
            filed_submit = pattern.search(raw).group(1)

        fileds = {
            'form_action': form_action,
            'password': filed_password,
            'vk': filed_vk,
            'backURL': filed_backURL,
            'backTitle': filed_backTitle,
            'submit': filed_submit
        }
        return fileds

    def login(self):
        raw_login = self.socket_resp(self.url_login_prepare, True)
        fileds_pre = self.login_prepare(raw_login)

        url = self.url_login_prepare + fileds_pre.get('form_action')
        #url = HTMLParser.HTMLParser().unescape(
        #    url_login_prepare + fileds_pre.get('form_action')
        #)
        headers = {'Referer': self.url_login_prepare}
        fileds = {
            'mobile': 'oyiyi.com@gmail.com',
            '%s' % fileds_pre.get('password'): 'lovelele',
            'remember': 'on',
            'backURL': fileds_pre.get('backURL'),
            'backTitle': fileds_pre.get('backTitle'),
            'tryCount': '',
            'vk': fileds_pre.get('vk'),
            'submit': fileds_pre.get('submit')
        }
        resp = self.socket_resp(url, True, fileds=fileds, headers=headers,
                                cookies=self.cookies)
    def img_add_prepare(self, raw):
        filed_album_id = None
        filed_upload = None
        filed_rl = None

        pattern = re.compile('option value="([^"]*)"')
        if pattern.search(raw):
            filed_album_id = pattern.search(raw).group(1)

        pattern = re.compile('name="upload" value="([^"]*)"')
        if pattern.search(raw):
            filed_upload = pattern.search(raw).group(1)

        pattern = re.compile('name="rl" value="([^"]*)"')
        if pattern.search(raw):
            filed_rl = pattern.search(raw).group(1)

        fileds = {
            'album_id': filed_album_id,
            'upload': filed_upload,
            'rl': filed_rl
        }
        return fileds

    def get_filename(self, file_path):
        return os.path.basename(file_path)

    def get_filetype(self, file_path):
        return os.path.splitext(file_path)[1]

    def get_img_url(self, raw=None):
        '''
        with open('sina_album.html', 'rb') as fh:
            raw = fh.read()
        '''

        img_url = None
        pattern = re.compile('<img src="([^"]*)" alt=\'\'')
        if pattern.search(raw):
            img_url = pattern.search(raw).group(1)
        return img_url

    def get_remote_img(self, url, filename='temp.jpg'):
        #return self.socket_resp(url)
        import utils
        utils.save_binary_file(filename, self.socket_resp(url))
        return filename

    def upload(self, upfile=None):
        if not upfile and upfile:
            L.debug('have no img to upload')
            return None

        if upfile.startswith('http://'):
            upfile = self.get_remote_img(upfile)

        raw_img_add = self.socket_resp(self.url_img_add, True)
        fileds_pre = self.img_add_prepare(raw_img_add)

        fileds = {
            'album_id': fileds_pre.get('album_id'),
            #'photo': raw_img,
            'photo': open(upfile, 'rb'),
            'description': '',
            'upload': fileds_pre.get('upload'),
            'rl': fileds_pre.get('rl')
        }

        headers = self.headers.copy()
        headers.update({'Referer': self.url_img_add})

        url = self.url_img_doadd

        request = urllib2.Request(url, None, headers)
        cookie_handler = urllib2.HTTPCookieProcessor(self.cookies)
        redirect_handler = urllib2.HTTPRedirectHandler()
        opener = urllib2.build_opener(
            cookie_handler, redirect_handler,
            MultipartPostHandler.MultipartPostHandler
        )
        resp = opener.open(request, fileds)
        result = self.get_img_url(self.decode_resp(resp))
        L.debug('uploaded image url: %s' % (result,))
        return result

    def upload_batch(self, upfiles=None):
        if not upfiles:
            return None
        result = []
        for upfile in upfiles:
            result.append(self.upload(upfile))
        return result

if __name__ == '__main__':
    url = 'http://img31.mtime.cn/mt/801/10801/10801_300x450.jpg'
    si = SinaImg()
    si.login()
    si.upload(url)
