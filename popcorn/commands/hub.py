import os
import signal
from popcorn.commands import BaseCommand
from popcorn.apps.hub import Hub, ClientHeartChecker


class HubCommand(BaseCommand):

    def run_from_argv(self, prog_name, argv=None, **_kwargs):
        hub = Hub(self.app)
        heart_checker = ClientHeartChecker(hub)
        heart_checker.start()

        def _exit_handler(sig, stack_frame):
            print 'Trying to stop heart check threading'
            heart_checker.stop_checker()
            os.killpg(os.getpid(), signal.SIGKILL)

        signal.signal(signal.SIGTERM, _exit_handler)
        signal.signal(signal.SIGINT, _exit_handler)
        signal.signal(signal.SIGUSR1, _exit_handler)
        hub.start()

    def handle_argv(self, prog_name, argv=None):
        return self.run_from_argv(prog_name, argv)
