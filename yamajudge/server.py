import logging
import logging.config
import os
import sys
import bson

from yamajudge.util import options
from yamajudge import mq
from yamajudge import request
from yamajudge.job import task
from yamajudge.constant import record

options.define('log_format',
               default=('%(log_color)s[%(levelname).1s '
                        '%(asctime)s %(module)s:%(lineno)d]%(reset)s %(message)s'),
               help='Log format.')
options.define('debug', default=False, help='Enable debug mode.')

_logger = logging.getLogger(__name__)


def on_message(channel, method, header, body):
    rid = bson.BSON.decode(body)['rid']
    request.begin_judge(rid)
    try:
        judge_task = task.JudgeTask(rid)
        judge_task.run()
    except Exception as e:
        _logger.error(e)
        request.end_judge(rid, record.STATUS_SYSTEM_ERROR)
        raise e
    finally:
        channel.basic_ack(method.delivery_tag)


def main():
    logging.config.dictConfig({
        'version': 1,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'colored',
            },
        },
        'formatters': {
            'colored': {
                '()': 'colorlog.ColoredFormatter',
                'format': options.options.log_format,
                'datefmt': '%y%m%d %H:%M:%S'
            }
        },
        'root': {
            'level': 'DEBUG' if options.options.debug else 'INFO',
            'handlers': ['console'],
        },
        'disable_existing_loggers': False,
    })

    request.init()
    channel = mq.channel('judge')
    channel.queue_declare('judge')
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(on_message, 'judge')
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()


if __name__ == '__main__':
    sys.exit(main())
