# -*- coding:utf-8 -*-
import os

cwd = os.getcwd()
path = os.path.join(cwd, 'res_mtime')

import glob
print glob.glob(os.path.join(path, '*.stp1'))

