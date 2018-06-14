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

def read_html(self,html):
    datas=[]
    tables = BeautifulSoup(html,'lxml').select('table.table-bordered.table-striped')
    for table in tables:
        data = []
        for row in table.findAll('tr'):
           cell = row.findAll('td')
            le_row = []
            for point in cell:
                le_row.append(re.sub('<\/?(?:td|strong|br\/)>','',
                    re.sub('<\/?div\s?(?:align=\"\w+\")?>', '',
                        re.sub('\sbgcolor=\"\w*?\"', '', 
                            re.sub('\swidth=\"\d+%\"','', str(point))))))
            data.append(le_row)
        datas.append(data)
    return datas

if __name__ == '__main__':
    dt_moodle = parse_datetime_moodle('sexta, 4 Jan 2018, 23:00')
    print(dt_moodle)
    print(datetime.datetime.now())
    print(dt_moodle > datetime.datetime.now())
