#!/usr/bin/env python3

import schoolopy
import yaml
from termcolor import colored as c
from os.path import expanduser
import sys
import re
from datetime import datetime

CONFIG_PATH = expanduser('~') + '/.sc.yaml'

cfg = {}
# TODO: Handle config which exists, but lacks necessary fields
# TODO: Make this more efficient
try:
    with open(CONFIG_PATH, 'r+') as f:
        cfg = yaml.load(f.read())
except FileNotFoundError:
    cfg = {}
if not cfg:
    from getpass import getpass

    print(c('Generating configuration for first run.', 'green'))
    cfg = {
        'key': input('API key: '),
        'secret': getpass('API secret: '),
        # TODO: Get this automatically
        'me': int(input('User ID: ')),
        'limit': 10,
        'accent': 'cyan',
    }
    with open(CONFIG_PATH, 'w') as f:
        yaml.dump(cfg, f)

api = schoolopy.Schoology(schoolopy.Auth(cfg['key'], cfg['secret']))
api.limit = cfg['limit']


def date(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y/%m/%d, %H:%M:%S')

def listprop(fields, contents):
    for field, content in zip(fields, contents):
        print(c(field + ':', cfg['accent']) + ' %s' % content)

def load_users(data, key='uid'):
    users = []
    # TODO: Switch to multi-get request once it's available
    for i, datum in enumerate(data):
        sys.stdout.write('\r%s %s/%s' % ('/-\\|'[i % 4], i, len(data)))
        sys.stdout.flush()
        users.append(api.get_user(datum[key]))
    sys.stdout.write('\r')
    return users


def display(data):
    if isinstance(data, list):  # data is a list of objects to show
        if isinstance(data[0], schoolopy.Update):
            users = load_users(data)
            for user, update in zip(users, data):
                print(c(user.name_display if user.name_display else '%s %s' % (user.name_first, user.name_last), cfg['accent']), end='')
                print(' / ' + update.body[:75-(len(user.name_display)+3)].replace('\r\n', ' ').replace('\n', ' ') + '... / ', end='')
                print(c('%dL' % update.likes, 'yellow'))
        elif isinstance(data[0], schoolopy.Group):
            for group in data:
                print(c(group.title + (c('*', 'yellow') if group.admin else ''), cfg['accent']))
        elif isinstance(data[0], schoolopy.Section):
            for section in data:
                display(section)
        elif isinstance(data[0], schoolopy.MessageThread):
            users = load_users(data, key='author_id')
            for user, thread in zip(users, data):
                print(c(user.name_display, cfg['accent']), end='')
                print(' / ' + thread.subject)
                if thread.message_status == 'unread':
                    print(c('*', yellow))
    else:  # data is scalar object
        if isinstance(data, schoolopy.Update):
            user = api.get_user(data.uid)
            listprop(['By', 'Date'],
                     [user.name_display, date(data.created)])
            print('\n%s\n' % data.body)
            print(c('👍  %d Likes' % data.likes, 'yellow'))
        elif isinstance(data, schoolopy.Group):
            group = api.get_group(data.id)
            listprop(['Title', 'Admin', 'Description', 'Category'],
                     [group.title, group.admin == 1, group.description, group.category])
        elif isinstance(data, schoolopy.User):
            listprop(['Name', 'Email', 'Graduation Year', 'Location', 'Language'],
                     ['%s (%s)' % (data.name_display, data.school_uid), data.primary_email, data.grad_year, data.tz_name, data.language])
        elif isinstance(data, schoolopy.Section):
            listprop(['Name', 'Section'],
                     [data.course_title, data.section_title])
        elif isinstance(data, schoolopy.MessageThread):
            messages = api.get_message(data.id)
            users = {message.author_id: api.get_user(message.author_id) for message in messages}
            author = api.get_user(data.author_id)
            listprop(['Subject', 'Author', 'Time', 'Status'],
                     [data.subject, author.name_display, date(data.last_updated), data.message_status])
            print()
            for message in messages:
                print(('' if message.message_status == 'read' else c('* ', 'yellow')) + c(users[message.author_id].name_display, cfg['accent']) + ' / ' + c(date(message.last_updated), cfg['accent']) + ' / ' + message.message)


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
            elif content[0] == 'messages':
                many = api.get_inbox_messages()
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
        elif cmd == '':
            pass
        else:
            print('Unrecognized command.')

    except EOFError:
        print()
        sys.exit(0)
