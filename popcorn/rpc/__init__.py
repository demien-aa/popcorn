DISPATHCER_SERVER_NAME = 'popcorn.rpc.server.Dispatcher'
PORT = 9090


def get_uri(server, host, port):
    return 'PYRO:%s@%s:%s' % (server, str(host), str(port))
