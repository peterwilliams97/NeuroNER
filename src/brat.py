"""
    PDF to text conversion
"""
import os
from glob import glob
from collections import defaultdict
import hashlib
import string
from subprocess import CalledProcessError, Popen, PIPE
import utils
import re


nn = os.path.expanduser('~/code/NeuroNER')
assert os.path.exists(nn), nn

path_list = list(glob(os.path.join(nn, '*.ann'), recursive=True))
print('%d files' %)
