import time
import random
import threading


class Cycler(threading.Thread):
    def __init__(self, duty_cycle=0.1):
        threading.Thread.__init__(self)
        self.more = True
        self.state = 0
        self.duty_cycle = duty_cycle
        self._unit_time = 0.05

    def run(self):
        while(self.more):
            x = random.random()
            if x <= self.duty_cycle:
                self.state = 1
            else:
                self.state = 0
            time.sleep(self._unit_time)


if __name__ == '__main__':
    counter = 0

    cycler = Cycler(duty_cycle=0.05)
    cycler.start()

    while True:
        try:
            if cycler.state == 1:
                print('send {}'.format(counter))
                counter += 1
                time.sleep(0.008)
        except KeyboardInterrupt:
            cycler.more = False
            cycler.join(1)
            break
