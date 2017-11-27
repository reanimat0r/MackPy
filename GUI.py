from tkinter import messagebox
import sys
import traceback
from mackapp import Mackenzie
from tkinter import *


class MackenzieGUI():
	def __init__(self):
		self.mackenzie = Mackenzie()
		self.root = Tk()
		self.root.report_callback_exception = lambda *args: messagebox.showinfo(title='Exception:', message=traceback.format_exception(*args))
		self.root.title('MackApp')
		self.size = (800,600)
		self.root.geometry(str(self.size[0])+'x'+str(self.size[1]))
		self.root.protocol("WM_DELETE_WINDOW", sys.exit)
		self.bg = '#F00'
		self.left_frame = Frame(self.root, bg=self.bg)
		self.left_frame.pack(anchor='sw', fill='y', ipadx=self.size[0]/5, expand=True)
		self.materias_list = Listbox(self.left_frame, bg=self.bg)
		self.materias_list.pack(anchor='nw')
		self.startup()
		self.root.mainloop()

	def startup(self):
		# self.mackenzie.login_moodle()
		# try:
		materias = self.mackenzie.get_materias(depth=1)
		print(materias)
		# except Exception as e:
			# messagebox.showinfo(title='Exception:', message=e)




if __name__ == '__main__':

	# gui = MackenzieGUI()