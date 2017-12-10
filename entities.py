class Materia:
	def __init__(self, name, link):
		if not name or not link: raise Exception('NO NAME OR NO LINK')
		self.name = name
		self.link = link
		self.topicos = []

	def __str__(self):
		return '-' * 20+self.name + self.link + '\n'.join(self.topicos)


class Topico:
	def __init__(self, name):
		if not name: raise Exception('NO NAME')
		self.name = name
		self.subtopicos = []

	def __str__(self):
		return '-' * 15 + self.name + '\n'.join(self.subtopicos)


class Subtopico:
	def __init__(self, name, link, type):
		if not name or not link or not type: raise Exception('NO NAME OR NO LINK OR NO TYPE')
		self.name = name
		self.link = link
		self.tarefas = {}  # order by date?

	def __str__(self):
		return '-' * 10 + self.name + self.link + '\n'.join(self.tarefas)


class Tarefa:
	def __init__(self, name, link, type):
		if not name or not link or not type: raise Exception('NO NAME OR NO LINK OR NO TYPE')
		self.name = name
		self.link = link
		self.type = type

	def __str__(self):
		return self.name + self.link + self.type
