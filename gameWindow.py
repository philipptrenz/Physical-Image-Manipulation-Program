#!/usr/bin/env python3

import sys
import io
import os

import time
from time import sleep

import numpy
import matplotlib
from PIL import Image
from PyQt5.QtCore import *
import PyQt5.QtCore
from PyQt5.QtGui import *

from PyQt5.QtWidgets import *

from pyqt import FreakingQtImageViewer

from skimage import color
#from skimage import data
from skimage.feature import canny
from skimage.transform import hough_ellipse
from skimage.draw import ellipse_perimeter

from skimage.transform import hough_circle
from skimage.feature import peak_local_max
from skimage.draw import circle_perimeter
from skimage.util import img_as_ubyte

import scipy.misc


import picamera
import picamera.array

from cv import circle_detection


class DraughtsGameWindow(QWidget):
	def __init__(self):
		super().__init__()
		self.corners = []
		self.CELLS_PER_ROW = 8
		self.BLACK_COLOR = QColor(0,0,0,255)
		self.WHITE_COLOR = QColor(255,255,255,255)
		self.BLUE_COLOR = QColor(0,0,255,255)
		self.RED_COLOR = QColor(255,0,0,255)
		self.GREEN_COLOR = QColor(0,255,0,255)
		self.DEFAULT_PEN = QPen(self.BLUE_COLOR)
		self.DEFAULT_PEN.setWidth(20)
		self.PIX_PADDING = 75
		self.BORDER_RADIUS = 10

		self.initUI()
		
	def keyPressEvent(self, event):
		if event.key() == Qt.Key_Escape: 
			self.close()
		elif event.key() == Qt.Key_C:
			self.capture()
		
	def initUI(self):
		
		self.WIDTH, self.HEIGHT, self.CELL_SIZE = screen_rect.width(), screen_rect.height(), screen_rect.width() / self.CELLS_PER_ROW
		self.pixmap = QPixmap(self.WIDTH-20,self.HEIGHT-20)
		
		self.upper_left = (self.PIX_PADDING + self.WIDTH / 2 - self.pixmap.height() / 2, self.PIX_PADDING)
		self.upper_right = (- self.PIX_PADDING + self.WIDTH / 2 + self.pixmap.height() / 2, self.PIX_PADDING + 0)
		self.lower_right = (-self.PIX_PADDING + self.WIDTH / 2 + self.pixmap.height() / 2, -self.PIX_PADDING + self.pixmap.height())
		self.lower_left = (self.PIX_PADDING + self.WIDTH / 2 - self.pixmap.height() / 2, -self.PIX_PADDING + self.pixmap.height())
		
		self.DRAW_SIZE = self.upper_right[0] - self.upper_left[0]
		print(self.DRAW_SIZE)
		
		self.painter = QPainter(self.pixmap)
		self.painter.setPen(self.DEFAULT_PEN)

		self.painter.fillRect(0, 0,self.WIDTH, self.HEIGHT, self.WHITE_COLOR)
		self.painter.drawEllipse(self.upper_left[0]-10,self.upper_left[1]-10,20,20)
		self.DEFAULT_PEN.setColor(self.BLACK_COLOR)
		self.painter.setPen(self.DEFAULT_PEN)
		self.painter.drawEllipse(self.upper_right[0]-10,self.upper_right[1]-10,20,20)
		self.DEFAULT_PEN.setColor(self.RED_COLOR)
		self.painter.setPen(self.DEFAULT_PEN)
		self.painter.drawEllipse(self.lower_right[0]-10,self.lower_right[1]-10,20,20)
		self.DEFAULT_PEN.setColor(self.GREEN_COLOR)
		self.painter.setPen(self.DEFAULT_PEN)
		self.painter.drawEllipse(self.lower_left[0]-10,self.lower_left[1]-10,20,20)
		
		self.vbox = QVBoxLayout(self)
		
		self.lbl = QLabel(self)
		self.lbl.setPixmap(self.pixmap)
		self.vbox.addWidget(self.lbl)
		
		self.setLayout(self.vbox)
		self.vbox.setAlignment(Qt.AlignHCenter)
		self.showFullScreen()
		self.setWindowTitle('DraughtsCV')
		self.show()
		#capture()
		

	def checkCoords(self, img, coords):
		self.redC = []
		self.greenC = []
		self.blueC = []
		self.blackC = []
		for index, coord in enumerate(coords):
			#print(img[coord[0], coord[1]]," - ", )
			pixel = img[coord[0], coord[1]]
			sum = 0
			sum += pixel[0]
			sum += pixel[1]
			sum += pixel[2]
			if sum > 300:
				print("delete ", coord, ' with ', pixel)
			else:
				if pixel[0] < 50 and pixel[1] < 50 and pixel[2] < 50:
					print(coord, ' could be black with', pixel)
					self.blackC.append(coord)
				elif pixel[0] > 110:
					print(coord, ' could be red with', pixel)
					self.redC.append(coord)
				elif pixel[1] > 110:
					print(coord, ' could be green with', pixel)
					self.greenC.append(coord)
				elif pixel[2] > 110:
					print(coord, ' could be blue with', pixel)
					self.blueC.append(coord)
		
		#final_red = (int(numpy.sum(self.redC[0])/len(self.redC)),int(numpy.sum(self.redC[1])/len(self.redC[])))	#(sum(self.redC[0]), sum(self.redC[1]))
		final_black = numpy.average(self.blackC, axis=0)
		final_red = numpy.average(self.redC, axis=0)
		final_green = numpy.average(self.greenC, axis=0)
		final_blue = numpy.average(self.blueC, axis=0)
		print('avg black ',final_black)
		print('avg red ',final_red)
		print('avg green',final_green)
		print('avg blue ',final_blue)
		
		self.lbl.setPixmap(self.pixmap)
		finalCoords = []
		finalCoords.append(final_blue)
		finalCoords.append(final_black)
		finalCoords.append(final_red)
		finalCoords.append(final_green)
		if len(self.blackC) == 0 or len(self.blueC) == 0 or len(self.greenC) == 0 or len(self.redC) == 0 :
			return -1
		return finalCoords
		
			

	def capture(self):
		camera = picamera.PiCamera()
		res = -1
		while res == -1:
			with picamera.array.PiRGBArray(camera) as stream:
				camera.capture(stream, format='rgb')
				img = stream.array
				img, coords, circleDebug = circle_detection(img, 20, 25)
				im = Image.fromarray(img) #.convert('LA')
				imDeb = Image.fromarray(circleDebug) #.convert('LA')
				im.save('./tmp.png')
				imDeb.save('./deb.png')
				res =  self.checkCoords(img, coords)
		self.corners = res
		camera.close()
		print(self.corners)
		



if __name__ == '__main__':

	app = QApplication(sys.argv)

	screen_rect = app.desktop().screenGeometry()
	viewer = DraughtsGameWindow() # init ui
	# capture
	sys.exit(app.exec_())