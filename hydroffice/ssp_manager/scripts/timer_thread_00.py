from __future__ import absolute_import, division, print_function

import threading
import time
import datetime


def run(timing=1):
    next_call = time.time()
    while True:
        next_call += timing
        now = datetime.datetime.now()
        print(now)
        time.sleep(next_call - time.time())


t = threading.Thread(target=run)
t.setDaemon(True)
t.start()

time.sleep(5)
