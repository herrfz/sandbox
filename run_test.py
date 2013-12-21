import time
import urllib
import threading
import Queue
import os
import signal
import argparse
from sys import platform as _platform

if _platform=='win32':
    devnull = 'nul'
else:
    devnull = '/dev/null'

parser = argparse.ArgumentParser()
parser.add_argument('n_clients', help='the number of clients to generate', type=int)
parser.add_argument('-m', '--multiplier', help='max_queue = m * n_clients', type=int)
args = parser.parse_args()

n_clients = args.n_clients if args.n_clients > 0 else 1
if args.multiplier and args.multiplier > 0:
    q_size = args.multiplier * n_clients
else: 
    q_size = 1 # just set a small queue size such that the program will eventually stop
    
queue = Queue.Queue()
lock = threading.Lock()

class Client(threading.Thread):
    def __init__(self, cid, url, interval):
        threading.Thread.__init__(self)
        self.cid = cid
        self.url = url
        self.interval = interval
        self.stopped = False
        self.downloaded = 0
        
    def run(self):
        while True:
            if not self.stopped:
                lock.acquire() # don't allow other threads to add tasks while one is being added
                queue.put((self.cid, self.url))
                lock.release()
                time.sleep(self.interval)
            else:
                break
                
class Worker(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.stopped = False
        
    def run(self):
        while True:
            try:
                if not self.stopped:
                    if not queue.empty():
                        print ','.join([time.ctime(time.time()), str(queue.qsize())])
                        cid, cur_url = queue.get()
                        _ , headers = urllib.urlretrieve(cur_url, devnull)
                        downloaded = headers.getheader('Content-Length')
                        queue.task_done()
                        if downloaded is not None:
                            clients[cid].downloaded += int(downloaded)
                            
                    else:
                        print ','.join([time.ctime(time.time()), '0'])
                        time.sleep(1)
                        
                else:
                    break
                        
            except KeyboardInterrupt:
                break
                
            except RuntimeError:
                queue.task_done()
                continue

def clean_quit(signum, frame):
    print 'interrupting...'
    for client in clients:
        client.stopped = True
    threads = [c.join(1) for c in clients if c is not None and c.isAlive()]
    print 'clients stopped'
    worker.join(1)
    worker.stopped = True
    print 'worker stopped'
    testtime = time.time() - starttime
    mbps_scaler = 8 / testtime / 1e6
    agg_data = 0
    print '======================='
    for client in clients:
        print 'client %03d: %f Mbps' % (client.cid, client.downloaded * mbps_scaler)
        agg_data += client.downloaded
    print '======================='
    print 'average: %f Mbps' % (agg_data * mbps_scaler / n_clients)
    print 'bye!\n'
    os._exit(0)

    
if __name__=='__main__':
    signal.signal(signal.SIGINT, clean_quit)
    clients = []
    #base_url = 'http://www.google.com/favicon.ico'  
    base_url = 'http://www.freeware-guide.com/download/files/playlist.zip'
    wget_interval = 9 # seconds
    client_interval = 2 # seconds
    
    worker = Worker()
    worker.start()
    
    starttime = time.time()

    for i in xrange(n_clients):
        client = Client(i, base_url, wget_interval)
        client.start()
        clients.append(client)
        time.sleep(client_interval)
    
    while True:
        if queue.qsize() > q_size:  # this check is not always accurate
            print 'max queue size exceeded!'
            clean_quit(signal.SIGINT, None)
        else:
            continue
