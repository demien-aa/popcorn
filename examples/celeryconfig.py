import os

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERYD_POOL_RESTARTS = True
CELERY_IMPORTS = (
    "tasks",
)

HUB_IP = '192.168.1.52'
BROKER_URL = 'redis://%s:6379/0' % HUB_IP

ROOT = os.path.abspath(os.path.dirname(__file__))

if os.path.exists(os.path.join(ROOT, "celeryconfig_local.py")):
    execfile(os.path.join(ROOT, "celeryconfig_local.py"))
