CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERYD_POOL_RESTARTS = True
CELERY_IMPORTS = (
    "tasks",
)
HUB_IP = '192.168.1.52'
HUB_IP = '192.168.1.245'
#HUB_IP = '192.168.31.243'
import socket
HUB_IP = socket.gethostbyname(socket.gethostname())

#HUB_IP = '0.0.0.0'
BROKER_URL = 'redis://%s:6379/0' % HUB_IP
