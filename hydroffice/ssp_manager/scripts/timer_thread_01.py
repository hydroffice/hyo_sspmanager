from __future__ import absolute_import, division, print_function

import datetime
import time

from ...base.timerthread import TimerThread


def run():
    print(datetime.datetime.now())

t = TimerThread(target=run, timing=0.5)
t.start()

time.sleep(5)
if t.is_alive():
    t.stop()
    print('\nStopping thread ...\n')

time.sleep(1)
print('Thread stopped: %s' % t.is_alive())