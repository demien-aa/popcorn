from popcorn.commands import BaseCommand
import time
import logging
from celery import bootsteps
from celery.utils.imports import instantiate
from multiprocessing import Process
from popcorn.apps.constants import TIME_SCALE, INTERVAL
from popcorn.apps.hub import Hub
from popcorn.apps.utils.broker_util import taste_soup
from popcorn.rpc.pyro import RPCClient

logger = logging.getLogger(__name__)


STRATEGY_MAP = {
    'simple': 'popcorn.apps.planner.strategy.SimpleStrategy:SimpleStrategy'
}


class RegisterPlanner(object):

    class Blueprint(bootsteps.Blueprint):

        """Hub bootstep blueprint."""
        name = 'RegisterPlanner'
        default_steps = set([
            'popcorn.rpc.pyro:RPCClient',
            'popcorn.apps.planner:Register',
        ])

    def __init__(self, app, queue, strategy_name):
        self.app = app or self.app
        self.steps = []
        self.blueprint = self.Blueprint(app=self.app)
        self.queue = queue
        self.strategy_name = strategy_name
        self.blueprint.apply(self)

    def start(self):
        self.blueprint.start(self)


class Planner(object):

    class Blueprint(bootsteps.Blueprint):

        """Hub bootstep blueprint."""
        name = 'Planner'
        default_steps = set([
            'popcorn.rpc.pyro:RPCClient',
            'popcorn.apps.planner:Strategy',
            'popcorn.apps.planner:Loop',
        ])

    def __init__(self, app, queue, strategy_name):
        self.app = app or self.app
        self.steps = []
        self.blueprint = self.Blueprint(app=self.app)
        self.queue = queue
        self.strategy_name = strategy_name
        self.blueprint.apply(self)

    def start(self):
        self.blueprint.start(self)

    def plan(self):
        while True:
            previous_timestampe = int(round(time.time() * TIME_SCALE))
            previous_status = taste_soup(self.queue, self.app.conf['BROKER_URL'])
            time.sleep(INTERVAL)
            timestampe = int(round(time.time() * TIME_SCALE))
            status = taste_soup(self.queue, self.app.conf['BROKER_URL'])
            result = self.strategy.apply(
                previous_status=previous_status,
                previous_time=previous_timestampe,
                status=status,
                time=timestampe
            )
            plan = {self.queue: result}
            print '[Planner] Heart beat on queue: %s' % self.queue
            if result:
                print '[Planner] create new plan: %s' % str(plan)
                self.rpc_client.start('popcorn.apps.hub:hub_set_plan', plan=plan)


class Strategy(bootsteps.StartStopStep):

    def __init__(self, p, **kwargs):
        pass

    def include_if(self, p):
        return True

    def create(self, p):
        strategy_cls = STRATEGY_MAP[p.strategy_name]
        p.strategy = instantiate(strategy_cls)
        return self

    def start(self, p):
        pass

    def stop(self, p):
        print 'in stop'

    def terminate(self, p):
        print 'in terminate'


class Loop(bootsteps.StartStopStep):
    requires = (Strategy, RPCClient, )

    def __init__(self, p, **kwargs):
        pass

    def include_if(self, p):
        return True

    def create(self, p):
        self.process = Process(target=p.plan)
        self.process.start()
        return self

    def start(self, p):
        pass

    def stop(self, p):
        print 'in stop'

    def terminate(self, p):
        print 'in terminate'


class Register(bootsteps.StartStopStep):
    requires = (RPCClient, )

    def __init__(self, p, **kwargs):
        pass

    def include_if(self, p):
        return True

    def create(self, p):
        return self

    def start(self, p):
        p.rpc_client.start('popcorn.apps.planner:Planner', app=p.app, queue=p.queue, strategy_name=p.strategy_name)

    def stop(self, p):
        print 'in stop'

    def terminate(self, p):
        print 'in terminate'
