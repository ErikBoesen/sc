import schoolopy
import yaml
from termcolor import colored as c

with open('example_config.yml', 'r') as f:
    cfg = yaml.load(f)

sc = schoolopy.Schoology(cfg['key'], cfg['secret'])

for update in sc.get_feed():
    user = sc.get_user(update.uid)
    print(c(user.name_display, 'red'), end='')
    print(' / ' + update.body[:40].replace('\r\n', ' ').replace('\n', ' ') + '... / ', end='')
    print(c('%d likes' % update.likes, 'yellow'))
