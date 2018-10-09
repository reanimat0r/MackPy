#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import atexit
import time
import sys
import getpass
import os
import pickle
import signal
import os
import sqlite3
from lxml import etree
from tkinter import *
import requests
from bs4 import BeautifulSoup
from lxml import html
from collections import OrderedDict
import pandas as pd
from entities import Materia, Topico, Subtopico, Tarefa
from util import *
import jsonpickle
from requesthandler import *
import logging

# ----------------------------------------------------
#                       SETUP
# ----------------------------------------------------
signal.signal(signal.SIGINT | signal.SIGKILL, exit_gracefully)
LOG_FILE='mackapp.log'
LOG_FORMAT = "%(levelname)s %(name)s %(asctime)s - %(message)s" 
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.getLevelName('DEBUG'))
LOG.addHandler(logging.StreamHandler(sys.stdout))

class Mackenzie():

    def __init__(self, con, user, pwd):
            LOG.debug('Init Mack Access')
            self._moodle_home = 'https://moodle.mackenzie.br/moodle/'
            self._moodle_login = self._moodle_home + 'login/index.php?authldap_skipntlmsso=1'
            self._tia_home = 'https://www3.mackenzie.br/tia/'
            self._tia_index = self._tia_home + 'index.php'
            self._tia_verifica = self._tia_home + 'verifica.php'
            self._tia_index2 = self._tia_home + 'index2.php'
            self._tia_horarios = self._tia_home + 'horarChamada.php'
            self._tia_notas = self._tia_home + 'notasChamada.php'
            self.session = requests.session()
            if con:
                self.con = con;
                self.cursor = con.cursor()
            self.busy = False
            self.user = user
            self.pwd = pwd
            self.login_status={'tia':False,'moodle':False}

    # ----------------------------------------------------
    #                       MOODLE
    # ----------------------------------------------------
    def login_moodle(self):
        LOG.debug('Logging in moodle for ' + str(self.user))
        self.logging_in_moodle = True
        res = self.session.post(self._moodle_login, data={'username': self.user, 'password': self.pwd}, allow_redirects=True)
        res = self.session.get('https://moodle.mackenzie.br/moodle/login/index.php?testsession=25632')
        res = self.session.get('https://moodle.mackenzie.br/moodle/')
        self.login_status['moodle'] = 'Minhas Disciplinas/Cursos' in res.text
        LOG.debug(str(self.user) +' logged in: ' + str(self.login_status['moodle']))
        return self.login_status['moodle']

    def get_tarefas(self, fetch=False, ):
        self.get_materias(fetch=fetch)
        tarefas = []
        for m in self.materias: tarefas.extend(m.all_tarefas())
        sorted_filtered_tarefas = filter(lambda t: t.due_date > datetime.datetime.now(), sorted(tarefas, key=lambda t: t.due_date)) 
        return sorted_filtered_tarefas

    def reset(self):
        tabelas = ['horario', 'materia', 'nota']
        for t in tabelas: self.con.cursor().execute('DELETE FROM ' + t + ' WHERE tia=?', [self.user])
        return True

    def get_novas_tarefas(self):
        old_tarefas = self._clone_tarefas()
        new_tarefas = self.get_tarefas(fetch=True)
        diff = [new_tarefas[i] for i in range(len(old_tarefas)) if new_tarefas[i] != old_tarefas[i]]
#         filtro = lambda x: 'Avaliado' not in x.info['Status da avaliação'] and 'nviado' not in x.info['Status da avaliação'] and parse_datetime_moodle(x.info['Data de entrega']) > datetime.datetime.now()
#         filtered_diff = filter(filtro, diff)
        return diff

    def _clone_tarefas(self):
        self._clone_materias()
        tarefas = []
        for m in self.materias: tarefas.extend(m.all_tarefas())
        return [t for t in sorted(tarefas, key=lambda t: t.due_date)]

    def update_materias(self):
        self.materias

    def _clone_materias(self):
        le_json = ''
        try: le_json = self.con.cursor().execute('SELECT json FROM materia WHERE tia=?', [self.user]).fetchone()[0]
        except: self.materias = []
        try: self.materias = jsonpickle.decode(le_json)
        except Exception as e: LOG.exception(e)
        return self.materias

    def _diff_materias(self,materias1,materias2):
        report = ''
        if len(materias1) != len(materias2):
            report+='Qtd materias mudou'
        else:
            for i in range(len(materias1)):
                if materias1[i].name == materias2[i].name:
                    print([str(t) for t in materias1[i].all_tarefas()])
        return report           

    def get_materias(self, fetch=False, diff=False):
        if fetch: 
            if not self.login_status['moodle']: self.login_moodle()
            self.materias = self._fetch_materias(self.session.get(self._moodle_home).text)
            self.cursor.execute('INSERT OR REPLACE INTO materia VALUES(?,?)', [self.user, jsonpickle.encode(self.materias)])
            self.cursor.execute('UPDATE user SET last_refresh=? WHERE tia=?', [time.strftime('%d/%m/%Y %H:%M'), self.user])
            self.con.commit()
        else: self._clone_materias()
        return self.materias

    def _fetch_materias(self, html):
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
                            LOG.debug('Fetching tarefa: ' + str(sub_topic_link.encode('utf-8')))
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
    def login_tia(self):
        LOG.debug('logging in tia for ' + str(self.user))
        res = self.session.get(self._tia_index)
        token = list(set(html.fromstring(res.text).xpath("//input[@name='token']/@value")))[0]
        data = {'alumat': self.user, 'pass': self.pwd, 'token': token, 'unidade': '001'}
        headers = dict(referer=self._tia_index)
        self.session.post(self._tia_verifica, data=data, headers=headers, allow_redirects=True)
        res = self.session.get(self._tia_index2).text
        self.login_status['tia'] = str(self.user) in res
        if 'manuten' in res: raise Exception('MANUTENCAO')
        LOG.debug(str(self.user) + (' not' if not self.login_status['tia'] else ' else ''') + ' logged in')
        return self.login_status['tia']

    def get_notas(self, fetch=True):
        if not self.login_status['tia']: self.login_tia()
        if fetch:
            notas = self._extract_notas(self.session.get(self._tia_notas).text)
            self.cursor.execute('INSERT OR REPLACE INTO nota VALUES (?,?)', [self.user, jsonify(notas)])
            return notas
        return self._clone_notas()

    def get_novas_notas(self):
        old_notas = self.get_notas(fetch=True)
        new_notas = self.get_notas(fetch=False)
        code.interact(local=locals())
        diff = [new_notas[i] for i in range(len(old_notas)) if new_notas[i] != old_notas[i]]
#         filtro = lambda x: 'Avaliado' not in x.info['Status da avaliação'] and 'nviado' not in x.info['Status da avaliação'] and parse_datetime_moodle(x.info['Data de entrega']) > datetime.datetime.now()
#         filtered_diff = filter(filtro, diff)
        return diff

    def _clone_notas(self):
        le_json = self.con.cursor().execute('SELECT json FROM nota WHERE tia=?', [self.user]).fetchone()[0]
        LOG.info('Clone notas para ' + str(self.user) + '\n\n' + le_json)
        self.notas = json.loads(le_json)
        return self.notas

    def _extract_notas(self, html):
        refined = OrderedDict()
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

    def get_horarios(self, fetch=False):
        if fetch:
            if not self.login_status['tia']: self.login_tia()
            horarios = self._extract_horarios(self.session.get(self._tia_horarios).text)
            LOG.debug(horarios)
            self.cursor.execute('INSERT OR REPLACE INTO horario VALUES (?,?)', [self.user, jsonify(horarios)])
            self.con.commit()
            return jsonify(horarios).replace('}','').replace('{','').replace('"','').replace(',','')
        return self._clone_horarios().replace('}','').replace('{','').replace('"','').replace(',','')

    def _clone_horarios(self):
        le_json = self.con.cursor().execute('SELECT json FROM horario WHERE tia=?', [self.user]).fetchone()[0]
        if le_json: self.horarios = jsonify(json.loads(le_json))
        else: self.horarios = None 
        return self.horarios
            
    def _extract_horarios(self, html): # not passing 
        if not self.login_status['tia']: self.login_tia() 
        refined = OrderedDict()
        dias = {0: 'Seg', 1: 'Ter', 2: 'Qua', 3: 'Qui', 4: 'Sex', 5: 'Sab'}
        dias_lindo = {0:'unda',1:'ca',2:'rta',3:'nta',4:'ta',5:'ado'}
        def extract_table(refined, lists, dias):
            for i in range(1, len(lists)):
                code.interact(local=locals())
                l = lists[i]
                hor = l[0]
                for j in range(1, len(l)):
                    if str(dias[j - 1]+dias_lindo[j-1]) not in refined:
                        refined[dias[j - 1]+dias_lindo[j-1]] = []
                        if hor not in refined[dias[j - 1]+dias_lindo[j-1]]: refined[dias[j - 1]+dias_lindo[j-1]] = OrderedDict()
                    try: refined[dias[j - 1]+dias_lindo[j-1]][hor] = re.sub('\s{2,}',' ',re.sub('\t',' ',re.sub('\s\(.*?\)','',l[j][:].replace('\u00c3','e').replace('\u00a9','').replace('\u00e1','a').replace('Predio', ' Predio').replace('Sala', ' Sala'))))
                    except:refined[dias[j - 1]+dias_lindo[j-1]][hor] = l[j] 
            return refined
        lists = pd.read_html(html)[0]
        refined = extract_table(refined, lists, dias)
        lists = pd.read_html(html)[1]
        refined = extract_table(refined, lists, dias)
        for k,v in refined.copy().items():
            for hora,aula in v.copy().items():
                if aula == '--': del refined[k][hora]
        return refined


# ----------------------------------------------------
#                       MAIN
# ----------------------------------------------------

def main():
    bot = RequestHandler()
    bot.start()
    bot.join()

if __name__ == '__main__':
    main()
