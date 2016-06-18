import sys
from popcorn.commands import BaseCommand
from popcorn.rpc.pyro import PyroClient
from celery.bin.base import Option
from popcorn.apps.planner import RegisterPlanner


class PlannerCommand(BaseCommand):

    def run_from_argv(self, prog_name, argv=None, command=None):
        command = sys.argv[0] if command is None else command
        argv = sys.argv[1:] if argv is None else argv
        options, args = self.prepare_args(*self.parse_options(prog_name, argv, command))

        planner = RegisterPlanner(self.app, queue=options['queue'], strategy_name=options['strategy'])
        planner.start()

    def get_options(self):
        return (
            Option('-Q', '--queue'),
            Option('-S', '--strategy', default='simple')
        )
