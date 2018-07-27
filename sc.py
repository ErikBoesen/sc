#!/usr/bin/env python3

import schoolopy
import json
from termcolor import colored as c
import os
from datetime import datetime

HOME = os.getenv('HOME')
TOKENS_PATH = HOME + '/.sc.tokens.json'
CONFIG_PATH = HOME + '/.sc.config.json'
CACHES_PATH = HOME + '/.sc.caches.json'

# Load or generate API tokens
if os.path.isfile(TOKENS_PATH):
    with open(TOKENS_PATH, 'r') as f:
        tokens = json.load(f)
else:
    from getpass import getpass

    print(c('Logging in.', 'green'))
    print(c('Obtain tokens at [your institution\'s Schoology root]/api.', 'green'))
    tokens = {
        'key': input('API key: '),
        'secret': getpass('API secret: '),
    }
    with open(TOKENS_PATH, 'w') as f:
        json.dump(tokens, f)

# API Initialization
api = schoolopy.Schoology(schoolopy.Auth(tokens['key'], tokens['secret']))

# Load or generate sc configuration
if os.path.isfile(CONFIG_PATH):
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
else:
    config = {
        'me': api.get_me()['uid'],
        'limit': 10,
        'accent': 'cyan',
    }
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)

# Set API properties retrieved from config
api.limit = config['limit']

# Load or generate data caches
if os.path.isfile(CACHES_PATH):
    with open(CACHES_PATH, 'r') as f:
        cache = json.load(f)
else:
    cache = {
        'users': {},
    }
    # Write at end: changes are made throughout.

def date(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y/%m/%d %H:%M:%S')

def listprop(fields, contents):
    for field, content in zip(fields, contents):
        print(c(field + ':', config['accent']) + ' %s' % content)

def load_users(data, key='uid'):
    users = []
    # TODO: Switch to multi-get request once it's available from API
    for i, datum in enumerate(data):
        print('\r%s %s/%s' % ('/-\\|'[i % 4], i, len(data)), end='', flush=True)
        if cache['users'].get(datum[key]):
            # TODO: Caching doesn't work at all.
            #print('user %d in cache' % datum[key])
            user = cache['users'][datum[key]]
        else:
            #print('user %d needs to be fetched' % datum[key])
            user = api.get_user(datum[key])
            cache['users'][datum[key]] = user
        users.append(user)
    print('\r', end='')
    return users


def display(data):
    if isinstance(data, list):  # data is a list of objects to show
        if isinstance(data[0], schoolopy.Update):
            users = load_users(data)
            for user, update in zip(users, data):
                print(c(user.name_display if user.name_display else '%s %s' % (user.name_first, user.name_last), config['accent']), end='')
                print(' / ' + update.body[:75-(len(user.name_display)+3)].replace('\r\n', ' ').replace('\n', ' ') + '... / ', end='')
                print(c('%dL' % update.likes, 'yellow'))
        elif isinstance(data[0], schoolopy.Group):
            for group in data:
                print(c(group.title + (c('*', 'yellow') if group.admin else ''), config['accent']))
        elif isinstance(data[0], schoolopy.Section):
            for section in data:
                display(section)
        elif isinstance(data[0], schoolopy.MessageThread):
            users = load_users(data, key='author_id')
            for user, thread in zip(users, data):
                print(c(user.name_display, config['accent']), end='')
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
                print(('' if message.message_status == 'read' else c('* ', 'yellow')) + c(users[message.author_id].name_display, config['accent']) + ' / ' + c(date(message.last_updated), config['accent']) + ' / ' + message.message)


many = api.get_feed()
one = None
display(many)

while True:
    try:
        try:
            args = input('> ').split()
        except KeyboardInterrupt:
            print()
            continue
        verb = args.pop(0)
        #print('RECIEVED: %s, %s' % (verb, args))

        if verb == 'view':
            try:
                one = many[int(args[0])]
            except IndexError:
                one = many[0]
            display(one)
        elif verb == 'list':
            if args[0] == 'groups':
                many = api.get_user_groups(config['me'])
                display(many)
            elif args[0] == 'courses':
                many = api.get_user_sections(config['me'])
                display(many)
            elif args[0] == 'messages':
                many = api.get_inbox_messages()
                display(many)
        elif verb == 'home':
            many = api.get_feed()
            display(many)
        elif verb == 'me':
            one = api.get_me()
            display(one)
        elif verb == 'user':
            one = api.get_user(content[0])
            display(one)
        elif verb == 'req':
            exec('print(api.%s)' % ''.join(args))
        elif verb == '':
            pass
        else:
            print('Unrecognized command.')

    except EOFError:
        print()
        break

# Write caches to file
with open(CACHES_PATH, 'w') as f:
    json.dump(cache, f)
