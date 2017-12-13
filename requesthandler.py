from util import *
import pickle
import telepot
import os
import threading


class RequestHandler(threading.Thread):
	def __init__(self, mack, users_file='users.mack', verbose=True):
		threading.Thread.__init__(self)
		self.verbose = verbose
		self._users_file = users_file
		self.mack = mack
		try:
			self.users = pickle.load(open(users_file, 'rb'))
		except:
			self.users = {}
		self.bot = telepot.Bot(os.environ['MACK_BOT_TOKEN'])
		self.pending = ''  # awaited response
		# self.help = '\n'.join(['/start', '/fetch', '/materias'])
		self._commands = '''
start - Processo de autenticação
fetch - Descobrir novas postagens
materias - Todas as matérias encontradas
tarefas - Todas as tarefas
		'''
		self.help = self.make_help()

	def make_help(self):
		split = self._commands.split('\n')
		help = {}
		for c in split:
			if c and c.strip():
				c,desc = c.split(' - ')
				help.update({'/'+c:desc})
		return help

	def safe_send(self, chat_id,
	              message):  # this mitigates telepot.exception.TelegramError: 'Bad Request: message is too long'
		if len(message) > 4096:
			messages = split_string(4096, message)
			for m in messages: self.bot.sendMessage(chat_id, m)
		else:
			self.bot.sendMessage(chat_id, message)

	def run(self):
		print('Awaiting requests.')
		self.bot.message_loop(self._telepot_callback, run_forever=True)

	def _telepot_callback(self, msg):
		chat_id = msg['chat']['id']
		text = msg['text']
		# do we need msg['from']['username']?
		if self.pending:
			if chat_id not in self.users: self.users.update({chat_id: {}})
			self.users[chat_id][self.pending] = text
			pickle.dump(self.users, open(self._users_file, 'wb'))
			if self.pending == 'tia':
				self.pending = 'pwd'
				self.safe_send(chat_id, 'Insira senha')
			elif self.pending == 'pwd':
				self.pending = None
				self.safe_send(chat_id, 'Insira senha')
				self.safe_send(chat_id, 'Comandos: \n' + self.help)

		if text == '/start':
			self.safe_send(chat_id, 'Insira TIA')
			self.pending = 'tia'
		elif text == '/fetch':
			self.safe_send(chat_id, 'Fetching matérias...')
			materias, diff = self.mack.get_materias(fetch=True, diff=True)
			response = '\n'.join(m.name for m in materias)
			# TODO insert details about update (diff)
			if not response:
				self.safe_send(chat_id, '/fetch failed.')
			else:
				self.safe_send(chat_id, response)
		elif text.startswith('/show'):  # tarefas, materias, horarios, notas
			try:
				arg = text.split()[1]
				if arg.strip().lower() == 'tarefas':
					tarefas = self.mack.get_tarefas()
					self.safe_send(chat_id, '\n'.join([str(t) for t in tarefas]))
			except: self.safe_send(chat_id, self.help[text])

		elif text.startswith('/remind'):  # tarefas, materias, horarios, notas
			pass
		elif text.startswith('/esperar_por'):  # tarefas, materias, horarios, notas
			pass
		else:
			unimsg = 'Unrecognized command: ' + text
			print(unimsg)
			self.safe_send(chat_id, unimsg)

if __name__  == '__main__':
	rh = RequestHandler(None)
	print(rh.help)