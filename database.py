# -*- coding: utf-8 -*-
import sqlite3
import os.path
import time
import logging

L = logging.getLogger()

from config import DATA_DIR


class DB(object):
    def __init__(self, filename, timeout=0):
        self.filename = filename
        self.timeout = timeout
        self.cursor = None
        self.conn = None
        self.conntime = 0
        self.reset()

    def reset(self):
        self.close()
        self.conn = sqlite3.connect(self.filename)
        self.conn.text_factory = str
        self.cursor = self.conn.cursor()
        self.conntime = int(time.time())

    def reconn(self):
        if self.timeout < 1:
            return
        n = int(time.time())
        if n - self.conntime >= self.timeout:
            self.reset()
        self.conntime = n

    def execute(self, *args, **kws):
        v = list(args)
        if isinstance(v[0], str):
            v[0] = v[0].replace('%s', '?')
            v[0] = v[0].replace('%d', '?')
        if len(v) > 1:
            if not isinstance(v[1], list) and not isinstance(v[1], tuple):
                v[1] = (v[1], )
        args = tuple(v)
        self.reconn()
        self.cursor.execute(*args,  **kws)

    def getall(self):
        self.reconn()
        return self.cursor.fetchall()

    def getone(self):
        self.reconn()
        return self.cursor.fetchone()

    def insert_id(self):
        return self.cursor.lastrowid

    def commit(self):
        self.reconn()
        self.conn.commit()

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.commit()
            self.conn.close()
        self.cursor = None
        self.conn = None

    def __del__(self):
        self.close()


def createDB():
    dbfile = os.path.join(DATA_DIR, 'data.db')
    if os.path.exists(dbfile):
        L.error('data.db already exists!')
    return DB(dbfile)


def initDB():
    '''
    videos:
        id      int pk autoinc
        name    text //名称
        alias   text //别名
        rank    real //评分
    '''
    db = createDB()
    db.execute('''DROP TABLE IF EXISTS videos''')
    db.execute('''CREATE TABLE videos (id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, alias TEXT, rank REAL)''')
    db.execute('INSERT INTO videos (name) VALUES (%s)', '雷神2：黑暗世界')

    db.close()

if __name__ == '__main__':
    initDB()
