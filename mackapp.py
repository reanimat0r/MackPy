import atexit
import time
import sys
import getpass
import os
import pickle
import signal
import sqlite3
from lxml import etree
from tkinter import *
import requests
from bs4 import BeautifulSoup
from lxml import html
from collections import OrderedDict
from entities import Materia, Topico, Subtopico, Tarefa
from util import *
import jsonpickle
from requesthandler import *

# ----------------------------------------------------
#                       SETUP
# ----------------------------------------------------
signal.signal(signal.SIGINT | signal.SIGKILL, exit_gracefully)  # does OR gating work in this scenario?
DEFAULT_SQLITE_FILE = 'mack.sqlite'
class Mackenzie():
    def __init__(self, con, user, pwd):
#                 self.userdata_file = os.path.expanduser(userdata_file)
#                 try:
#                         self.userdata = pickle.load(open(self.userdata_file, 'rb'))
#                 except:
#                         input('CANNOT LOAD USERDATA')
#                         self.userdata = {} # chat_id:tia,tia:materias,chat_id:materias / "In Python, dictionaries really store pointers to objects. That means that having two keys point to the same object will not create the object twice."
            self._moodle_home = 'https://moodle.mackenzie.br/moodle/'
            self._moodle_login = self._moodle_home + 'login/index.php?authldap_skipntlmsso=1'
            self._tia_home = 'https://www3.mackenzie.br/tia/'
            self._tia_index = self._tia_home + 'index.php'
            self._tia_verifica = self._tia_home + 'verifica.php'
            self._tia_index2 = self._tia_home + 'index2.php'
            self._tia_horarios = self._tia_home + 'horarChamada.php'
            self._tia_notas = self._tia_home + 'notasChamada.php'
            self.session = requests.session()
            self.con = con;
            self.cursor = con.cursor()
            self.busy = False
            self.user = user
            self.pwd = pwd
            self.login_status={'tia':False,'moodle':False}
            self._usage = '''Mack App\n\nUsage: python3 mackapp.py [-g] [-m tia] [-p senha] [-i] [-h] [-v] targets\n
                            Options:
                                    -g      interface gráfica
                                    -h              isto
                                    -m              tia do aluno
                                    -p              senha pre-configurada opcional
                                    -i              modo interativo
                                    -t      targets
                                    -v      modo detalhado

                            Exemplos: 
                                    python3 mackapp.py -m 31417485

                            target pode ser notas, horarios, tarefas no momento
                    '''
            self._server_usage = '''Mack App\n\nUsage: python3 mackapp.py -b [bot_id_info]\n
                                            Options:
                                                    -h              isto
                                                    -i              modo interativo
                                    '''

    # ----------------------------------------------------
    #                       MOODLE
    # ----------------------------------------------------
    def login_moodle(self, v=True):
        self.logging_in_moodle = True
        #session_moodle = r1.cookies['MoodleSessionmoodle']
        res = self.session.post(self._moodle_login, data={'username': self.user, 'password': self.pwd}, headers={}, allow_redirects=True)
        res = self.session.get('https://moodle.mackenzie.br/moodle/login/index.php?testsession=25632')
        res = self.session.get('https://moodle.mackenzie.br/moodle/')
        self.login_status['moodle'] = 'Minhas Disciplinas/Cursos' in res.text
        if v: print('Logged in.' if self.login_status['moodle'] else 'Could not log in.')
        return self.login_status['moodle']

    def get_tarefas(self, fetch=False):
        self.get_materias(fetch=fetch)
        tarefas = []
        for m in self.materias:
            tarefas.extend(m.all_tarefas())
        return sorted(tarefas, key=lambda t: t.due_date)

    def update_materias(self):
        self.materias

    def _clone_materias(self):
        le_json = self.con.cursor().execute('SELECT json FROM materia WHERE tia=?', [self.user]).fetchone()[0]
        try: self.materias = jsonpickle.decode(le_json)
        except Exception as e: print(e)
        return self.materias

    def _clone_tarefas(self):
        self._clone_materias()
        tarefas = []
        for m in self.materias:
            tarefas.extend(m.all_tarefas())
        return [t for t in sorted(tarefas,key=lambda t: t.due_date) if not 'Enviado' in t.info['Status de envio'] and not 'Avaliado' in t.info['Status de avaliacao']]

    def _diff_materias(self,materias1,materias2):
        report = ''
        if len(materias1) != len(materias2):
            report+='Qtd materias mudou'
        else:
            for i in range(len(materias1)):
                if materias1[i].name == materias2[i].name:
                    print([str(t) for t in materias1[i].all_tarefas()])
        return report           

    def _clone_notas(self):
        le_json = self.con.cursor().execute('SELECT json FROM notas WHERE tia=?', [self.user]).fetchone()[0]
        self.notas = json.loads(le_json)
        return self.notas

    def _clone_horarios(self):
        le_json = self.con.cursor().execute('SELECT json FROM horarios WHERE tia=?', [self.user]).fetchone()[0]
        if le_json: self.horarios = jsonify(json.loads(le_json))
        else: self.horarios = None 
        return self.horarios

    def get_materias(self, fetch=False, diff=False, v=True):
        if not self.login_status['moodle']: self.login_moodle()
        if fetch: 
            self.materias = self._fetch_materias(self.session.get(self._moodle_home).text, v=v)
            self.cursor.execute('INSERT OR REPLACE INTO materia VALUES(?,?)', [self.user, jsonpickle.encode(self.materias)])
            self.cursor.execute('UPDATE users SET last_refresh=? WHERE tia=?', [time.strftime('%d/%m/%Y %H:%M'), self.user])
            self.con.commit()
        else: self._clone_materias()
        return self.materias

    def _fetch_materias(self, html,v=False):
        materias = []
        v = False
        bs = BeautifulSoup(html, 'lxml')
        as_ = bs.find_all('a', href=True)
        for a in as_:
            if 'course' in a['href'] and a.get('title') is not None:
                title = a.get('title')
                if title not in materias and re.search(r'\s\d{4}/\d+$', title) is not None:
                    materia = Materia(a['title'], a['href'])
                    if not any(materia.name in m.name for m in materias):
                        materias.append(materia)
        if v >= 1:
            for m in materias: print(m.hash(), str(m))
        for materia in materias:
            bs = BeautifulSoup(self.session.get(materia.link).text, 'lxml')
            i = 1
            no_topic_name_count = 10
            while True:
                sec = bs.find(id='section-' + str(i))
                if sec is None: break
                as_ = BeautifulSoup(str(sec), 'lxml').find_all('a', href=True)
                topic_name = sec.get('aria-label')
                if not topic_name:
                        no_topic_name_count -= 1
                        if not no_topic_name_count: break
                        continue
                materia.topicos.append(Topico(topic_name))
                for a in as_:
                    if a.get('onclick') is not None:
                        sub_topic_name, sub_topic_type = ' '.join(a.text.split()[:-1]), ''.join(a.text.split()[-1:])
                        if sub_topic_name is None: continue
                        sub_topic_link = a['href']
                        t = materia.topicos[-1]
                        if not any(sub_topic_name == st.name for st in t.subtopicos): t.subtopicos.append(Subtopico(sub_topic_name, sub_topic_link, sub_topic_type))
                        if sub_topic_type == 'Tarefa':
                            tarefa_page = BeautifulSoup(self.session.get(sub_topic_link).text, 'lxml')
                            tarefa_name = tarefa_page.find_all('h2')[0].text
                            tarefa_desc = tarefa_page.find_all('div', attrs={'id':'intro'})[0].text
                            tarefa_table = tarefa_page.find_all('table', class_='generaltable')[0]
                            tds = tarefa_table.find_all('td')
                            j = 0
                            tarefa = Tarefa(tarefa_name, tarefa_desc)
                            tarefa.link = sub_topic_link
                            tarefa_ik = None
                            for td in tds:
                                tarefa_attrib = td.text
                                j += 1
                                if j == 10: break  # exceeded useful table rows
                                if not tarefa_ik: tarefa_ik = tarefa_attrib.rstrip()
                                else:
                                    # if tarefa_ik == 'Data de entrega': tarefa_attrib = parse_datetime_moodle(tarefa_attrib)
                                    tarefa.info.update({tarefa_ik: tarefa_attrib})
                                    tarefa_ik = None
                            if tarefa:
                                tarefa.due_date = parse_datetime_moodle(tarefa.info['Data de entrega'])
                                t.subtopicos[-1].tarefas.append(tarefa)
                i += 1
        return materias

    # ----------------------------------------------------
    #                       TIA
    # ----------------------------------------------------

    def login_tia(self, v=True):
        res = self.session.get(self._tia_index)
        token = list(set(html.fromstring(res.text).xpath("//input[@name='token']/@value")))[0]
        data = {'alumat': self.user, 'pass': self.pwd, 'token': token, 'unidade': '001'}
        headers = dict(referer=self._tia_index)
        self.session.post(self._tia_verifica, data=data, headers=headers, allow_redirects=True)
        res = self.session.get(self._tia_index2).text
        self.login_status['tia'] = str(self.user) in res
        if v: print('Entrou no TIA')
        if 'manuten' in res: raise Exception('MANUTENCAO')
        return self.login_status['tia']

    def get_horarios(self, fetch=False):
        if fetch:
            if not self.login_status['tia']: self.login_tia()
            horarios = self._extract_horarios(self.session.get(self._tia_horarios).text)
            self.cursor.execute('INSERT OR REPLACE INTO horarios VALUES (?,?)', [self.user, jsonify(horarios)])
            self.con.commit()
            return jsonify(horarios).replace('}','').replace('{','').replace('"','').replace(',','')
        return self._clone_horarios()

    def get_notas(self, fetch=False):
        if not self.login_status['tia']: self.login_tia()
        if fetch:
            notas = self._extract_notas(self.session.get(self._tia_notas).text)
            return jsonify(notas)
        return self._clone_notas()

    def get_novas_tarefas(self):
        old_tarefas = self._clone_tarefas()
        new_tarefas = self.get_tarefas(fetch=True)
        diff = list(set(old_tarefas) - set(new_tarefas))
        if diff:
            return jsonify(diff)
            
    def _extract_horarios(self, html): # passing 
        if not self.login_status['tia']: self.login_tia() 
        refined = OrderedDict()
        dias = {0: 'Seg', 1: 'Ter', 2: 'Qua', 3: 'Qui', 4: 'Sex', 5: 'Sab'}
        dias_lindo = {0:'unda',1:'ca',2:'rta',3:'nta',4:'ta',5:'ado'}
        def extract_table(refined, lists, dias):
            for i in range(1, len(lists)):
                l = lists[i]
                hor = l[0]
                for j in range(1, len(l)):
                    if str(dias[j - 1]+dias_lindo[j-1]) not in refined:
                        refined[dias[j - 1]+dias_lindo[j-1]] = []
                        if hor not in refined[dias[j - 1]+dias_lindo[j-1]]: refined[dias[j - 1]+dias_lindo[j-1]] = OrderedDict()
                    try: refined[dias[j - 1]+dias_lindo[j-1]][hor] = re.sub('\s{2,}',' ',re.sub('\t',' ',re.sub('\s\(.*?\)','',l[j][:].replace('\u00c3','e').replace('\u00a9','').replace('\u00e1','a').replace('Predio', ' Predio').replace('Sala', ' Sala'))))
                    except:refined[dias[j - 1]+dias_lindo[j-1]][hor] = l[j] 
            return refined
        lists = self.read_html(html)[0]
        refined = extract_table(refined, lists, dias)
        lists = self.read_html(html)[1]
        refined = extract_table(refined, lists, dias)
        for k,v in refined.copy().items():
            for hora,aula in v.copy().items():
                if aula == '--': del refined[k][hora]
        return refined

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

    def _extract_notas(self, html):
        refined = {}
        cod_notas = {2: 'A', 3: 'B', 4: 'C', 5: 'D', 6: 'E', 7: 'F', 8: 'G', 9: 'H', 10: 'I', 11: 'J',
                     12: 'NI1', 13: 'NI2', 14: 'SUB', 15: 'PARTIC', 16: 'MI', 17: 'PF', 18: 'MF'}
        lists = pd.read_html(html)[1].values.tolist()
        for i in range(0, len(lists)):
            l = lists[i]
            cod_materia = l[0]
            nome_materia = l[1]
            refined[nome_materia] = {'id': cod_materia}
            for j in range(2, len(l)):
                if cod_notas[j] not in refined:
                    refined[nome_materia][cod_notas[j]] = l[j]
        return refined


# ----------------------------------------------------
#                       MAIN
# ----------------------------------------------------
def process_args(args):
    argskv = {}
    key = None
    value = None
    for a in args[1:]:
            if a.startswith('-'):
                    key = a
            else:
                    value = a
            if key is not None and value is not None:
                    argskv[key[1:]] = value
                    key = None
                    value = None
            elif key is None:
                    argskv[value] = True
            elif value is None:
                    argskv[key[1:]] = True
    return argskv

def server_use(argv):
    argkv = process_args(argv)
    if 'h' in argkv:
            print(mack._server_usage)
            return
    bot = RequestHandler()
    bot.start()
    bot.join()

def test_materias():
    con = sqlite3.connect(DEFAULT_SQLITE_FILE, check_same_thread=False)
    mack = Mackenzie(con, 31417485,19960428)
    mack.login_moodle(v=True)
    print(mack.get_novas_tarefas())
    
def main(argv):
    server_use(argv)
#     test_materias()

if __name__ == '__main__':
    main(sys.argv)
