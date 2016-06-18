import hashlib
import os
import sys
import Pyro4
from popcorn.rpc.pyro import PyroClient
import time
import subprocess
import socket
from celery import bootsteps
from popcorn.rpc.pyro import RPCClient


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

    def get_id(self):
        name = socket.gethostname()
        ip = socket.gethostbyname(name)
        return '%s@%s' % (name, ip)

    def start(self):
        self.blueprint.start(self)

    def loop(self, rpc_client):
        while True:
            print '[Guard] Heart beat %s' % self.id
            try:
                self.collect_machine_info()
                order = self.get_order(rpc_client)
                if order:
                    print '[Guard] get order: %s' % str(order)
                    self.follow_order(order)
                time.sleep(5)
            except Pyro4.errors.ConnectionClosedError:
                print "Hub server is closed, guard will be close"
                sys.exit(1)


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
        return rpc_client.start_with_return('popcorn.apps.hub:hub_send_order', id=self.id)

    def collect_machine_info(self):
        print '[Guard] collect info:  CUP 90%'

    def follow_order(self, order):
        for queue, concurrency in order.iteritems():
            if concurrency <= 0:
                continue
            cmd = 'celery worker -Q %s --autoscale=%s,1' % (queue, concurrency)
            print '[Guard] exec command: %s' % cmd
            subprocess.Popen(cmd.split(' '))


class Register(bootsteps.StartStopStep):
    requires = (RPCClient, )

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
    requires = (Register, )

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
