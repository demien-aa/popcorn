import Pyro4
import socket
from celery import bootsteps
from popcorn.rpc import DISPATHCER_SERVER_NAME, PORT, get_uri
from popcorn.rpc.base import BaseRPCServer, BaseRPCClient, RPCDispatcher


class PyroServer(BaseRPCServer):

    def __init__(self, **kwargs):
        ip = self.get_ip()
        port = PORT
        Pyro4.config.SERIALIZER = 'pickle'
        self.daemon = Pyro4.Daemon(host=ip, port=port)  # make a Pyro daemon

    def _register(self):
        uri = self.daemon.register(RPCDispatcher, DISPATHCER_SERVER_NAME)   # register the greeting maker as a Pyro object
        print '[RPC Server] Register Uri %s' % uri

    def start(self):
        self._register()
        self.daemon.requestLoop()                   # start the event loop of the server to wait for calls

    def get_ip(self):
        host = socket.gethostname()
        return socket.gethostbyname(host)


class PyroClient(BaseRPCClient):

    def __init__(self, server, ip, port):
        uri = get_uri(server, ip, port)
        print '[RPC Client] connection server %s' % uri
        self.rpc_client = Pyro4.Proxy(uri)    # use name server object lookup uri shortcut

    def start(self, func_path, *args, **kwargs):
        Pyro4.config.SERIALIZER = 'pickle'
        self.rpc_client.dispatch(func_path, *args, **kwargs)

    def start_with_return(self, func_path, *args, **kwargs):
        return self.rpc_client.dispatch_with_return(func_path, *args, **kwargs)



class RPCServer(bootsteps.StartStopStep):

    def __init__(self, h, **kwargs):
        h.test = None

    def include_if(self, h):
        return True

    def create(self, h):
        self.rpc_server = PyroServer()  # fix me. Load rpc implementation dynamiclly
        return self

    def start(self, h):
        self.rpc_server.start()

    def stop(self, h):
        print 'in stop'

    def terminate(self, h):
        print 'in terminate'


class RPCClient(bootsteps.StartStopStep):

    def __init__(self, p, **kwargs):
        pass

    def include_if(self, p):
        return True

    def create(self, p):
        server = DISPATHCER_SERVER_NAME
        port = PORT
        ip = p.app.conf['HUB_IP']
        p.rpc_client = PyroClient(server, ip, port)
        return self

    def start(self, p):
        pass

    def stop(self, h):
        print 'in stop'

    def terminate(self, h):
        print 'in terminate'
