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

    def __init__(self, client_heart_infos):
        super(ClientHeartChecker, self).__init__(name='ClientHeartChecker')
        self.client_list = client_heart_infos
        self.stop = threading.Event()

    def stop_checker(self):
        self.stop.set()

    def check_client_heart(self):
        for clent_info in self.client_list:


    def run(self):
        interval = 5
        while not self.stop.wait(1):
            self.stop.wait(interval)




class Hub(object):

    class Blueprint(bootsteps.Blueprint):

        """Hub bootstep blueprint."""
        name = 'Hub'
        default_steps = set([
            # 'popcorn.apps.hub.components:PlannerServer',
            'popcorn.apps.hub.components:RPCServer',
        ])

    PLAN = defaultdict(int)
    MACHINES = []

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
        for queue, task in Hub.PLAN.iteritems():
            order[queue] = int(task / len(Hub.MACHINES))
        return order

    @staticmethod
    def set_plan(plan):
        Hub.PLAN.update(plan)

    @staticmethod
    def enroll(id):
        if id in Hub.MACHINES:
            print '[Hub] new guard enroll: %s' % id
            Hub.MACHINES.append(id)
            return True
        else:
            print '[Hub] Found existed guard from: %s' % id
            return False

    @staticmethod
    def unregister(id):
        if id in Hub.MACHINES:
            Hub.MACHINES.remove(id)
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
