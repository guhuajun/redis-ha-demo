# -*- coding: utf-8 -*-
# pylint: disable=


import logging
import sys
import time
from datetime import datetime

from redis.sentinel import Sentinel

if __name__ == "__main__":
    # change logging config
    logging.basicConfig(level=logging.DEBUG,
                        format='[%(asctime)s.%(msecs)03d][%(filename)s, %(lineno)d][%(levelname)s]%(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    # redis
    sentinels = [
        ('redis-sentinel-1', 26379),
        ('redis-sentinel-2', 26379),
        ('redis-sentinel-3', 26379)
    ]

    while True:
        try:
            sentinel = Sentinel(sentinels, socket_timeout=1)
            logging.debug(str(sentinel.discover_master('mymaster')))
            logging.debug(str(sentinel.discover_slaves('mymaster')))

            master = sentinel.master_for('mymaster', socket_timeout=1, password='123456')
            slave = sentinel.slave_for('mymaster', socket_timeout=1, password='123456')

            master.set('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            logging.debug('Reading key - timestamp: %s', slave.get('timestamp'))
        except Exception as ex:
            logging.error(str(ex))
        finally:
            time.sleep(1)