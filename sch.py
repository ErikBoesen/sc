#!/usr/bin/env python3

import schoolopy
import yaml
from termcolor import colored as c
from os.path import expanduser
import sys
import argparse

CONFIG = expanduser('~') + '/.sch.yaml'

parser = argparse.ArgumentParser(description='Schoology in the terminal.')
parser.add_argument('command', type=str, nargs='?', help='What you want to do (home, config).')
parser.add_argument('id', type=int, nargs='?', help='ID to use in getting data.')
parser.add_argument('--realm', nargs='?', help='Specify the realm to get a resource from.')

args = parser.parse_args()

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

if not args.command or args.command == 'home':
    updates = api.get_feed()
    users = []
    # TODO: Switch to multi-get request once it's available
    # TODO: Generalize loading system
    for i,update in enumerate(updates):
        sys.stdout.write('\r%s %s/%s' % ('/-\\|'[i%4], i, len(updates)))
        sys.stdout.flush()
        users.append(api.get_user(update.uid))

    sys.stdout.write('\r')
    for user,update in zip(users,updates):
        print(c(user.name_display, 'red'), end='')
        print(' / ' + update.body[:40].replace('\r\n', ' ').replace('\n', ' ') + '... / ', end='')
        print(c('%dL' % update.likes, 'yellow'))
elif args.command == 'update':
    update_id = args.id
    realm_type = args.realm[0]
    realm_id = args.realm[1]
    if realm_type == 'section':
        update = api.get_update(update_id, section_id=realm_id)
    elif realm_type == 'group':
        update = api.get_update(update_id, group_id=realm_id)
    elif realm_type == 'user':
        update = api.get_update(update_id, user_id=realm_id)
    user = api.get_user(update.uid)
else:
    print('Unknown command %s.' % args.command)
