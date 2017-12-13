import json
from hashlib import sha1 # deprecated but fukkit dans fast
from collections import OrderedDict

def hash(o): # builtin hash function uses id function which depends on memory location which depends on ToE
	return sha1(o.encode('utf-8')).hexdigest()

class Aluno:
	def __init__(self, tia, senha):
		self.tia = tia
		self.senha = senha

class Materia:
	def __init__(self, name, link):
		if not name or not link: raise Exception('NO MATERIA NAME OR NO LINK')
		self.name = name
		self.link = link
		self.topicos = []

	def all_tarefas(self):
		all_tarefas = []
		for t in self.topicos:
			all_tarefas.extend(t.all_tarefas())
		return all_tarefas

	def hash(self):
		hashes = ''
		hashes += hash(self.name)
		hashes += hash(self.link)
		for t in self.topicos: hashes += t.hash()
		return hash(hashes)

	def __str__(self):
		return '\n\t' + self.name +\
		       '\n\t' + self.link +\
		       '\n\t'.join([str(t) for t in self.topicos]) + '\n'


class Topico:
	def __init__(self, name):
		if not name: raise Exception('NO TOPICO NAME')
		self.name = name
		self.subtopicos = []

	def all_tarefas(self):
		all_tarefas = []
		for st in self.subtopicos:
			all_tarefas.extend(st.tarefas)
		return all_tarefas

	def hash(self):
		hashes = ''
		hashes += hash(self.name)
		for st in self.subtopicos: hashes+=st.hash()
		return hash(hashes)

	def __str__(self):
		return '\n\t' + self.name +\
		       '\n\t\t'.join([str(st) for st in self.subtopicos]) + '\n'


class Subtopico:
	def __init__(self, name, link, type):
		if not name or not link or not type: raise Exception('NO NAME OR NO LINK OR NO TYPE')
		self.name = name
		self.link = link
		self.type = type
		self.tarefas = []  # order by date?

	def hash(self):
		hashes = ''
		hashes += hash(self.name)
		hashes += hash(self.link)
		hashes += hash(self.type)
		for t in self.tarefas: hashes+= t.hash()
		return hash(hashes)


	def __str__(self):
		return '\n\t\t' + self.name + \
		       '\n\t\t' + self.link + \
		       '\n\t\t' + self.type + \
		       '\n\t\t\t'.join([str(trf) for trf in self.tarefas]) + '\n\t\t'


class Tarefa:
	def __init__(self, tarefa_name, tarefa_desc):
		self.info = {'Título':tarefa_name, 'Descrição':tarefa_desc} # reconsiderar esta merda toda

	def __len__(self):
		return len(self.info)

	def hash(self):
		hashes = ''
		sorted_items = OrderedDict(sorted(self.info.items())).items()
		for k,v in sorted_items:
			hashes+= hash(k)
			hashes+= hash(v)
		return hash(hashes)

	def __str__(self):
		return json.dumps(self.info, ensure_ascii=False, indent=4)


def test_hash():
	m = Materia('a', 'b')
	m.topicos.append(Topico('c'))
	m.topicos[0].subtopicos.append(Subtopico('d', 'e', 'f'))
	m.topicos[0].subtopicos[0].tarefas.append(Tarefa())
	print(m.hash())


# if __name__ == '__main__':
# 	test_hash()
