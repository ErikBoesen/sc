#!/usr/bin/env python3

import schoolopy
import yaml
from termcolor import colored as c
from os.path import expanduser
import sys
import re
from datetime import datetime

CONFIG = expanduser('~') + '/.sc.yaml'

cfg = {}
# TODO: Handle config which exists, but lacks necessary fields
# TODO: Make this more efficient
try:
    with open(CONFIG, 'r+') as f:
        cfg = yaml.load(f.read())
except FileNotFoundError:
    cfg = {}
if not cfg:
    from getpass import getpass

    print(c('Generating configuration for first run.', 'green'))
    cfg = {}
    cfg['key'] = input('API key: ')
    cfg['secret'] = getpass('API secret: ')
    with open(CONFIG, 'w+') as f:
        yaml.dump(cfg, f)


# TODO: Unsure of naming of `api`
api = schoolopy.Schoology(cfg.get('key'), cfg.get('secret'))

def date(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y/%m/%d, %H:%M:%S')

def display(data):
    if isinstance(data, list): # data is a list of objects to show
        if isinstance(data[0], schoolopy.Update):
            users = []
            # TODO: Switch to multi-get request once it's available
            # TODO: Generalize loading system
            for i, update in enumerate(data):
                sys.stdout.write('\r%s %s/%s' % ('/-\\|'[i % 4], i, len(data)))
                sys.stdout.flush()
                users.append(api.get_user(update.uid))

            sys.stdout.write('\r')
            for user, update in zip(users, data):
                print(c(user.name_display, 'red'), end='')
                print(' / ' + update.body[:40].replace('\r\n', ' ').replace('\n', ' ') + '... / ', end='')
                print(c('%dL' % update.likes, 'yellow'))
        elif isinstance(data[0], schoolopy.Group):
            pass
        elif isinstance(data[0], schoolopy.Section):
            pass
    else: # data is scalar object
        if isinstance(data, schoolopy.Update):
            user = api.get_user(data.uid)
            fields = ['By', 'Date']
            contents = [user.name_display, date(data.created)]
            for field, content in zip(fields, contents):
                print(c(field + ':', 'red') + ' ' + content)
            print()
            print(data.body)
            print(c(data.likes, 'yellow'))
        elif isinstance(data, schoolopy.Group):
            pass
        elif isinstance(data, schoolopy.User):
            pass

shown = api.get_feed()
display(shown)

while True:
    try:
        rawcmd = input('> ')
        try:
            cmd = re.search(r'^(\w+)', rawcmd).group(0)
            content = rawcmd[len(cmd)+1:].split(' ')
        except AttributeError:
            cmd = None
            content = None
        print('RECIEVED: %s, %s' % (cmd, content))

        if cmd == 'view':
            display(shown[int(content[0])])
        elif cmd == 'home':
            pass

    except EOFError:
        print()
        sys.exit(0)
