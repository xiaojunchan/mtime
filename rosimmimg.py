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


def get_logger(logger_name):
    format_string = '%(asctime)s %(levelname)5s %(message)s'
    level = logging.DEBUG
    logging.basicConfig(format=format_string, level=level)
    logger = logging.getLogger(logger_name)
    return logger

#L = get_logger('rosimm')
L = logging.getLogger(__name__)


def get_socket_resp(url=None, extr_headers=None):
    time.sleep(random.randrange(5, 20, 1))
    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.5',
        'User-Agent': 'Mozilla/5.0 (Windows NT 5.1; rv:19.0) Gecko/20100101 \
        Firefox/19.0'
    }

    request = urllib2.Request(url=url, headers=headers)

    if extr_headers:
        if hasattr(extr_headers, 'items'):
            extr_headers = extr_headers.items()
        else:
            try:
                if len(extr_headers) \
                        and not isinstance(extr_headers[0], tuple):
                    raise TypeError
            except TypeError:
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


def get_gather_url(html):
    pattern = ur'(?imsu)(?:href|src)="(.*?)"'
    regex = re.compile(pattern)
    urls = regex.findall(html)
    urls = list(set(urls))
    return urls


def get_css_assets(source_url=None):
    data = get_raw_html(source_url)
    if not data:
        return []
    pattern = ur'(?imsu)[(](?:"|\')?(.*?)(?:"|\')?[)]'
    regex = re.compile(pattern)
    undeal_urls = regex.findall(data)
    undeal_urls = list(set(undeal_urls))
    allow_ext = ['.css', '.jpg', '.gif', '.png']
    urls = []
    for url in undeal_urls:
        for ext in allow_ext:
            if url.endswith(ext):
                url = url.startswith('http://')\
                    and url or urlparse.urljoin(source_url, url)
                if url.endswith('.css'):
                    css_urls = get_css_assets(url)
                    urls.extend(css_urls)
                urls.append(url)
                break
    return urls


def get_html_assets(source_url=None):
    data = get_raw_html(source_url)
    if not data:
        return []
    pattern = ur'(?imsu)(?:href|src)="(.*?)"'
    regex = re.compile(pattern)
    undeal_urls = regex.findall(data)
    undeal_urls = list(set(undeal_urls))
    allow_ext = ['.js', '.jpg', '.gif', '.png']
    urls = []
    for url in undeal_urls:
        for ext in allow_ext:
            if url.endswith(ext):
                url = url.startswith('http://')\
                    and url or urlparse.urljoin(source_url, url)
                urls.append(url)
                break
    return urls


def deal_gather_url(undeal_urls, source_url=None):
    allow_ext = ['.js', '.css', '.jpg', '.gif', '.png', '.html']
    urls = []
    for url in undeal_urls:
        for ext in allow_ext:
            if url.endswith(ext):
                url = url.startswith('http://')\
                    and url or urlparse.urljoin(source_url, url)
                urls.append(url)
                if url.endswith('.css'):
                    css_urls = get_css_assets(url) or []
                    L.info('*'*10 + ''.join(css_urls))
                    urls.extend(css_urls)
                if url.endswith('.html'):
                    html_urls = get_html_assets(url) or []
                    L.info('*'*10 + ''.join(html_urls))
                    urls.extend(html_urls)
                break
    urls = list(set(urls))
    return urls


def save_gather_data(filename, resp):
    binary_ext = ['jpg', 'png', 'gif']
    ext = filename.rsplit('.', 1)[1]
    if ext in binary_ext:
        data = resp.read()
        save_binary_file(filename, data)
    else:
        data = get_resp_body(resp)
        save_text_file(filename, data)


def dump_template(source_url):
    out_folder = os.path.normpath('rosimm/templates/admin/s/')
    out_folder = os.path.join(os.getcwd(), out_folder)
    raw_html = get_raw_html(source_url)
    if not raw_html:
        return None
    undeal_urls = get_gather_url(raw_html)
    urls = deal_gather_url(undeal_urls, source_url)
    for url in urls:
        parsed_url = urlparse.urlparse(url)
        save_path = os.path.join(
            out_folder,
            parsed_url.netloc + os.path.dirname(parsed_url.path)
        )
        save_path = os.path.normpath(save_path)
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        basename = os.path.basename(parsed_url.path)
        filename = os.path.join(save_path, basename)
        if os.path.exists(filename):
            continue
        L.debug('#filename: %s' % filename)
        L.debug('#url: %s' % url)
        resp = get_socket_resp(url)
        if not resp:
            continue
        save_gather_data(filename, resp)


def get_local_file(filename=None):
    if not filename:
        filename = 'utf-8.txt'
    filename = os.path.join(os.getcwd(), 'rosimm/helper/', filename)
    filename = os.path.normpath(filename)
    with open(filename, 'r') as f:
        data = f.read()
    encoding = chardet.detect(data)['encoding']
    data = data.decode(encoding)
    return data


def get_list_urls():
    '''
    [
    'http://missmm.com/page-1.html',
    'http://missmm.com/page-2.html',
    ...,
    'http://missmm.com/page-[max_list].html'
    ]
    '''
    url = 'http://missmm.com/'
    resp = get_socket_resp(url, {'Referer': url})
    data = get_resp_body(resp)
    encoding = chardet.detect(data)['encoding']
    data = data.decode(encoding)

    #data = get_local_file('shouye.txt')

    #pattern = ur'(?imsu)href="(.*?(?:page-[0-9])\.html)"'
    pattern = ur'(?imu)href=".*?-([0-9]+)\.html"'
    regex = re.compile(pattern)
    list_numbers = regex.findall(data)
    list_numbers = map(int, list_numbers)
    max_list = max(list_numbers)
    list_urls = []
    for i in range(1, max_list+1):
        basename = 'page-' + str(i) + '.html'
        list_urls.append(urlparse.urljoin(url, basename))

    L.info('*'*2+'[MAXLIST]'+'*'*2+str(max_list))
    L.debug('*'*5+'[get_list_urls]'+'*'*5+str(list_urls))
    return list_urls


def get_album_urls(urls=None):
    ''' [(url, cover_url)] '''
    ''' [('http://missmm.com/521.html',
        'http://missmm.com/usr/uploads/2013/04/184766276.jpg')] '''

    def get_album_url(url, referer_url=None):
        L.debug('*' * 5 + '[get_album_url]' + '*' * 5 + url)
        resp = get_socket_resp(url, {'Referer': referer_url})
        data = get_resp_body(resp)
        encoding = chardet.detect(data)['encoding']
        data = data.decode(encoding)

        #data = get_local_file('page-1.txt')

        #pattern = ur'''(?imux)href="(.*?/[0-9]+\.html)">
        #<img\ssrc="/photo/thumb\.php\?src=(.*?)
        #&[^"]*"\salt="(.*?)"
        #'''
        pattern = ur'''(?imux)href="(.*?/[0-9]+\.html)">
        <img\ssrc="/photo/thumb\.php\?src=(.*?)
        &[^"]*"
        '''
        regex = re.compile(pattern)
        mixes = regex.findall(data)
        album_url = []
        for url, cover in mixes:
            album_url.append((url, urlparse.urljoin(url, cover)))
        return album_url

    album_urls = []
    referer_url = 'http://missmm.com/'
    if isinstance(urls, list):
        for url in urls:
            album_urls.extend(get_album_url(url, referer_url))
            referer_url = url
    elif isinstance(urls, str):
        album_urls.extend(get_album_url(urls))

    L.info(
        '*' * 2 + '[get_album_urls]' +
        '*' * 2 + str(len(album_urls)) +
        '*' * 2 + str(album_urls)
    )

    return album_urls


def get_album_info(url=None):
    L.info('*' * 2 + '[get_album_info]' + '*' * 2 + url)
    resp = get_socket_resp(url, {'Referer': url})
    data = get_resp_body(resp)
    encoding = chardet.detect(data)['encoding']
    data = data.decode(encoding)

    #url = 'http://missmm.com/523.html'
    #data = get_local_file('detail.txt')

    pattern_img = ur'''
    (?imux)
    href="(.*?(?:-|_)?[0-9]{3}\.jpg)">
    <img\s(?:alt="MissMM\.COM"\s)?src="(.*?)"
    '''
    pattern_period = ur'(?iu)description"\s{1}content="第(\d+?)期'
    pattern_pubdate = ur'(?iu)发布时间：(\d{4})年(\d{2})月(\d{2})日'
    #pattern_person = ur'(?iu)照片模特：<.*?>(.*?)<.*?>'
    pattern_person = ur'(?iu)description"\s{1}content="(?:.*?)模特(.*?)"'
    pattern_tags = ur'(?iu)keywords"\s{1}content="(.*?)"'

    regex = re.compile(pattern_img)
    mix_imgs = regex.findall(data)
    imgs = []
    for real_img, thumb_img in mix_imgs:
        imgs.append((real_img, urlparse.urljoin(url, thumb_img)))

    regex = re.compile(pattern_period)
    period = regex.findall(data)[0]

    regex = re.compile(pattern_pubdate)
    pubdate = regex.findall(data)[0]

    regex = re.compile(pattern_person)
    person = regex.findall(data)[0]

    regex = re.compile(pattern_tags)
    tags = regex.findall(data)[0].split(',')
    #tags = tags[:len(tags)-3]

    result = (url, period, pubdate, person, tags, imgs)
    return result


def save_album_photos(photos, source_url, photo_path):
    allow_ext = ['gif', 'png', 'jpg']
    for photo, thumb in photos:
        photo_ext = os.path.basename(photo).rsplit('.', 1)[1].lower()
        if not photo_ext in allow_ext:
            continue
        thumb_ext = os.path.basename(thumb).rsplit('.', 1)[1].lower()
        file_md5 = utils.get_timestamp_md5()
        filename_photo = file_md5 + '.' + photo_ext
        filename_thumb = file_md5 + '.s.' + thumb_ext
        filepath_photo = os.path.join(photo_path, filename_photo)
        filepath_thumb = os.path.join(photo_path, filename_thumb)

        resp = get_socket_resp(thumb, {'Referer': source_url})
        try:
            data = resp.read()
        except:
            pass
        else:
            save_binary_file(filepath_thumb, data)

        resp = get_socket_resp(photo, {'Referer': source_url})
        try:
            data = resp.read()
        except:
            pass
        else:
            save_binary_file(filepath_photo, data)

        L.info('*' * 2 + '[save_album_photos]' + '*' * 2 + str(thumb))
        L.info('*' * 2 + '[save_album_photos]' + '*' * 2 + str(photo))
        L.info('*' * 2 + '[save_album_photos]' + '*' * 2 + str(filename_thumb))
        L.info('*' * 2 + '[save_album_photos]' + '*' * 2 + str(filepath_thumb))
        L.info('*' * 2 + '[save_album_photos]' + '*' * 2 + str(filename_photo))
        L.info('*' * 2 + '[save_album_photos]' + '*' * 2 + str(filepath_photo))


def save_album_cover(cover, source_url, photo_path):
    allow_ext = ['gif', 'png', 'jpg']
    cover_ext = os.path.basename(cover).rsplit('.', 1)[1].lower()
    if not cover_ext in allow_ext:
        return None
    filename_cover = 'x.' + cover_ext
    filepath_cover = os.path.join(photo_path, filename_cover)

    resp = get_socket_resp(cover, {'Referer': source_url})
    data = resp.read()
    save_binary_file(filepath_cover, data)

    L.info('*' * 2 + '[save_album_cover]' + '*' * 2 + str(source_url))
    L.info('*' * 2 + '[save_album_cover]' + '*' * 2 + str(cover))
    L.info('*' * 2 + '[save_album_cover]' + '*' * 2 + str(filename_cover))
    L.info('*' * 2 + '[save_album_cover]' + '*' * 2 + str(filepath_cover))


def test():
    list_urls = get_list_urls()
    list_urls = list_urls[4:6]
    album_urls = get_album_urls(list_urls)
    album_urls = album_urls[:2]
    album_infos = []
    for album_url, cover_url in album_urls:
        mixes = get_album_info(album_url)
        album_infos.append((mixes[0], mixes[1], mixes[2], mixes[3],
                            mixes[4], cover_url, mixes[5]))
    for album_info in album_infos:
        L.info('*'*2 + '[ALBUM_INFO] ' + str(album_info))

    album_infos = album_infos[:2]
    uploads_path = os.path.join(os.getcwd(), 'rosimm', 'uploads')
    if not os.path.exists(uploads_path):
        os.makedirs(uploads_path)
    for album_info in album_infos:
        ablum_source_url = album_info[0]
        album_photo_path = os.path.join(uploads_path, album_info[1])
        if not os.path.exists(album_photo_path):
            os.makedirs(album_photo_path)
        album_cover = album_info[5]
        album_photos = album_info[6]
        L.info('*' * 10 + str(ablum_source_url))
        L.info('*' * 10 + str(album_photo_path))
        L.info('*' * 10 + str(album_cover))
        L.info('*' * 10 + str(album_photos))
        save_album_photos(album_photos, ablum_source_url, album_photo_path)


if __name__ == '__main__':
    test()
    #a = get_resp_body(get_socket_resp('http://www.baidu.com/'))[:1000]
    #L.info(u'百度内容： %s'.encode('u8'), a)
