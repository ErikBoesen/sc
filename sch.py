#!/usr/bin/env python3

import schoolopy
import yaml
from termcolor import colored as c
from os.path import expanduser
import sys
import argparse

CONFIG = expanduser('~') + '/.sch.yaml'

class SCH:
    cfg = {}
    def __init__(self):
        # TODO: Handle config which exists, but lacks necessary fields
        # TODO: Make this more efficient
        with open(CONFIG, 'r+') as f:
            self.cfg = yaml.load(f.read())
        if not self.cfg:
            print(c('No configuration detected. Run sch config to generate config file.', 'red'))

        # TODO: Unsure of naming of `api`
        self.api = schoolopy.Schoology(self.cfg['key'], self.cfg['secret'])

    def genconfig(self):
        from getpass import getpass

        print(c('Generating configuration for first run.', 'green'))
        self.cfg = {}
        self.cfg['key'] = input('API key: ')
        self.cfg['secret'] = getpass('API secret: ')
        print(self.cfg)
        with open(CONFIG, 'w+') as f:
            yaml.dump(self.cfg, f)

    def home(self):
        updates = self.api.get_feed()
        users = []
        # TODO: Switch to multi-get request once it's available
        # TODO: Generalize loading system
        for i,update in enumerate(updates):
            sys.stdout.write('\r%s %s/%s' % ('/-\\|'[i%4], i, len(updates)))
            sys.stdout.flush()
            users.append(self.api.get_user(update.uid))

        sys.stdout.write('\r')
        for user,update in zip(users,updates):
            print(c(user.name_display, 'red'), end='')
            print(' / ' + update.body[:40].replace('\r\n', ' ').replace('\n', ' ') + '... / ', end='')
            print(c('%dL' % update.likes, 'yellow'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Schoology in the terminal.')
    parser.add_argument('command', type=str, nargs='?', help='What you want to do (home, config).')

    args = parser.parse_args()

    sch = SCH()


    if not args.command or args.command == 'home':
        sch.home()
    elif args.command.startswith('config'):
        sch.genconfig()
    else:
        print('Unknown command %s.' % args.command)
