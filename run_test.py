'''Tester client'''
import time
import urllib
import threading
import Queue
import os
import signal
import argparse
from sys import platform as _platform

if _platform == 'win32':
    devnull = 'nul'
else:
    devnull = '/dev/null'

parser = argparse.ArgumentParser()
parser.add_argument('n_clients', help='the number of clients to generate',
                    type=int)
parser.add_argument('-m', '--multiplier', help='max_queue = m * n_clients',
                    type=float)
args = parser.parse_args()

n_clients = args.n_clients if args.n_clients > 0 else 1
if args.multiplier and args.multiplier > 0:
    q_size = int(args.multiplier * n_clients)
else:
    q_size = n_clients

queue = Queue.Queue()
lock = threading.Lock()


class Client(threading.Thread):
    ''' Client thread, sends (cid, url) to the queue at a regular interval'''
    def __init__(self, cid, url, interval):
        threading.Thread.__init__(self)
        self.cid = cid
        self.url = url
        self.interval = interval
        self.stopped = False
        self.downloaded = 0

    def run(self):
        while not self.stopped:
            lock.acquire()  # block other threads before adding a task
            queue.put((self.cid, self.url))
            lock.release()
            time.sleep(self.interval)


class Worker(threading.Thread):
    ''' Worker thread, download files from url in the queue'''
    def __init__(self):
        threading.Thread.__init__(self)
        self.stopped = False

    def run(self):
        while not self.stopped or not queue.empty():
            cur_qsize = queue.qsize()
            print ','.join([time.ctime(time.time()),
                            str(cur_qsize)])
            if cur_qsize == 0:
                time.sleep(1)
            else:
                try:
                    cid, cur_url = queue.get()
                    _, headers = urllib.urlretrieve(cur_url, devnull)
                    downloaded = headers.getheader('Content-Length')
                    queue.task_done()
                    if downloaded is not None:
                        clients[cid].downloaded += int(downloaded)

                except:  # just carry on if anything goes wrong
                    continue


def clean_quit(signum, frame):
    '''stop clients and workers, print out test reports'''
    _, _ = signum, frame
    print 'interrupting...'
    for clt in clients:
        clt.stopped = True
    print 'clients stopped'
    worker.stopped = True
    print 'emptying queue...'
    worker.join()
    print 'queue emptied'
    print 'worker stopped'
    testtime = time.time() - starttime
    mbps_scaler = 8 / testtime / 1e6
    agg_data = 0
    print '========================='
    for clt in clients:
        print 'client %03d: %f Mbps' % (clt.cid,
                                        clt.downloaded * mbps_scaler)
        agg_data += clt.downloaded
    print '========================='
    print 'average: %f Mbps' % (agg_data * mbps_scaler / len(clients))
    print 'bye!\n'
    os._exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, clean_quit)
    clients = []
    #base_url = 'http://www.google.com/favicon.ico'
    base_url = 'http://www.freeware-guide.com/download/files/playlist.zip'
    wget_interval = 9  # seconds
    client_interval = 2  # seconds

    worker = Worker()
    worker.start()

    starttime = time.time()

    for i in xrange(n_clients):
        client = Client(i, base_url, wget_interval)
        client.start()
        clients.append(client)
        time.sleep(client_interval)

    while True:
        if queue.qsize() > q_size:  # works but not always timely stop the test
            print 'max queue size exceeded!'
            clean_quit(signal.SIGINT, None)
        else:
            time.sleep(1)  # !!!
