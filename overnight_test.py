import subprocess as sp
import os
import signal
import time

i = 0
while True:
    try:
        for j in xrange(5, 14):
            logfile = 'test_' + str(j) + '_' + str(i) + '.log'
            a = sp.Popen(['python', 'run_test.py', str(j), '-l', logfile])
            time.sleep(15 * 60)
            os.kill(a.pid, signal.SIGINT)
            time.sleep(15 * 60)
            
        i += 1
        
    except KeyboardInterrupt:
        os.kill(a.pid, signal.SIGINT)
        break