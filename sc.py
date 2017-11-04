#!/usr/bin/env python3

import schoolopy
import yaml
from termcolor import colored as c
from os.path import expanduser
import sys
import re
from datetime import datetime
from random import choice

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
    # TODO: Get this automatically
    cfg['me'] = int(input('User ID: '))
    cfg['limit'] = 10
    cfg['accent'] = 'cyan'
    with open(CONFIG, 'w+') as f:
        yaml.dump(cfg, f)

if cfg['accent'] == 'random':
    cfg['accent'] = choice(['grey', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan'])  # White skipped

api = schoolopy.Schoology(cfg.get('key'), cfg.get('secret'))
api.limit = cfg['limit']


def date(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y/%m/%d, %H:%M:%S')

def display(data):
    if isinstance(data, list):  # data is a list of objects to show
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
                print(c(user.name_display, cfg['accent']), end='')
                print(' / ' + update.body[:75-(len(user.name_display)+3)].replace('\r\n', ' ').replace('\n', ' ') + '... / ', end='')
                print(c('%dL' % update.likes, 'yellow'))
        elif isinstance(data[0], schoolopy.Group):
            for group in data:
                print(c(group.title, cfg['accent']))
        elif isinstance(data[0], schoolopy.Section):
            for section in data:
                # TODO: Print other data points
                print(c(section.title, cfg['accent']))
    else:  # data is scalar object
        if isinstance(data, schoolopy.Update):
            user = api.get_user(data.uid)
            fields = ['By', 'Date']
            contents = [user.name_display, date(data.created)]
            for field, content in zip(fields, contents):
                print(c(field + ':', cfg['accent']) + ' ' + content)
            print('\n%s\n' % data.body)
            print(c('👍  %d Likes' % data.likes, 'yellow'))
        elif isinstance(data, schoolopy.Group):
            group = api.get_group(data.id)
            print(group)
            return
            fields = ['By', 'Date']
            contents = [user.name_display, date(data.created)]
            for field, content in zip(fields, contents):
                print(c(field + ':', cfg['accent']) + ' ' + content)
            print('\n%s\n' % data.body)
            print(c('👍  %d Likes' % data.likes, 'yellow'))
        elif isinstance(data, schoolopy.User):
            fields = ['Name', 'Email', 'Graduation Year', 'Location', 'Language']
            contents = ['%s (%s)' % (data.name_display, data.school_uid), data.primary_email, data.grad_year, data.tz_name, data.language]
            for field, content in zip(fields, contents):
                print(c(field + ':', cfg['accent']) + ' ' + content)
        elif isinstance(data, schoolopy.Section):
            pass


many = api.get_feed()
one = None
display(many)

while True:
    try:
        try:
            rawcmd = input('> ')
        except KeyboardInterrupt:
            print()
            continue

        try:
            cmd = re.search(r'^(\w+)', rawcmd).group(0)
            content = rawcmd[len(cmd)+1:].split(' ')
        except AttributeError:
            cmd = None
            content = None
        #print('RECIEVED: %s, %s' % (cmd, content))

        if cmd == 'view':
            try:
                one = many[int(content[0])]
            except IndexError:
                one = many[0]
            display(one)
        elif cmd == 'list':
            if content[0] == 'groups':
                many = api.get_user_groups(cfg['me'])
                display(many)
            elif content[0] == 'courses':
                many = api.get_user_sections(cfg['me'])
                display(many)
        elif cmd == 'home':
            many = api.get_feed()
            display(many)
        elif cmd == 'me':
            one = api.get_me()
            display(one)
        elif cmd == 'user':
            one = api.get_user(content[0])
            display(one)
        elif cmd == 'req':
            exec('print(api.%s)' % ''.join(content))

    except EOFError:
        print()
        sys.exit(0)
