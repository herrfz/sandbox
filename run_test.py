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
parser.add_argument('-l', '--logfile', help='file to log output',
                    type=str)
args = parser.parse_args()

n_clients = args.n_clients if args.n_clients > 0 else 1
logfile = args.logfile if args.logfile else 'test.log'
if args.multiplier and args.multiplier > 0:
    q_size = int(args.multiplier * n_clients)
else:
    q_size = n_clients

logger = logging.getLogger('logger')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s, %(message)s')
hdlrs = [logging.FileHandler(logfile, mode='w'),
         logging.StreamHandler(sys.stdout)]
for hdlr in hdlrs:
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)


class Client(threading.Thread):
    ''' Client thread, sends (cid, url) to the queue at a regular interval'''
    def __init__(self, cid, url, interval):
        threading.Thread.__init__(self)
        self.cid = cid
        self.url = url
        self.interval = interval
        self.queue = Queue.Queue()
        self.stopped = False
        self.downloaded = 0

    def run(self):
        while not self.stopped:
            self.queue.put(self.url)
            time.sleep(self.interval)


class Worker(threading.Thread):
    ''' Worker thread, download files from url in the queue'''
    def __init__(self, client):
        threading.Thread.__init__(self)
        self.client = client
        self.stopped = False

    def run(self):
        while not self.stopped or not self.client.queue.empty():
            try:
                logger.info('{0}, {1}'.format(self.client.cid,
                                              self.client.queue.qsize()))
                cur_url = self.client.queue.get(block=True)
                _, headers = urllib.urlretrieve(cur_url, devnull)
                downloaded = headers.getheader('Content-Length')
                self.client.queue.task_done()
                if downloaded is not None:
                    self.client.downloaded += int(downloaded)
                                        
            except:  # just carry on if anything else goes wrong
                continue


def clean_quit(signum, frame):
    '''stop clients and workers, print out test reports'''
    _, _ = signum, frame
    logger.debug('interrupting...')
    for clt, wrk in zip(clients, workers):
        clt.stopped = True
        wrk.stopped = True
    logger.debug('clients and workers stopped')
    testtime = time.time() - starttime
    mbps_scaler = 8 / testtime / 1e6
    agg_data = 0
    logger.info('=================')
    for clt in clients:
        logger.info('%02d: %f Mbps', clt.cid, clt.downloaded * mbps_scaler)
        agg_data += clt.downloaded
    logger.info('=================')
    logger.info('average: %f Mbps', agg_data * mbps_scaler / len(clients))
    os._exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, clean_quit)
    clients = []
    workers = []
    #base_url = 'http://www.freeware-guide.com/download/files/lexunbackupsolution.zip'
    base_url = 'http://172.16.255.253/test_hobbit/hobbit_std/InternalUSEONLYTheHobbit_trailer_std-9.ts'
    wget_interval = 9  # seconds
    client_interval = 2  # seconds

    starttime = time.time()

    for i in xrange(n_clients):
        client = Client(i, base_url, wget_interval)
        client.start()
        clients.append(client)
        worker = Worker(client)
        worker.start()
        workers.append(worker)
        time.sleep(client_interval)

    while True:
        time.sleep(1)  # !!!
