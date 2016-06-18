import os
import signal

from popcorn.commands import BaseCommand
from popcorn.apps.guard import Guard


def exit_handler(sig, stack_frame):
    Guard().unregister()
    os.killpg(os.getpid(), signal.SIGKILL)


signal.signal(signal.SIGTERM, exit_handler)
signal.signal(signal.SIGINT, exit_handler)
signal.signal(signal.SIGUSR1, exit_handler)

class GuardCommand(BaseCommand):

    def run_from_argv(self, prog_name, argv=None, **_kwargs):
        Guard().start()
