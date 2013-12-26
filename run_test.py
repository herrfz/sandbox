'''Tester client'''
import time
import urllib
import threading
import Queue
import os
import sys
import signal
import argparse
import socket
import logging
from sys import platform as _platform

if _platform == 'win32':
    devnull = 'nul'
else:
    devnull = '/dev/null'

timeout = 5
socket.setdefaulttimeout(timeout)

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

logger = logging.getLogger('logger')
formatter = logging.Formatter('%(asctime)s %(message)s')
hdlr = logging.FileHandler('test.log')
hdlr.setFormatter(formatter)
console_hdlr = logging.StreamHandler(sys.stdout)
console_hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.addHandler(console_hdlr)
logger.setLevel(logging.INFO)

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
            logger.info(str(cur_qsize))
            if cur_qsize == 0:
                time.sleep(0.5)
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
    logger.debug('interrupting...')
    for clt in clients:
        clt.stopped = True
    logger.debug('clients stopped')
    worker.stopped = True
    logger.debug('emptying queue...')
    worker.join()
    logger.debug('queue emptied')
    logger.debug('worker stopped')
    testtime = time.time() - starttime
    mbps_scaler = 8 / testtime / 1e6
    agg_data = 0
    logger.info('======================')
    for clt in clients:
        logger.info('client-%02d:%fMbps' % (clt.cid, 
                                              clt.downloaded * mbps_scaler))
        agg_data += clt.downloaded
    logger.info('======================')
    logger.info('average:%fMbps' % (agg_data * mbps_scaler / len(clients)))
    os._exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, clean_quit)
    clients = []
    base_url = 'http://www.freeware-guide.com/download/files/playlist.zip'
    #base_url = 'http://blitz:8000/coffee.mp4'
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
            logger.warning('max queue size exceeded!')
            clean_quit(signal.SIGINT, None)
        else:
            time.sleep(1)  # !!!
