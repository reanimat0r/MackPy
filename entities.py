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
		return '-' * 30 + '\n' + self.name + '\n' + self.link + '\n\t'.join([str(t) for t in self.topicos]) + '-' * 30


class Topico:
	def __init__(self, name):
		if not name: raise Exception('NO NAME')
		self.name = name
		self.subtopicos = []

	def all_tarefas(self):
		return [st.tarefas for st in self.subtopicos]

	def __str__(self):
		return '-' * 20 + '\n' + self.name + '\n\t'.join([str(st) for st in self.subtopicos]) + '-' * 20


class Subtopico:
	def __init__(self, name, link, type):
		if not name or not link or not type: raise Exception('NO NAME OR NO LINK OR NO TYPE')
		self.name = name
		self.link = link
		self.tarefas = []  # order by date?

	def __str__(self):
		return '-' * 10 + '\n' + self.name + '\n' + self.link + '\n\t'.join(
			[str(trf) for trf in self.tarefas]) + '-' * 10


class Tarefa:
	def __init__(self):
		self.info = {}

	def __len__(self):
		return len(self.info)

	def __str__(self):
		return json.dumps(self.info, ensure_ascii=False, indent=4)
