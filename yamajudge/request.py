import functools
import logging
from urllib import request
from urllib import parse
from http import cookiejar
from threading import Timer
from threading import Lock
from bson import objectid

from yamajudge.util import options
from yamajudge.constant import record
from yamajudge import error

options.define('api_host', default='http://localhost', help='Judge API hostname.')
options.define('api_heartbeat', default='/judge/heartbeat', help='Judge API heartbeat.')
options.define('api_judge_main', default='/judge/main', help='Main judge API.')
options.define('api_login', default='/login', help='User login API.')
options.define('judger_username', default='judger', help='Username of judger.')
options.define('judger_password', default='judger', help='Password of judger.')

_logger = logging.getLogger(__name__)
_opener = request.build_opener(request.HTTPCookieProcessor(cookiejar.CookieJar()))
request.install_opener(_opener)
_lock = Lock()
_api_judge_main = options.options.api_host + options.options.api_judge_main


def post(url: str, **kwargs):
    params = parse.urlencode(kwargs)
    data = params.encode('utf-8')
    req = request.Request(url=url,
                          data=data,
                          headers={'Accept': 'application/json'})
    try:
        _logger.debug('Waiting for lock...')
        with _lock:
            _logger.debug('Lock acquired.')
            res = request.urlopen(req)
    except Exception as e:
        raise e
    return res or None


def get(url: str):
    req = request.Request(url=url, headers={'Accept': 'application/json'})
    try:
        _logger.debug('Waiting for lock...')
        with _lock:
            _logger.debug('Lock acquired.')
            res = request.urlopen(req)
    except Exception as e:
        raise e
    return res or None


def login():
    res = post(url=options.options.api_host + options.options.api_login,
               uname=options.options.judger_username,
               password=options.options.judger_password,
               remember_me=True)
    if res.status != 200:
        raise error.LoginError(options.options.judger_username)
    _logger.info('Use username login: {0}'.format(options.options.judger_username))


def heartbeat():
    _logger.debug('Send heartbeat request...')
    get(options.options.api_host + options.options.api_heartbeat)
    timer = Timer(30.0, heartbeat)
    timer.start()


def init():
    login()
    heartbeat()
    _logger.info('Heartbeat timer started.')


def begin_judge(rid: objectid.ObjectId, status: int=record.STATUS_FETCHED):
    post(_api_judge_main, operation='begin', rid=str(rid), status=status)


def next_judge(rid: objectid.ObjectId, **kwargs):
    post(_api_judge_main, operation='next', rid=str(rid), **kwargs)


def end_judge(rid: objectid.ObjectId, status: int, time_ms: int=0, memory_kb: int=0):
    post(_api_judge_main, operation='end', rid=str(rid),
         status=status, time_ms=time_ms, memory_kb=memory_kb)
