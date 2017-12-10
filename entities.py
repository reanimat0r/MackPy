class Materia:
	def __init__(self, name, link):
		if not name or not link: raise Exception('NO NAME OR NO LINK')
		self.name = name
		self.link = link
		self.topicos = []

	def __str__(self):
		print('-'*20)
		print(self.name)
		print(self.link)
		for t in self.topicos: print(t)

class Topico:
	def __init__(self, name):
		if not name: raise Exception('NO NAME')
		self.name = name
		self.subtopicos = []

	def __str__(self):
		print('-'*15)
		print(self.name)
		print(self.subtopicos)

class Subtopico:
	def __init__(self, name, link, type):
		if not name or not link or not type: raise Exception('NO NAME OR NO LINK OR NO TYPE')
		self.name = name
		self.link = link
		self.tarefas = {} # order by date?

	def __str__(self):
		print('-'*10)
		print(self.name)
		print(self.link)
		print(self.tarefas)

class Tarefa:
	def __init__(self, name, link, type):
		if not name or not link or not type: raise Exception('NO NAME OR NO LINK OR NO TYPE')
		self.name = name
		self.link = link
		self.type = type

	def __str__(self):
		print(self.name)
		print(self.link)
		print(self.type)