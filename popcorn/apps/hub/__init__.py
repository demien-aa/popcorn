import time
import math
from celery import bootsteps
import threading
from celery.bootsteps import RUN, TERMINATE
from collections import defaultdict
import os


class ClientHeartChecker(threading.Thread):
    """
    The ProcessChecker is a separate thread that will check all the processes
    of the ProcessManager periodically.
    """

    def __init__(self, hub_server):
        super(ClientHeartChecker, self).__init__(name='ClientHeartChecker')
        self.hub_server = hub_server
        self.stop = threading.Event()

    def stop_checker(self):
        self.stop.set()

    def _loop_client(self):
        for client_id in self.hub_server.MACHINES.keys():
            client_lastest_heart_time = self.hub_server.MACHINES[client_id]
            current_time = time.time()
            if math.ceil(current_time - client_lastest_heart_time) > 10:
                print "[Hub] Found dead client and deleted: %s" % client_id
                del self.hub_server.MACHINES[client_id]

    def check_client_heart(self):
        with self.hub_server.hub_lock:
            if not self.hub_server.MACHINES:
                print "[Hub] Not found any guard client"
            else:
                self._loop_client()

    def run(self):
        interval = 5
        while not self.stop.wait(1):
            self.check_client_heart()
            self.stop.wait(interval)


class Hub(object):

    class Blueprint(bootsteps.Blueprint):
        """Hub bootstep blueprint."""
        name = 'Hub'
        default_steps = set([
            'popcorn.rpc.pyro:RPCServer',  # fix me, dynamic load rpc portal
        ])

    PLAN = defaultdict(int)
    MACHINES = {}
    hub_lock = threading.RLock()

    def __init__(self, app, **kwargs):
        self.app = app or self.app
        self.steps = []
        self.blueprint = self.Blueprint(app=self.app)
        self.blueprint.apply(self, **kwargs)

    def start(self):
        self.blueprint.start(self)

    @staticmethod
    def send_order(id):
        order = defaultdict(int)
        print "[Hub] Got order request from %s" % id
        with Hub.hub_lock:
            for queue, task in Hub.PLAN.iteritems():
                order[queue] = int(task / len(Hub.MACHINES))
            Hub.MACHINES[id] = time.time()
        Hub.clear_plan()
        return order

    @staticmethod
    def clear_plan():
        Hub.PLAN = defaultdict(int)

    @staticmethod
    def set_plan(plan):
        Hub.PLAN.update(plan)

    @staticmethod
    def enroll(id):
        with Hub.hub_lock:
            if id not in Hub.MACHINES:
                print '[Hub] new guard enroll: %s' % id
                Hub.MACHINES[id] = time.time()
                return True
            else:
                print '[Hub] Found existed guard from: %s' % id
                return False

    @staticmethod
    def unregister(id):
        with Hub.hub_lock:
            if id in Hub.MACHINES:
                del Hub.MACHINES[id]
                print '[Hub] Guard exited and delete it from hub server cache'
                return True
            return False


def hub_send_order(id):
    return Hub.send_order(id)


def hub_set_plan(plan=None):
    return Hub.set_plan(plan)


def hub_enroll(id):
    return Hub.enroll(id)


def hub_unregister(id):
    return Hub.unregister(id)
