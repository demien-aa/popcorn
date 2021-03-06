# from mock import MagicMock, Mock
import mock
from popcorn.utils import ip

default_queues = {
    'q1': {
        'strategy': 'simple',
    },
    'q2': {
        'strategy': 'simple',
    }
}


class PickableMock(mock.MagicMock):
    def __reduce__(self):
        return (mock.MagicMock, ())


class Foo(object):
    pass


class Config(object):

    find_value_for_key = PickableMock()

    def __init__(self, config):
        self.config = config
    
    def __getitem__(self, key):
        return self.config.get(key, '')

    def get(self, key, default=None):
        return self.config.get(key, default)


class App(object):
    log = Foo()

    conf = Config({
        'DEFAULT_QUEUE': default_queues,
        'BROKER_URL': '127.0.0.1',
        'HUB_IP': ip(),
        'HEALTHY_MOCK': True,
    })

    def __init__(self):
        self.log.setup = PickableMock()


class Pool(object):

    @property
    def pinfo(self):
        return {}
