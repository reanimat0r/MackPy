from util import *
import sqlite3
import sys
import pickle
import telepot
import os
import threading
from mackapp import *

"""
Test multiuser
Implement


"""
class RequestHandler(threading.Thread):
    def __init__(self, verbose=True):
        threading.Thread.__init__(self)
        self.verbose = verbose
        self.sessions = {}#chat_id:mack obj
        self.con = sqlite3.connect(DEFAULT_SQLITE_FILE, check_same_thread=False)
        try:
                self.users = pickle.load(open(users_file, 'rb'))
        except:
                self.users = {}
        try: self.bot = telepot.Bot(os.environ['MACK_BOT_TOKEN'])
        except: 
            print('\n'*30, 'CRIE A VARIAVEL DE AMBIENTE MACK_BOT_TOKEN com o token do seu bot', '\n'*30)
            sys.exit(0)
        self.pending = {}  # current awaited response (this can generate conflict between two users?)
        self.help = make_help('''
start - Processo de autenticação
fetch - Descobrir novas postagens
materias - Todas as matérias encontradas
show - Mostrar <tarefas|horarios|notas>
        ''') # Ctrl+C,Ctrl+V@BotFather

    def safe_send(self, msg, response):  # this mitigates telepot.exception.TelegramError: 'Bad Request: message is too long'
        if len(response) > 4096:
                messages = split_string(4096, response)
                for m in messages: self.safe_send(msg, m)
        else:
                self.bot.sendMessage(msg['chat']['id'], response)
                print('TO {}: {}'.format(msg['from']['username'], response))

    def run(self):
        print('Awaiting requests.')
        self.bot.message_loop(self._telepot_callback, run_forever=True)

    def insert_new_user(self, chat_id, tia, pwd):
        self.con.execute('INSERT INTO users VALUES ({},{},{},\'\')'.format(chat_id,tia,pwd))            

    def _telepot_callback(self, msg):
        chat_id = msg['chat']['id']
        text = msg['text']
        # do we need msg['from']['username']?
        if chat_id in self.pending:
            if chat_id not in self.users: self.users.update({chat_id: {}})
            self.users[chat_id][self.pending[chat_id]] = text
            if self.pending[chat_id] == 'tia':
                    self.pending[chat_id] = 'pwd'
                    self.safe_send(msg, 'Insira senha')
            elif self.pending[chat_id] == 'pwd':
                    self.pending.pop(chat_id) # done with startup
                    self.insert_new_user(chat_id,*self.users[chat_id].values())
                    self.safe_send(msg, 'Comandos: \n' + str(self.help))
        elif text == '/start':
                    self.safe_send(msg, 'Insira TIA')
                    self.pending[chat_id] = 'tia'
        elif text == '/fetch':
                if not chat_id in self.users: 
                    self.safe_send(msg, '/start first')
                else:
                    self.safe_send(msg, 'Fetching matérias...')
                    materias, diff = self.mack.get_materias(fetch=True, diff=True)
                    response = '\n'.join(m.name for m in materias)
                    # TODO insert details about update (diff)
                    if not response:
                            self.safe_send(msg, '/fetch failed.')
                    else:
                            self.safe_send(msg, response)
        elif text.startswith('/show'):  # tarefas, materias, horarios, notas
            try:
                arg = text.split()[1]
                if arg.strip().lower() == 'tarefas':
                    tarefas = self.mack.get_tarefas()
                    self.safe_send(msg, '\n'.join([str(t) for t in tarefas]))
            except: self.safe_send(msg, self.help[text])

        elif text.startswith('/remind'):  # tarefas, materias, horarios, notas
                pass
        elif text.startswith('/watch'):  # tarefas, materias, horarios, notas
                pass
        else:
                unimsg = 'Unrecognized command: ' + text
                self.safe_send(msg, unimsg)

if __name__  == '__main__':
        rh = RequestHandler(None)
        print(rh.help)
