import subprocess as sp
import os
import signal
import time

i = 0
while True:
    try:
        logfile = 'test_' + str(i) + '.log'
        a = sp.Popen(['python', 'run_test.py', '-m 3', '12', '-l', logfile])
        time.sleep(15 * 60)
        os.kill(a.pid, signal.SIGINT)
        time.sleep(15 * 60)
        i += 1
    except KeyboardInterrupt:
        os.kill(a.pid, signal.SIGINT)
        time.sleep(60)
        break