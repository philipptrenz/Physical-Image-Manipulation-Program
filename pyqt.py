#! /usr/bin/python3 

import sys
import time
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, 
    QLabel, QApplication, QPushButton)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QObject
import threading


class FreakingQtImageViewer(QWidget):

	cam = 1

	def refresh_thread(self):
		while self.running:
			self.function()

			pixmap = QPixmap("tmp.png")
			pixmap = pixmap.scaledToWidth(800)
			self.lbl.setPixmap(pixmap)
			time.sleep(0.5)

	def __init__(self, function):
		super().__init__()
		self.function = function
		self.running = False
		self.initUI(function)


	def refreshCam(self):
	cam = 1
		if not self.running:
			self.thread = threading.Thread(name='refresh_image', target=self.refresh_thread)
			self.running = True
			self.thread.start()
		else:
			self.running = False

	def refreshFile(self):
		cam = 0
		if not self.running:
			self.thread = threading.Thread(name='refresh_image', target=self.refresh_thread)
			self.running = True
			self.thread.start()
		else:
			self.running = False

	def initUI(self, function):

		hbox = QVBoxLayout(self)

		self.lbl = QLabel(self)

		btn = QPushButton(self)
		btn.setText('Kamera')
		btn.clicked.connect(self.refreshCam)
		
		btn2 = QPushButton(self)
		btn2.setText('Datei')
		btn2.clicked.connect(self.refreshFile)

		hbox.addWidget(self.lbl)
		hbox.addWidget(btn)
		hbox.addWidget(btn2)
		self.setLayout(hbox)

		self.move(300, 200)
		self.setWindowTitle('Freaking Qt Image Viewer')
		self.show()





