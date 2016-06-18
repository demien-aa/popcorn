import os
import signal

from popcorn.commands import BaseCommand
from popcorn.apps.guard import Guard


class GuardCommand(BaseCommand):

    def run_from_argv(self, prog_name, argv=None, **_kwargs):
        guard_obj = Guard(self.app)

        def _exit_handler(sig, stack_frame):
            guard_obj.unregister()
            os.killpg(os.getpid(), signal.SIGKILL)

        signal.signal(signal.SIGTERM, _exit_handler)
        signal.signal(signal.SIGINT, _exit_handler)
        signal.signal(signal.SIGUSR1, _exit_handler)

        guard_obj.start()
