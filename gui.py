import pickle
import json
from threading import Thread
import colorsys
from tkinter import messagebox
from tkinter import simpledialog

import sys
import traceback
from mackapp import Mackenzie
from tkinter import *


class MackenzieGUI():
	def __init__(self):
		self.mack = Mackenzie()
		self.root = Tk()
		# self.root.report_callback_exception = lambda *args: messagebox.showinfo(title='Exception:',
		#                                                                         message=traceback.format_exception(
		# 	                                                                        *args))
		self.root.title('MackApp')
		self.size = (800, 600)
		self.root.geometry(str(self.size[0]) + 'x' + str(self.size[1]))
		self.root.protocol("WM_DELETE_WINDOW", self.root.withdraw)
		self.bg = '#A00'

		self.left_frame = Frame(self.root, bg=self.bg, width=800, height=self.size[1])
		self.left_frame.grid_propagate(0)
		self.left_frame.grid(column=1, sticky='nsew')

		self.right_frame = Frame(self.root, bg='#000', width=1000, height=1000)
		self.right_frame.grid(row=0, column=2, sticky='nsew')

		self.materias_list = Listbox(self.left_frame, bg=self.bg)
		self.materias_list.grid()

		self.tarefas_list = Listbox(self.left_frame, bg=self.bg)
		self.tarefas_list.bind('<<ListboxSelect>>', self._tarefa_clicked)
		self.tarefas_list.grid(row=0,column=1)

		self.indicator_label = Label(self.left_frame, text='Not logged in')
		self.indicator_label.grid(row=1, column=0, sticky='sw')

		self.current_tarefa_label = Label(self.left_frame, text='')
		self.current_tarefa_label.grid(row=1, column=0, sticky='sw')

		self.root.after(1, self._startup)
		self.root.mainloop()

	def _distinct_colors(self, n):
		tuples = list(map(lambda x: colorsys.hsv_to_rgb(*x), [(x*1.0/n, 0.5, 0.5) for x in range(n)]))
		for ti in range(len(tuples)):
			t = tuples.pop(ti)
			t=(t[0]*255, t[1],t[2])
			tuples.insert(ti, t)
		return sorted(tuples)

	def _startup(self):
		self._UI_update_materias()

	def _tarefa_clicked(self, evt):
		w = evt.widget
		index = int(w.curselection()[0])
		value = w.get(index)
		print(value)

	def _UI_update_materias(self):
		persist = 3
		while len(self.mack.config) < 2 or not self.mack.config['user'] or not self.mack.config['password'] and persist:
			self.mack.config['user'] = simpledialog.askstring('Authentication', 'TIA:')
			self.mack.config['password'] = simpledialog.askstring('Authentication', 'Password:', show='*')
			persist-=1
		self.indicator_label.config(text='Logging in')
		self.mack.login_moodle(v=True)
		if not self.mack.logged_in: self.indicator_label.config(text='Logging in failed')
		self.indicator_label.config(text='Retrieving materias')
		self.materias = self.mack.get_materias(depth=10)
		# horarios = self.mack.get_horarios()
		# notas = self.mack.get_notas()

		for m in self.materias: self.materias_list.insert(0, m)
		for nome_materia,topicos_materia in self.materias.items():
			for k,topico in topicos_materia.items():
				print(k)
				if isinstance(topico, dict):
					for subtopico in topico:
						sub = topico[subtopico]
						if 'Tarefa' in sub: print(sub)
						# for evt in sub:
						# 	print(evt)
				else: print(topico)
				# if nome_topico is not 'link':
				# 	item = topicos[nome_topico]
				# 	if item['type'] == 'Tarefa': self.tarefas_list.insert(0, item)

		self.indicator_label.config(text='Startup done')


	def _is_same_dict(self, d1, d2):
		for k in d1.keys():
			if k not in d2: return False
			else:
				if type(d1[k]) is dict and not self._is_same_dict(d1[k],d2[k]): return False
				elif d1[k] != d2[k]: return False
		return True

if __name__ == '__main__':
	gui = MackenzieGUI()