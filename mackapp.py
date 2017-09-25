import getpass
import re
import pickle
import json
import pandas as pd
import requests
from bs4 import BeautifulSoup
from lxml import html
from lxml import etree

cookie_file = 'D:\\Google Drive\\Programming\\Python\\MackApp 3.0\\cookies'

# Retrieve cookies
session = requests.session()
try:session.cookies = pickle.load(open(cookie_file, 'rb'))
except: pass

def save(html):
    with open('D:\\Google Drive\\Programming\\Python\\MackApp 3.0\\page.html', 'wb') as f:
        f.write(bytes(html, 'utf-8'))

# ----------------------------------------------------
#                       MOODLE
# ----------------------------------------------------
moodle_home = 'http://moodle.mackenzie.br/moodle/'
moodle_login = moodle_home + 'login/index.php?authldap_skipntlmsso=1'

def login_moodle(user, pwd):
    res = session.get(moodle_home)
    #token = list(set(html.fromstring(res.text).xpath("//input[@name='token']/@value")))[0]
    data = {'authldap_skipntlmsso':'1','username':user, 'password':pwd}
    cookies = dict(res.cookies)
    headers = dict(referer=tia_index)
    res = session.post(moodle_login, data=data, cookies=cookies, headers=headers, allow_redirects=True)
    return 'Minhas Disciplinas/Cursos' in res.text

def get_materias(extended=False):
    r = extract_materias(session.get(moodle_home).text, extended)
    return json.dumps(r, indent=4)
    

def extract_materias(html, extended=False):
    refined = {}
    bs = BeautifulSoup(html, 'lxml')
    save(html)
    as_ = bs.find_all('a', href=True)
    last_href = ''
    for a in as_:
        if 'course' in a['href'] and a.get('title') is not None:
            title = a.get('title')
            if title not in refined:
                if re.search(r'\s\d{4}\/\d+$', title) is not None:
                    refined[a['title']] = {'link':a['href']}
    if extended:
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
                        sub_topic, sub_topic_type = ' '.join(a.text.split()[:-1]), a.text.split()[-1:]
                        if sub_topic not in topics:
                            topics[sub_topic] = {'type':''.join(sub_topic_type)}
                        topics[sub_topic]['link'] = a['href']
                refined[k][topic_name] = topics
                i+=1
    return refined

# ----------------------------------------------------
#                       TIA
# ----------------------------------------------------

tia_home = 'https://www3.mackenzie.br/tia/'
tia_index = tia_home + 'index.php'
tia_verifica = tia_home + 'verifica.php'
tia_index2 = tia_home + 'index2.php'
tia_horarios = tia_home + 'horarChamada.php'
tia_notas = tia_home + 'notasChamada.php'

def login_tia(user, pwd):
    res = session.get(tia_index)
    token = list(set(html.fromstring(res.text).xpath("//input[@name='token']/@value")))[0]
    data = {'alumat':user, 'pass':pwd, 'token':token, 'unidade':'001'}
    cookies = dict(res.cookies)
    headers = dict(referer=tia_index)
    res = session.post(tia_verifica, data=data, cookies=cookies, headers=headers, allow_redirects=True)
    
def extract_horarios(html):
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

def get_horarios():
    r = extract_horarios(session.get(tia_horarios).text)
    return json.dumps(r, indent=4)

def extract_notas(html):
    refined = {}
    cod_notas = {2:'A',3:'B',4:'C',5:'D',6:'E',7:'F',8:'G',9:'H',10:'I',11:'J',
                 12:'NI1',13:'NI2',14:'SUB',15:'PARTIC',16:'MI',17:'PF',18:'MF'}
    lists = pd.read_html(html)[1].values.tolist()
    for i in range(1, len(lists)):
        l = lists[i]
        cod_materia = l[0]
        nome_materia = l[1]
        refined[nome_materia] = {'id':cod_materia}
        for j in range(2, len(l)):
            if cod_notas[j] not in refined:
                refined[nome_materia][cod_notas[j]] = l[j]
    return refined

def get_notas():
    r = extract_notas(session.get(tia_notas).text)
    return json.dumps(r, indent=4)

alumat = '31417485'
#login_tia(alumat, pwd)
login_moodle(alumat, getpass.getpass('Senha: '))
print(get_materias(extended=True))
pickle.dump(session.cookies, open(cookie_file, 'wb'))
