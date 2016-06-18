#!/usr/bin/env python
from setuptools import setup, find_packages

with open('requirements.txt') as requirements:
    requires = [i.split('=')[0].strip() for i in requirements.readlines() if i]


setup(
    name='popcorn',
    version='0.1',
    description='Celery Popcorn',
    long_description=open('README.rst').read(),
    url='https://github.com/demien-aa/popcorn',
    license='BSD',
    packages=find_packages(exclude=('tests', 'tests.*')),
    install_requires=requires,
    entry_points={
        'console_scripts': [
            'popcorn = popcorn.__main__:main',
        ],
        'celery.commands': [
            'guard = popcorn.commands.guard:GuardCommand',
            'hub = popcorn.commands.hub:HubCommand',
            'planner = popcorn.commands.planner:PlannerCommand',
        ],
    },
)
