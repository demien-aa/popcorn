import time
import math
from celery import bootsteps
import threading
from collections import defaultdict


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
            client_lastest_heart_time = self.hub_server.MACHINES[client_id].latest_heart
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


class Machine(object):
    RECORD_NUMBER = 100

    _CPU_WINDOW_SIZE = 5
    _CPU_THS = 10  # 10 percent
    _MEMORY_THS = 500 * 1024 ** 2  # if remain memeory < this number , not start more worker

    def __init__(self, id):
        self.id = id
        self._original_stats = []
        self._plan = defaultdict(int)
        self.latest_heart = time.time()

    def update_stats(self, stats):
        print '[Machine] %s cpu:%s , memory:%s MB' % (self.id, self.cpu, self.memory / 1024 ** 2)
        self._original_stats.append(stats)
        if len(self._original_stats) > self.RECORD_NUMBER:
            self._original_stats.pop(0)

    @property
    def memory(self):
        if self._original_stats:
            print '******'
            print self._original_stats[-1]['memory']
            return self._original_stats[-1]['memory'].available
        else:
            return self._MEMORY_THS + 100

    @property
    def cpu(self):
        if len(self._original_stats) >= self._CPU_WINDOW_SIZE:
            # return sum([i['cpu'].idle for i in self._original_stats[-self._CPU_WINDOW_SIZE:]]) / float(
            #     self._CPU_WINDOW_SIZE)
            if sum([1 for i in self._original_stats[-self._CPU_WINDOW_SIZE:] if i['cpu'].idle < 5]) > 1:
                return 100
            else:
                return 0
        else:
            return 50

    @property
    def health(self):
        return self.cpu >= self._CPU_THS and self.memory >= self._MEMORY_THS

    def get_worker_number(self, queue):
        return self._plan[queue]

    def current_worker_number(self, queue):
        return 1

    def plan(self, *queues):
        return {queue: self.get_worker_number(queue) for queue in queues}
        # import random
        # return {'pop': random.randint(1, 6)}

    # def update_plan(self, queue, worker_number):
    #     if self.health:
    #         support = self.memory / 100 * 1024 ** 2
    #         if worker_number <= support:
    #             self._plan[queue] = worker_number
    #         else:
    #             self._plan[queue] = support
    #     print '[Machine] %s take %d workers' % (self.id, self._plan.get(queue, 0))
    #     return self._plan[queue]  # WARNING should always return workers you take in

    def add_plan(self, queue, worker_number):
        self._plan[queue] += worker_number

    def clear_plan(self):
        self._plan = defaultdict(int)


class Task(object):
    memory_consume = 0

    def __init__(self):
        pass

        # @property
        # def memory_consume(self):
        #     """
        #     :return: int, maximum bytes this task need
        #     50MB for current demo
        #     """
        #     return 50 * 1024 ** 2


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
    def send_order(id, stats):
        try:
            with Hub.hub_lock:
                machine = Hub.MACHINES.get(id, Machine(id))
                machine.latest_heart = time.time()
                Hub.MACHINES[id] = machine
                machine.update_stats(stats)
                if filter(lambda a: a != 0, Hub.PLAN.values()):
                    print "[Hub] Analyze Queue plan:", Hub.PLAN
                    for queue, worker_number in Hub.PLAN.iteritems():
                        Hub.PLAN[queue] = Hub.load_balancing(queue, worker_number)
                    machine_plan = machine.plan(*Hub.PLAN.keys())
                    print "[Hub] Create machine %s plan %s" % (str(id), str(machine_plan))
                    machine.clear_plan()
                    if filter(lambda a: a != 0, machine_plan.values()):
                        print "[hub] Plan machine:", id, machine_plan
                    return machine_plan
        except Exception as e:
            import traceback
            traceback.print_exc()
            print e
            return {}
        return {}

    def get_worker_number(self, queue):
        # get numbers we need
        return 10

    @staticmethod
    def clear_plan():
        Hub.PLAN = defaultdict(int)

    @staticmethod
    def set_plan(plan):
        if filter(lambda a: a != 0, plan.values()):
            Hub.PLAN.update(plan)

    @staticmethod
    def enroll(id):
        with Hub.hub_lock:
            if id not in Hub.MACHINES:
                print '[Hub] new guard enroll: %s' % id
                Hub.MACHINES[id] = Machine(id)
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

    @staticmethod
    def load_balancing(queue, worker_number):
        with Hub.hub_lock:
            remain_worker = 0
            while worker_number > 0:
                for id, machine in Hub.MACHINES.items():
                    if machine.health:
                        machine.add_plan(queue, 1)
                        worker_number -= 1
                    else:
                        print "Machine >>> unhealth"
                if not [machine for machine in Hub.MACHINES.values() if machine.health]:
                    print '[Hub] warning , remain %d workers' % worker_number
                    remain_worker = worker_number
                    return remain_worker
            for machine in Hub.MACHINES.values():
                if machine._plan[queue]:
                    print '[Machine] load balance: %s take %d workers' % (machine.id, machine._plan[queue])
            return remain_worker


def hub_send_order(id, stats):
    """
    :param id:
    :param stats: dict contains memory & cpu use
    :return:
    """
    return Hub.send_order(id, stats=stats)



def hub_set_plan(plan=None):
    return Hub.set_plan(plan)


def hub_enroll(id):
    return Hub.enroll(id)


def hub_unregister(id):
    return Hub.unregister(id)
