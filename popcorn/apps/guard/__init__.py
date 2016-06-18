import sys
import Pyro4
from popcorn.apps.hub import Machine
import time
import subprocess
import socket
from celery import bootsteps
from popcorn.rpc.pyro import RPCClient
import psutil
from collections import defaultdict
from popcorn.apps.utils import taste_soup


class Guard(object):
    class Blueprint(bootsteps.Blueprint):
        """Hub bootstep blueprint."""
        name = 'Guard'
        default_steps = set([
            'popcorn.rpc.pyro:RPCClient',
            'popcorn.apps.guard:Register',
            'popcorn.apps.guard:Loop',
        ])

    def __init__(self, app):
        self.app = app or self.app
        self.steps = []
        self.id = self.get_id()
        self.blueprint = self.Blueprint(app=self.app)
        self.blueprint.apply(self)
        self.processes = defaultdict(list)
        self.machine = Machine(self.id)
        self.machine.update_stats(self.machine_info)
        # queue:[] worker process list

    def qsize(self, queue):
        return taste_soup(queue, self.app.conf['BROKER_URL'])

    def get_id(self):
        name = socket.gethostname()
        ip = socket.gethostbyname(name)
        return '%s@%s' % (name, ip)

    def start(self):
        self.blueprint.start(self)

    def loop(self, rpc_client):
        while True:
            try:
                order = self.get_order(rpc_client)
                if order:
                    print '[Guard] get order: %s' % str(order)
                    self.follow_order(order)
                time.sleep(5)
                self.clear_worker()
            except Pyro4.errors.ConnectionClosedError:
                print "Hub server is closed, guard will be close"
                sys.exit(1)
            except Exception:
                import traceback
                traceback.print_exc()

    def enroll(self, rpc_client):
        try:
            res = rpc_client.start_with_return('popcorn.apps.hub:hub_enroll', id=self.id)
            if not res:
                print "Failed to enroll: %s" % self.id
                sys.exit(1)
        except Pyro4.errors.CommunicationError:
            print "Hub server can not be connected, guard will be close"
            sys.exit(1)

    def unregister(self):
        res = self.rpc_client.start_with_return('popcorn.apps.hub:hub_unregister', id=self.id)
        print "Unregister result is %s" % res


    def get_order(self, rpc_client):
        self.machine.update_stats(self.machine_info)
        return rpc_client.start_with_return('popcorn.apps.hub:hub_send_order',
                                            id=self.id,
                                            stats=self.machine_info)

    @property
    def machine_info(self):
        print '[Guard] collect info:  CUP IDLE%s%%' % self.cpu_percent.idle
        rdata = {'memory': self.memory,
                 'cpu': self.cpu_percent,
                 'workers': self.worker_stats}
        return rdata

    def follow_order(self, order):
        for queue, worker_number in order.iteritems():
            print '[Guard] Queue[%s], Workers [%2d]' % (queue, worker_number)
            # self.add_worker(queue, worker_number) if worker_number is delta, use this method
            if self.qsize(queue) == 0:
                print '[Guard] Queue[%s].size ==0 , Clear Workers' % queue
                self.update_worker(queue, 0)
            else:
                self.update_worker(queue, worker_number)

    def update_worker(self, queue, worker_number):
        plist = self.processes[queue]
        delta = worker_number - len(plist)
        if delta > 0:
            self.add_worker(queue, delta)

    def clear_worker(self):
        for queue in self.processes.keys():
            if self.qsize(queue) == 0:
                print '[Guard] Clear Work For Empyt Queue'
                self.add_worker(queue, number=-100)

    def add_worker(self, queue, number=1):
        print '[Guard] Queue[%s], %d Workers' % (queue, number)
        if number > 0:
            for _ in range(number):
                if self.machine.health:
                    print '[Guard] Exec command: %s' % str(['celery', 'worker', '-Q', queue, '-c', '1'])
                    self.processes[queue].append(subprocess.Popen(['celery', 'worker', '-Q', queue, '-c', '1']))
                    time.sleep(1)
                else:
                    print '[Guard] not more resource on this machine'
        elif number < 0:
            for _ in range(abs(number)):
                plist = self.processes[queue]
                if len(plist) >= 1:
                    p = plist.pop()
                    # p.send_signal(2)  # send Ctrl + C to subprocess
                    p.terminate()  # send Ctrl + C to subprocess
                    p.wait()  # wait this process quit
                else:
                    # no more workers
                    return

    @property
    def memory(self):
        return psutil.virtual_memory()

    @property
    def cpu_percent(self):
        # return psutil.cpu_percent()
        return psutil.cpu_times_percent()

    @property
    def worker_stats(self):
        return {queue: len(plist) for queue, plist in self.processes.items()}


class Register(bootsteps.StartStopStep):
    requires = (RPCClient,)

    def __init__(self, p, **kwargs):
        pass

    def include_if(self, p):
        return True

    def create(self, p):
        p.enroll(p.rpc_client)
        return self

    def start(self, p):
        pass

    def stop(self, p):
        print 'in stop'

    def terminate(self, p):
        print 'in terminate'


class Loop(bootsteps.StartStopStep):
    requires = (Register,)

    def __init__(self, p, **kwargs):
        pass

    def include_if(self, p):
        return True

    def create(self, p):
        return self

    def start(self, p):
        p.loop(p.rpc_client)
        pass

    def stop(self, p):
        print 'in stop'

    def terminate(self, p):
        print 'in terminate'
