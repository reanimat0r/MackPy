# -*- coding: utf-8 -*-
from util import *
import logging
import json
import threading
from hashlib import sha1 # deprecated but fukkit dans fast
import os.path
from collections import OrderedDict
LOG = logging.getLogger(__name__)

def myhash(o): # builtin hash function uses id function which depends on memory location which depends on ToE
        return sha1(o.encode('utf-8')).hexdigest()

class Aluno:
        def __init__(self, tia, senha):
                self.tia = tia
                self.senha = senha

class Materia: # adc nom prof
        def __init__(self, name, link):
                if not name or not link: raise Exception('NO MATERIA NAME OR NO LINK')
                self.name = name
                self.link = link
                self.professor = None
                self.topicos = []

        def all_tarefas(self):
                all_tarefas_ = []
                for t in self.topicos:
                    all_tarefas_.extend(t.all_tarefas()[:])
                for t in all_tarefas_:
                    t.due_date = parse_datetime_moodle(t.info['Data de entrega'])
                    t.info[self.name] = t.link
                return sorted(all_tarefas_,key=lambda t: t.due_date)

        def hash(self):
                hashes = ''
                hashes += hash(self.name)
                hashes += hash(self.link)
                for t in self.topicos: hashes += t.hash()
                return hash(hashes)

        def __str__(self):
                return '\n\t' + self.name +\
                       '\n\t' + self.link
#                        '\n\t'.join([str(t) for t in self.topicos]) + '\n'


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
            self.info = OrderedDict({'Título':tarefa_name, 'Descrição':tarefa_desc[:140] if len(tarefa_desc) > 140 else tarefa_desc}) # reconsiderar esta merda toda
            self.due_date = None
            self.link = None

        def __len__(self):
            return len(self.info)

        def __hash__(self):
            content = aux_info = dict(self.info)
            content.pop('Tempo restante')
            return hash(frozenset(content.items()))

        def __eq__(self, other):
            if isinstance(other, self.__class__):
                aux_info = dict(self.info)
                other_aux_info = dict(other.info)
                aux_info.pop('Tempo restante')
                other_aux_info.pop('Tempo restante')
                return aux_info == other_aux_info
            else: return False

        def __str__(self):
            return json.dumps(self.info, ensure_ascii=False, indent=4)

class Broadcaster(threading.Thread):
    def __init__(self, bot, con, broadcast_file='broadcast.txt'):
        threading.Thread.__init__(self)
        self.bot = bot
        self.con = con
        self.broadcast_file = broadcast_file

    def get_users(self):
        cur = self.con.cursor()
        return [u[0] for u in cur.execute('SELECT chat_id FROM user').fetchall()]

    def run(self):
        while True:
            if os.path.isfile(self.broadcast_file):
                broadcast_file = open(self.broadcast_file, 'r')
                broadcast = '\n'.join(broadcast_file.readlines())
                if broadcast:
                    for u in self.get_users(): 
                        LOG.debug('Sending broadcast to ' + str(u))
                        self.bot.sendMessage(u, broadcast)
                broadcast_file.close()
                open(self.broadcast_file, 'w').close()

def test_hash():
        m = Materia('a', 'b')
        m.topicos.append(Topico('c'))
        m.topicos[0].subtopicos.append(Subtopico('d', 'e', 'f'))
        m.topicos[0].subtopicos[0].tarefas.append(Tarefa())
        print(m.hash())
