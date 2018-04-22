import time
import re
from time import mktime
import datetime
import time
import sys
import json
def exit_gracefully(signal, frame):
	sys.exit(0)

def save_page(html):
	with open('page.html', 'wb') as f:
		f.write(bytes(html, 'utf-8'))

def parse_datetime_moodle(horario):
	return datetime.datetime.fromtimestamp(mktime(time.strptime('-'.join(
		horario.replace('Fev', 'Feb').\
			replace('Abr', 'Apr').\
			replace('Mai', 'May').\
			replace('Ago', 'Aug').\
			replace('Set','Sep').\
			replace('Out', 'Oct').\
			replace('Dez', 'Dec').\
			split()[1:]), '%d-%b-%Y,-%H:%M')))
def jsonify(o):
	return json.dumps(o, indent=4)

def split_string(n, st):
	lst = ['']
	for i in str(st):
		l = len(lst) - 1
		if len(lst[l]) < n:
			lst[l] += i
		else:
			lst += [i]
	return lst

def make_help(commands):
    split = commands.split('\n')
    help = {}
    for c in split:
        if c and c.strip():
            c,desc = c.split(' - ')
            help.update({'/'+c:'        '+desc})
    return help
