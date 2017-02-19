import pika

from yamajudge.util import options

options.define('mq_host', default='localhost', help='Message queue hostname or IP address.')
options.define('mq_vhost', default='/anubis', help='Message queue virtual host.')
options.define('mq_user', default='guest', help='Message queue username.')
options.define('mq_password', default='guest', help='Message queue password')

_connection = None
_channels = {}


def _connect():
    global _connection
    if _connection:
        return _connection
    credentials = pika.PlainCredentials(username=options.options.mq_user,
                                        password=options.options.mq_password)
    parameters = pika.ConnectionParameters(
        host=options.options.mq_host,
        virtual_host=options.options.mq_vhost,
        credentials=credentials)
    try:
        _connection = pika.BlockingConnection(parameters=parameters)
        return _connection
    except Exception as e:
        raise e


def channel(key=None):
    global _channels
    if key:
        if key in _channels:
            return _channels[key]
    try:
        channel = _connect().channel()
        return channel
    except Exception as e:
        del _channels[key]
        raise e
