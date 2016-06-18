import abc
from celery.utils.imports import instantiate


class BaseRPCServer(object):

    __metaclass__ = abc.ABCMeta

    def start(self):
        raise NotImplementedError()


class BaseRPCClient(object):

    __metaclass__ = abc.ABCMeta

    def start(self, func_path):
        raise NotImplementedError()


class RPCDispatcher(object):

    def dispatch(self, func_path, *args, **kwargs):
        # print("[RPC Client] Send request %s" % func_path)
        instantiate(func_path, **kwargs)

    def dispatch_with_return(self, func_path, *args, **kwargs):
        # print("[RPC Client] Send request %s" % func_path)
        return instantiate(func_path, **kwargs)
