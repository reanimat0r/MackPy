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
        self.sessions = {} #chat_id:mack obj
        self.con = sqlite3.connect(DEFAULT_SQLITE_FILE, check_same_thread=False)
        self.cursor = self.con.cursor()
        self.users = {}
        def send_alerts(users_table): # constant alerts upon news
            while True:
                d = datetime.datetime.now()
                for user in users_table:
                    if user[3] and not d.hour % user[3] and d.minute == 0 and d.second < 5:
                        mack = Mackenzie(self.con, *user[1:3])
                        novas = mack.get_novas_tarefas()
                        if novas: self.safe_send(user[0], novas)
        users_table = self.cursor.execute('SELECT chat_id,tia,pwd,tarefas_interval FROM users').fetchall()
        threading.Thread(target=send_alerts, args=[users_table]).start()
        try: self.bot = telepot.Bot(os.environ['MACK_BOT_TOKEN'])
        except: 
            print('\n'*30, 'CRIE A VARIAVEL DE AMBIENTE MACK_BOT_TOKEN com o token do seu bot', '\n'*30)
            sys.exit(0)
        self.pending = {}  # current awaited response (this can generate conflict between two users?)
        self.help = make_help('''
start -   Processo de autenticacao
add -       Sugira uma funcao
interval - alterar intervalo entre checagem de tarefas
fetch -   Descobrir novas postagens <tarefas|horarios|notas>
show -     Mostrar <tarefas|horarios|notas>
        ''') # Ctrl+C,Ctrl+V@BotFather

    def safe_send(self, chat_id, response):  # this mitigates telepot.exception.TelegramError: 'Bad Request: message is too long'
        if len(response) > 4096:
            messages = split_string(4096, response)
            for m in messages: self.safe_send(chat_id, m)
        else:
            self.bot.sendMessage(chat_id, response)
#             print('TO {}: {}'.format(msg['from']['id'], response))

    def run(self):
        print('Awaiting requests.')
        self.bot.message_loop(self._telepot_callback, run_forever=True)

    def insert_new_user(self, chat_id, tia, pwd):
        try:
            self.cursor.execute('INSERT INTO users VALUES (?,?,?,\'\',0)',[chat_id,tia,pwd])
            self.con.commit()
        except: print('PROPER ERROR MESSAGE')
    def get_user(self, chat_id):
        self.cursor.execute('SELECT tia,pwd FROM users WHERE chat_id=?', (chat_id,))
        return self.cursor.fetchone()

    def _telepot_callback(self, msg):
        chat_id = msg['chat']['id']
        text = msg['text']
        # do we need msg['from']['username']?
        if chat_id in self.pending:
            if chat_id not in self.users: self.users.update({chat_id: {}})
            self.users[chat_id][self.pending[chat_id]] = text
            if self.pending[chat_id] == 'tia':
                self.pending[chat_id] = 'pwd'
                self.safe_send(chat_id, 'Insira senha')
            elif self.pending[chat_id] == 'pwd':
                self.pending.pop(chat_id) # done with startup
                self.insert_new_user(chat_id,self.users[chat_id]['tia'],self.users[chat_id]['pwd'])
                self.safe_send(chat_id, 'Comandos: \n' + str(self.help))
        elif text == '/start':
            self.safe_send(chat_id, 'Insira TIA')
            self.pending[chat_id] = 'tia'
        elif text == '/when':
            self.cursor.execute('SELECT last_refresh FROM users WHERE chat_id=?',[chat_id])
            self.safe_send(chat_id,self.cursor.fetchone()) 
        elif '/fetch' in text:
                if not chat_id in self.users and not self.get_user(chat_id): 
                    self.safe_send(chat_id, '/start primeiro')
                elif 'materias' in text:
                    self.safe_send(chat_id, 'Fetching matérias...')
                    mack = Mackenzie(self.con, *self.get_user(chat_id))
                    materias = mack.get_materias(fetch=True, diff=False)
                    response = '\n'.join(str(m) for m in materias)
                    # TODO insert details about update (diff)
                    if not response: self.safe_send(chat_id, '/fetch failed.')
                    else: self.safe_send(chat_id, response)
                elif 'tarefas' in text:
                    self.safe_send(chat_id, 'Fetching tarefas...')
                    mack = Mackenzie(self.con, *self.get_user(chat_id))
                    tarefas = mack.get_tarefas(fetch=True)
                    response = '\n'.join(str(t) for t in tarefas)
#                     response = re.sub(r'(https\:\/\/.*?\d+)',r'', response)
                    if not response: self.safe_send(chat_id, '/fetch failed')
                    else: self.safe_send(chat_id, response)
                elif 'notas' in text:
                    self.safe_send(chat_id, 'Fetching notas')
                    mack = Mackenzie(self.con, *self.get_user(chat_id))
                    notas = mack.get_notas(fetch=True)
                    if not notas: self.safe_send(chat_id, '/fetch failed')
                    else: self.safe_send(chat_id, notas)
                elif 'horarios' in text:
                    self.safe_send(chat_id, 'Fetching horários')
                    mack = Mackenzie(self.con, *self.get_user(chat_id))
                    horarios = mack.get_horarios(fetch=True)
                    if not horarios: self.safe_send(chat_id, '/fetch failed')
                    else: self.safe_send(chat_id, horarios)
                else:
                    self.safe_send(chat_id, '/fetch <materias|horarios|notas')
        elif text.startswith('/add'): 
            what = text.replace('/add ','')
            with open('additions.log', 'a') as f:
                f.write(what)
            response = 'valeu eh nois'
            self.safe_send(chat_id, response)
        elif text.startswith('/show'):  # tarefas, materias, horarios, notas
            try:
                what = text.replace('/show ','')
                mack = Mackenzie(self.con, *self.get_user(chat_id))
                if what  == 'tarefas':
                    tarefas = mack.get_tarefas()
                    response = '\n'.join([str(t) for t in tarefas])
                elif what == 'notas':
                    notas = mack.get_notas()
                    response = notas
                    self.safe_send(chat_id, notas)
                elif what == 'horarios':
                    horarios = mack.get_horarios()
                    response = horarios
                elif what == 'materias':
                    materias = mack.get_materias()
                    response = materias
                if not response:self.safe_send(chat_id, 'No results; try /fetch ' + what + '?')
                else: self.safe_send(chat_id, response)
            except Exception as e: 
                if text in self.help: response = jsonify(self.help[text])
                else: response = 'Not implemented'
                self.safe_send(chat_id, str(e) + '\n' + response)
                
        elif text.startswith('/remind'):  # tarefas, materias, horarios, notas
            pass
        elif text.startswith('/watch'):  # tarefas, materias, horarios, notas
            pass
        elif text.startswith('/interval'):  # tarefas, materias, horarios, notas
            text = text.replace('/interval')
            if len(text) > 1:
                self.cursor.execute('UPDATE users SET tarefas_interval = ? WHERE chat_id = ?',[int(text[1:]), chat_id])
            else:
                self.safe_send(chat_id, '/interval <fator_horas>')
        else:
            friendly_help = re.sub('(?:{|}|\")|^\s+|^\t+|\'','',str(self.help).replace(',','\n').replace('  /','/'))
            self.safe_send(chat_id,friendly_help)

if __name__  == '__main__':
        rh = RequestHandler()
        print(rh.help)
