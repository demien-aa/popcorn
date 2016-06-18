import time
from celery import task


@task
def add(x, y):
    return x + y


@task
def say(something):
    time.sleep(0.2)


@task
def demo(something):
    time.sleep(0.1)
    from cStringIO import StringIO
    sio = StringIO()
    for i in range(50 * 1024 ** 2):
        sio.write('oo')
    from random import randint
    time.sleep(randint(1, 10))  # waiting io
