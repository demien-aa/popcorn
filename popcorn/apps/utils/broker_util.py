from kombu import Connection
from celery.task.control import inspect

def taste_soup(queue, broker_url):
    try:
        with Connection(broker_url) as conn:
            q = conn.SimpleQueue(queue)
            return q.qsize()
    except Exception as e:
        return 0
