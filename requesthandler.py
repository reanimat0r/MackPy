#!/usr/bin/python3
# -*- coding: utf-8 -*-
from util import *
import code
import sqlite3
import sys
import pickle
import telepot
import time
import os
import threading
import logging
from entities import Broadcaster
from mackapp import *

"""

"""

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.getLevelName('DEBUG'))
LOG.addHandler(logging.StreamHandler(sys.stdout))

macks = {}
routines = {}
event_routines = {}

def get_instance(con, user, pwd):
    if user not in macks: macks[user] = Mackenzie(con, user, pwd)
    return macks[user] 
DEFAULT_SQLITE_FILE = 'mack.sqlite'
if os.path.isfile(os.path.join(os.environ['HOME'], DEFAULT_SQLITE_FILE)): 
    DEFAULT_SQLITE_FILE = os.path.join(os.environ['HOME'], DEFAULT_SQLITE_FILE)
elif os.path.isfile(os.path.join(os.getcwd(), DEFAULT_SQLITE_FILE)):
    DEFAULT_SQLITE_FILE = os.path.join(os.getcwd(), DEFAULT_SQLITE_FILE)
else: print('no database file in home nor current directories, exiting') or sys.exit(1)

class RequestHandler(threading.Thread):
    def __init__(self, routine_check=False):
        LOG.debug('Starting request handler')
        threading.Thread.__init__(self)
        self.sessions = {} #chat_id:mack obj
        self.con = sqlite3.connect(DEFAULT_SQLITE_FILE, check_same_thread=False)
        self.cursor = self.con.cursor()
        self.users = {}
        users_table = self.cursor.execute('SELECT chat_id,tia,pwd,tarefas_interval FROM user').fetchall()
        if routine_check:
            for user in users_table: 
                chat_id = user[0]
                event = threading.Event()
                event_routines[chat_id] = event
                routines[chat_id] = threading.Thread(target=self.routine_check, args=[user, event])
                routines[chat_id].start()
        try: self.bot = telepot.Bot(os.environ['MACK_BOT_TOKEN'])
        except: 
            LOG.error('\n'*30, 'CRIE A VARIAVEL DE AMBIENTE MACK_BOT_TOKEN com o token do seu bot', '\n'*30)
            sys.exit(1)
        self.pending = {}  # current awaited response (this can generate conflict between two users?)
        self.help = make_help('''
start -   autenticar
add -       sugerir uma funcao
tarefas - checar novas tarefas
horarios - mostrar horarios
notas - checar notas 
fetch -   checar novas <materias|tarefas|horarios|notas>
show -     mostrar <materias|tarefas|horarios|notas>
interval - alterar intervalo entre checagem de tarefas
        ''') # Ctrl+C,Ctrl+V@BotFather
        broadcaster = Broadcaster(self.bot, self.con)
        broadcaster.start()

    def routine_check(self, user, eventHook):
        LOG.debug('Routine check for ' + str(user[1]))
        mack = get_instance(self.con, *user[1:3])
        novas = mack.get_novas_tarefas()
        novas_msg = '\n'.join(str(t) for t in novas) 
        if len(novas_msg) > 0:
            self.send(user[0], 'Novas tarefas encontradas: ')
            self.send(user[0], novas_msg)
        time.sleep(500)
        if not eventHook.is_set(): self.routine_check(user, eventHook)

    def send(self, chat_id, response):  
        if not response: return
        if len(response) > 4096: # this mitigates telepot.exception.TelegramError: 'Bad Request: message is too long'
            messages = split_string(4096, response)
            for m in messages: self.send(chat_id, m)
        else: self.bot.sendMessage(chat_id, response)
        LOG.debug('Sent message: ' + str(response) + ' to ' + str(chat_id))

    def run(self):
        LOG.debug('Awaiting requests.')
        self.bot.message_loop(self._telepot_callback, run_forever=True)

    def insert_new_user(self, chat_id, tia, pwd, username, interval=0):
        try:
            self.cursor.execute('INSERT INTO user VALUES (?,?,?,?,?,?)',[chat_id,tia,pwd,'',interval,username])
            self.con.commit()
        except: LOG.error('PROPER ERROR MESSAGE')
    def get_user(self, chat_id):
        self.cursor.execute('SELECT tia,pwd FROM user WHERE chat_id=?', (chat_id,))
        return self.cursor.fetchone()

    def _telepot_callback(self, msg):
        chat_id = msg['chat']['id']
        text = msg['text']
        username = msg['from']['username'] if 'from' in msg and 'username' in msg['from'] else ''
        LOG.debug(str(chat_id) + ':' + username + ':' + msg['text'])

        mack = get_instance(self.con, *self.get_user(chat_id))
        if chat_id in self.pending:
            if chat_id not in self.users: self.users.update({chat_id: {}})
            self.users[chat_id][self.pending[chat_id]] = text
            if self.pending[chat_id] == 'tia':
                self.pending[chat_id] = 'pwd'
                self.send(chat_id, 'Insira senha')
            elif self.pending[chat_id] == 'pwd':
                self.pending.pop(chat_id) # done with startup
                self.insert_new_user(chat_id,self.users[chat_id]['tia'],self.users[chat_id]['pwd'])
                self.send(chat_id, 'Comandos: \n' + str(self.help))
        elif text == '/start':
            self.send(chat_id, 'Insira TIA')
            self.pending[chat_id] = 'tia'
        elif text == '/last':
            self.cursor.execute('SELECT last_refresh FROM user WHERE chat_id=?',[chat_id])
            self.send(chat_id,self.cursor.fetchone()) 
        elif '/fetch' in text:
                if not chat_id in self.users and not self.get_user(chat_id): 
                    self.send(chat_id, '/start primeiro')
                elif 'materias' in text:
                    self.send(chat_id, 'Fetching matérias...')
                    mack = get_instance(self.con, *self.get_user(chat_id))
                    materias = mack.get_materias(fetch=True, diff=False)
                    response = '\n'.join(str(m) for m in materias)
                    # TODO insert details about update (diff)
                    if not response: self.send(chat_id, '/fetch failed.')
                    else: self.send(chat_id, response)
                elif 'tarefas' in text:
                    self.send(chat_id, 'Fetching tarefas...')
                    mack = get_instance(self.con, *self.get_user(chat_id))
                    tarefas = mack.get_tarefas(fetch=True)
                    response = '\n'.join(str(t) for t in tarefas)
#                     response = re.sub(r'(https\:\/\/.*?\d+)',r'', response)
                    if not response: self.send(chat_id, '/fetch failed')
                    else: self.send(chat_id, response)
                elif 'notas' in text:
                    self.send(chat_id, 'Fetching notas')
                    mack = get_instance(self.con, *self.get_user(chat_id))
                    notas = mack.get_notas(fetch=True)
                    if not notas: self.send(chat_id, '/fetch failed')
                    else: self.send(chat_id, jsonify(notas))
                elif 'horarios' in text:
                    self.send(chat_id, 'Fetching horários')
                    mack = get_instance(self.con, *self.get_user(chat_id))
                    horarios = mack.get_horarios(fetch=True)
                    if not horarios: self.send(chat_id, '/fetch failed')
                    else: self.send(chat_id, horarios)
                else:
                    self.send(chat_id, '/fetch <materias|horarios|notas')
        elif text == '/tarefas': # alias
            msg['text'] = '/fetch tarefas'
            self._telepot_callback(msg)
        elif text == '/horarios': # alias
            msg['text'] = '/show horarios'
            self._telepot_callback(msg)
        elif text.startswith('/add'): 
            what = text.replace('/add ','')
            with open('additions.log', 'a') as f: f.write(str(chat_id) + ': ' + what + '\n')
            response = 'valeu eh nois'
            self.send(chat_id, response)
        elif text.startswith('/show'):  # tarefas, materias, horarios, notas
            try:
                what = text.replace('/show','').strip()
                mack = get_instance(self.con, *self.get_user(chat_id))
                response = ''
                if what  == 'tarefas':
                    tarefas = mack.get_tarefas()
                    response = '\n'.join([str(t) for t in tarefas])
                elif what == 'notas':
                    notas = mack.get_notas()
                    response = jsonify(notas)
                elif what == 'horarios':
                    horarios = mack.get_horarios()
                    response = horarios
                elif what == 'materias':
                    materias = mack.get_materias()
                    response = materias
                elif not what:
                    self.send(chat_id, 'Uso: /show <tarefas|materias|horarios|notas>')
                self.send(chat_id, response)
            except Exception as e: 
                if text in self.help: response = jsonify(self.help[text])
                else: response = 'Not implemented'
                self.send(chat_id, str(e) + '\n' + response)
                
        elif text.startswith('/reset'):
            self.send(chat_id, 'Resetando usuário...')
            if mack.reset(): self.send(chat_id, 'Resetado com sucesso')
            else: self.send(chat_id, 'Reset falhou')
        elif text.startswith('/remind'):  # tarefas, materias, horarios, notas
            pass
        elif text.startswith('/watch'):  # tarefas, materias, horarios, notas
            self.send(chat_id, 'Olhando')
            if text.endswith('notas'):
                self.send(chat_id, 'notas')
                prevNotas = mack.get_notas(fetch=True)
                tentativas_restantes = 120
                nextNotas = None
                while tentativas_restantes:
                    tentativas_restantes-=1 
                    nextNotas = mack.get_notas(fetch=True)
                    diferenca = False
                    for k,notas in prevNotas.items():
                        if set(notas) != set(nextNotas[k]): 
                            diferenca = True
                            break
                    if diferenca: break
                    time.sleep(30)
                if not tentativas_restantes: self.send(chat_id, 'Nao saiu a nota ainda, tente novamente')
                self.send(chat_id, jsonify(nextNotas))
            elif text.endswith('tarefas'):
                self.send(chat_id, 'tarefas')
                user = self.get_user(chat_id)
                if user in event_routines: event_routines[chat_id].set()
                event = threading.Event()
                event_routines[chat_id] = event
                user = tuple([chat_id] + list(user))
                routines[chat_id] = threading.Thread(target=self.routine_check, args=[user, event])
                routines[chat_id].start()
            elif text.endswith('/watch'):
                self.send('/watch <tarefas|notas>')
            else:
                self.send(chat_id, 'Not Implemented')
                

        elif text.startswith('/interval'):  # tarefas, materias, horarios, notas
            text = text.replace('/interval')
            if len(text) > 1:
                self.cursor.execute('UPDATE user SET tarefas_interval = ? WHERE chat_id = ?',[int(text[1:]), chat_id])
            else:
                self.send(chat_id, '/interval <fator_horas>')
                self.send(chat_id, 'Seu intervalo eh' + self.con.execute('SELECT tarefas_interval FROM user WHERE chat_id=?',[chat_id]).fetchone())
        else:
            friendly_help = re.sub('(?:{|}|\")|^\s+|^\t+|\'','',str(self.help).replace(',','\n').replace('  /','/'))
            self.send(chat_id,friendly_help)

