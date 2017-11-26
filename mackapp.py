import code
import signal
import os
import sys
import unicodedata as ud
import getpass
import re
import pickle
import json
import pandas as pd
import requests
import atexit
from bs4 import BeautifulSoup
from lxml import html
from lxml import etree
# ----------------------------------------------------
#                       SETUP
# ----------------------------------------------------
cookie_file = 'cookies'
# Retrieve cookies
session = requests.session()
try:session.cookies = pickle.load(open(cookie_file, 'rb'))
except: pass

def signal_handler(signal, frame):
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

@atexit.register
def atexit_do():
    pickle.dump(session.cookies, open(cookie_file, 'wb')) #make this happen on every exit
# ----------------------------------------------------
#                       UTIL
# ----------------------------------------------------
def pretty_dict(le_dict):
    return json.dumps(le_dict, indent=4)
def parse_datetime_moodle(datetime):
    return datetime.strptime('-'.join(datetime.replace('Fev', 'Feb').replace('Abr', 'Apr').replace('Mai', 'May').replace('Ago', 'Aug').replace('Set', 'Sep').replace('Out', 'Oct').replace('Dez', 'Dec').split()[1:]), '%d-%b-%Y,-%H:%M')
def save(html):
    with open('D:\\Google Drive\\Programming\\Python\\MackApp 3.0\\page.html', 'wb') as f:
        f.write(bytes(html, 'utf-8'))

class Mackenzie():
    def __init__(self):
        self._moodle_home = 'http://moodle.mackenzie.br/moodle/'
        self._moodle_login = self._moodle_home + 'login/index.php?authldap_skipntlmsso=1'
        self._tia_home = 'https://www3.mackenzie.br/tia/'
        self._tia_index = self._tia_home + 'index.php'
        self._tia_verifica = self._tia_home + 'verifica.php'
        self._tia_index2 = self._tia_home + 'index2.php'
        self._tia_horarios = self._tia_home + 'horarChamada.php'
        self._tia_notas = self._tia_home + 'notasChamada.php'
        self._usage = '''Mack App\n\nUsage: python3 mackapp.py [-g] [-m tia] [-p senha] [-i] [-h] [-v] targets\n
                Options:
                    -g      interface gráfica
                    -h 		mostrar help
                    -m 		tia do aluno
                    -p		senha pre-configurada opcional
                    -i		modo interativo
                    -t      targets
                    -v      modo detalhado

                Exemplos: 
                    python3 mackapp.py -m 31417485

                target pode ser notas, horarios, tarefas no momento
            '''

    # ----------------------------------------------------
#                       MOODLE
# ----------------------------------------------------
    def login_moodle(self, user, pwd, v):
        res = session.get(self._moodle_home)
        data = {'username':user, 'password':pwd}
        cookies = dict(res.cookies)
        headers = dict(referer=self._tia_index)
        res = session.post(self._moodle_login, data=data, cookies=cookies, headers=headers, allow_redirects=True)
        self.logged_in = 'Minhas Disciplinas/Cursos' in res.text
        if v: print('')
    
    def get_materias(self, depth=0):
        return self._extract_materias(session.get(self._moodle_home).text, depth)
    
    def _extract_materias(self, html, depth):
        refined = {}
        bs = BeautifulSoup(html, 'lxml')
        save(html)
        as_ = bs.find_all('a', href=True)
        for a in as_:
            if 'course' in a['href'] and a.get('title') is not None:
                title = a.get('title')
                if title not in refined:
                    if re.search(r'\s\d{4}\/\d+$', title) is not None:
                        refined[a['title']] = {'link':a['href']}
        if depth > 0:
            for k,v in refined.items():
                bs = BeautifulSoup(session.get(v['link']).text, 'lxml')
                i = 1
                while True:
                    sec = bs.find(id='section-' + str(i))
                    if sec is None: break
                    as_ = BeautifulSoup(str(sec),'lxml').find_all('a', href=True)
                    topic_name = sec.get('aria-label')
                    topics = {}
                    for a in as_:
                        if a.get('onclick') is not None:
                            sub_topic, sub_topic_type = ' '.join(a.text.split()[:-1]), ''.join(a.text.split()[-1:])
                            if sub_topic is None: continue
                            sub_topic_link = a['href']
                            if sub_topic not in topics: topics[sub_topic] = {'type':sub_topic_type}
                            topics[sub_topic]['link'] = sub_topic_link
                            if depth > 1 and sub_topic_type == 'Tarefa':
                                tarefa_table = BeautifulSoup(session.get(sub_topic_link).text,
                                              'lxml').find_all('table', class_='generaltable')[0]
                                tds = tarefa_table.find_all('td')
                                j = 0
                                tarefa_ik = ''
                                for td in tds:
                                    tarefa_iv = td.text
                                    j+=1
                                    if j == 10: break
                                    if tarefa_ik == '':
                                        tarefa_ik = tarefa_iv.rstrip()
                                    else:
                                        topics[sub_topic][tarefa_ik] = tarefa_iv
                                        tarefa_ik = ''
                    refined[k][topic_name] = topics
                    i+=1
        return refined
    
    # ----------------------------------------------------
    #                       TIA
    # ----------------------------------------------------

    def login_tia(self, user, pwd, v):
        res = session.get(self._tia_index)
        token = list(set(html.fromstring(res.text).xpath("//input[@name='token']/@value")))[0]
        data = {'alumat':user, 'pass':pwd, 'token':token, 'unidade':'001'}
        cookies = dict(res.cookies)
        headers = dict(referer=self._tia_index)
        res = session.post(self._tia_verifica, data=data, cookies=cookies, headers=headers, allow_redirects=True)
        logged_in = user in session.get(self._tia_index2).text
        if v: print( '' 'Entrou no TIA')
        return logged_in

    def _extract_horarios(self, html):
        refined = {}
        dias = {0:'Seg',1:'Ter',2:'Qua',3:'Qui',4:'Sex',5:'Sab'}
        lists = pd.read_html(html)[1].values.tolist()
        for i in range(1, len(lists)):
            l = lists[i]
            hor = l[0]
            for j in range(1, len(l)):
                if dias[j-1] not in refined:
                    refined[dias[j-1]] = []
                    if hor not in refined[dias[j-1]]: refined[dias[j-1]] = {}
                try: refined[dias[j-1]][hor] = l[j][:l[j].index('(') - 1]
                except: refined[dias[j-1]][hor] = l[j]
        return refined

    def get_horarios(self):
        return self._extract_horarios(session.get(self._tia_horarios).text)

    def _extract_notas(self, html):
        refined = {}
        cod_notas = {2:'A',3:'B',4:'C',5:'D',6:'E',7:'F',8:'G',9:'H',10:'I',11:'J',
                     12:'NI1',13:'NI2',14:'SUB',15:'PARTIC',16:'MI',17:'PF',18:'MF'}
        lists = pd.read_html(html)[1].values.tolist()
        for i in range(0, len(lists)):
            l = lists[i]
            cod_materia = l[0]
            nome_materia = l[1]
            refined[nome_materia] = {'id':cod_materia}
            for j in range(2, len(l)):
                if cod_notas[j] not in refined:
                    refined[nome_materia][cod_notas[j]] = l[j]
        return refined

    def get_notas(self):
        return self._extract_notas(session.get(self._tia_notas).text)
    
# ----------------------------------------------------
#                       MAIN
# ----------------------------------------------------
def process_args(args):
    argskv = {}
    key = None
    value = None
    for a in args[1:]:
        if a.startswith('-'): key = a
        else: value = a
        if key is not None and value is not None: 
            argskv[key[1:]] = value
            key = None
            value = None
        elif key is None: argskv[value] = True
        elif value is None: argskv[key[1:]] = True
    return argskv
    
def main(args):
    argskv = process_args(args)
    mack = Mackenzie()
    if 'h' in argskv: 
        print(mack._usage)
        return
    v = 'v' in argskv
    i = 'i' in argskv
    logged_in_tia = False
    logged_in_moodle = False
    to_do = list(filter(lambda k: not k.startswith('-'), argskv.keys()))
    if not to_do and not i: i = True
    m = argskv['m'] if 'm' in argskv else input('Matricula: ')
    p = argskv['p'] if 'p' in argskv else getpass.getpass('Senha: ')
    while True:
        if i:
            try: o = input(''' Operacoes:\n\tTarefas\n\tNotas\n\tHorarios\n\nOperacao: ''', end='').lower()
            except: continue
        else:
            try: o = to_do.pop()
            except: break
        out = None
        if o == 'tarefas':
            if not logged_in_moodle: logged_in_moodle = mack.login_moodle(m, p, v)
            out = mack.get_materias(3)
        elif o == 'notas':
            if not logged_in_tia: logged_in_tia = mack.login_tia(m, p, v)
            out = mack.get_notas()
        elif o == 'horarios':
            if not logged_in_tia: logged_in_tia = mack.login_tia(m, p, v)
            out = mack.get_horarios()
        print(pretty_dict(out))
        
        if not i: break

if __name__ == '__main__':
    main(sys.argv)