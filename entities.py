import json


class Materia:
	def __init__(self, name, link):
		if not name or not link: raise Exception('NO NAME OR NO LINK')
		self.name = name
		self.link = link
		self.topicos = []

	def all_tarefas(self):
		return [t.all_tarefas() for t in self.topicos]

	def __str__(self):
		return '\n\t' + self.name + '\n\t' + self.link + '\n\t'.join([str(t) for t in self.topicos]) + '\n'


class Topico:
	def __init__(self, name):
		if not name: raise Exception('NO NAME')
		self.name = name
		self.subtopicos = []

	def all_tarefas(self):
		return [st.tarefas for st in self.subtopicos]

	def __str__(self):
		return '\n\t' + self.name + '\n\t\t'.join([str(st) for st in self.subtopicos]) + '\n'


class Subtopico:
	def __init__(self, name, link, type):
		if not name or not link or not type: raise Exception('NO NAME OR NO LINK OR NO TYPE')
		self.name = name
		self.link = link
		self.type = type
		self.tarefas = []  # order by date?

	def __str__(self):
		return '\n\t\t' + self.name +\
		       '\n\t\t' + self.link +\
		       '\n\t\t' + self.type +\
		       '\n\t\t\t'.join([str(trf) for trf in self.tarefas]) + '\n\t\t'


class Tarefa:
	def __init__(self):
		self.info = {}

	def __len__(self):
		return len(self.info)

	def __str__(self):
		return json.dumps(self.info, ensure_ascii=False, indent=4)
