import hashlib
import os
import sys
from popcorn.rpc.pyro import PyroClient
import time
import subprocess
import socket


class Guard(object):

    def __init__(self):
        self.rpc_client = PyroClient()
        name = socket.gethostname()
        ip = socket.gethostbyname(name)
        self.id = '%s@%s' % (name, ip)

    def start(self):
        self.enroll()

        while True:
            self.collect_machine_info()
            order = self.get_order()
            print '[Guard] get order: %s' % str(order)
            self.follow_order(order)
            time.sleep(5)

    def enroll(self):
        res = self.rpc_client.start_with_return('popcorn.apps.hub:hub_enroll', id=self.id)
        if not res:
            print "Failed to enroll: %s" % self.id
            sys.exit(1)

    def unregister(self):
        res = self.rpc_client.start_with_return('popcorn.apps.hub:hub_unregister', id=self.id)
        print "Unregister result is %s" % res

    def get_order(self):
        return self.rpc_client.start_with_return('popcorn.apps.hub:hub_send_order', id=self.id)

    def collect_machine_info(self):
        print '[Guard] collect info:  CUP 90%'

    def follow_order(self, order):
        for queue, concurrency in order.iteritems():
            if concurrency <= 0:
                continue
            concurrency = 10 if concurrency > 10 else concurrency
            cmd = 'celery worker -Q %s -c %s' % (queue, concurrency)
            print '[Guard] exec command: %s' % cmd
            subprocess.Popen(cmd.split(' '))
