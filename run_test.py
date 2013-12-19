import time
import urllib
import threading
import Queue
import sys
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('n_clients', help='the number of clients to generate', type=int)
parser.add_argument('-m', '--multiplier', help='max_queue = m * n_clients', type=int)
args = parser.parse_args()

n_clients = args.n_clients
if args.multiplier and args.multiplier < 10: # don't allow arbitrary huge multiplier
    q_size = args.multiplier * n_clients
else: 
    q_size = n_clients # just set a small queue size such that the program will eventually stop
    
queue = Queue.Queue()
lock = threading.Lock()

class Getter():
    def __init__(self, url, ofile='/dev/null'):
        self.url = url
        self.ofile = ofile
        
    def start(self):
        urllib.urlretrieve(self.url, self.ofile)

class Client(threading.Thread):
    def __init__(self, cid, url, interval):
        threading.Thread.__init__(self)
        self.cid = cid
        self.url= url
        self.interval = interval
        self.stopped = False
        self.cur_task_id = 0
        self.completed_task = 0 # TODO: store the nbr of xferred bits, or req time, or rate
        
    def run(self):
        # TODO: how to automatically/programmatically stop if q_size is never exceeded;
        #       use signal listener?
        while True:
            if not self.stopped:
                lock.acquire() # don't allow other threads to add tasks while one is being added
                queue.put((self.cid, self.url, self.cur_task_id))
                lock.release()
                self.cur_task_id += 1
                time.sleep(self.interval)
            else:
                break


if __name__=='__main__':
    clients = []
    base_url = 'http://google.com/index.html'  
    #url = 'https://archive.org/download/alanoakleysmalltestvideo/spacetestSMALL.gif'
    ofile = 'nul'
    wget_interval = 9 # seconds
    client_interval = 2 # seconds
    
    # TODO: a better approach would be to add a 'Worker' thread here,
    #       which immediately starts dispatching the tasks:
    #       - there will be no initial transient backlogs,
    #       - decouple max_q_size from n_clients during the start phase.

    for i in xrange(n_clients):
        client = Client(i, base_url, wget_interval)
        client.start()
        clients.append(client)
        time.sleep(client_interval)
    
    while True:
        try:
            if queue.qsize() > q_size:
                print 'max queue size exceeded!'
                raise KeyboardInterrupt
                
            if not queue.empty():
                print ','.join([time.ctime(time.time()), str(queue.qsize())])
                cid, cur_url, task_id = queue.get()
                wget = Getter(cur_url, ofile=ofile)
                wget.start()
                queue.task_done()                
                clients[cid].completed_task += 1 # see TODO on completed_task
            else:
                print ','.join([time.ctime(time.time()), '0'])
                time.sleep(1)

        except KeyboardInterrupt:
            print 'interrupted...'
            for client in clients:
                client.stopped = True
            threads = [c.join(1) for c in clients if c is not None and c.isAlive()]
            print 'clients stopped'
            while not queue.empty():
                queue.get()
                queue.task_done()
            print 'queue emptied'
            print 'bye!\n'
            sys.exit()
            #os._exit(0) # good: always terminates; bad: don't know the consequences