from distutils.util import strtobool
from multiprocessing import cpu_count
from os import getenv

port = getenv('PORT', 5000)
workers = int(getenv('WEB_CONCURRENCY', cpu_count() * 2))
