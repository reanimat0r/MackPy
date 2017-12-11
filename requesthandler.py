from util import *
import pickle
import telepot
import os
import threading


class RequestHandler(threading.Thread):
	def __init__(self, mack, users_file='users.mack'):
		threading.Thread.__init__(self)
		self._users_file = users_file
		self.mack = mack
		try:
			self.users = pickle.load(open(users_file, 'rb'))
		except:
			self.users = {}
		self.bot = telepot.Bot(os.environ['MACK_BOT_TOKEN'])
		self.pending = ''  # awaited response
		self.help = '\n'.join(['/start', '/fetch', '/materias'])

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
			materias = self.mack.get_materias(fetch=True)
			response = '\n'.join(str(m) for m in materias)
			self.safe_send(chat_id, response)
		elif text == '/show': # tarefas, materias, horarios, notas
			pass
		elif text == '/remind': # tarefas, materias, horarios, notas
			pass
		elif text == '/esperar_por': # tarefas, materias, horarios, notas
			pass
		else:
			unimsg = 'Unrecognized command: ' + text
			print(unimsg)
			self.safe_send(chat_id, unimsg)
