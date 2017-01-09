#!/usr/bin/env python3

import sys
import io
import os

import time
from time import sleep

import numpy
from PIL import Image

from PyQt5.QtCore import *
import PyQt5.QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import scipy.misc
from skimage import color
from skimage import transform as tf
from skimage.io import imread
from skimage.util import img_as_ubyte
from skimage.feature import canny, peak_local_max
from skimage.transform import hough_ellipse, hough_circle
from skimage.draw import ellipse_perimeter, circle_perimeter

from _thread import start_new_thread

import picamera
import picamera.array

from cv import detect_colored_circles



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
		self.PIX_PADDING = 25
		self.BORDER_RADIUS = 10

		self.rg_bg = (2, 3)

		self.initUI()
		
	def keyPressEvent(self, event):
		if event.key() == Qt.Key_Escape: 
			self.close()
		elif event.key() == Qt.Key_C:
			start_new_thread(self.calibrate, (0, 0,))
		elif event.key() == Qt.Key_V:

			self.vbox.setContentsMargins(self.upper_left[0] + 10,self.PIX_PADDING + 10,240,112)
			self.pixmap = QPixmap("./src/board.jpg")
			self.pixmap = self.pixmap.scaledToWidth( self.upper_right[0]-self.upper_left[0] )
			'''
			self.painter.drawEllipse(self.upper_left[0]-10,self.upper_left[1]-10,20,20)
			self.painter = QPainter(self.pixmap)
			self.DEFAULT_PEN.setColor(self.WHITE_COLOR)
			self.painter.setPen(self.DEFAULT_PEN)
			self.painter.drawEllipse(self.upper_right[0]-10,self.upper_right[1]-10,20,20)
			self.DEFAULT_PEN.setColor(self.RED_COLOR)
			self.painter.setPen(self.DEFAULT_PEN)
			self.painter.drawEllipse(self.lower_right[0]-10,self.lower_right[1]-10,20,20)
			self.DEFAULT_PEN.setColor(self.GREEN_COLOR)
			self.painter.setPen(self.DEFAULT_PEN)
			self.painter.drawEllipse(self.lower_left[0]-10,self.lower_left[1]-10,20,20)
			'''
			
			self.lbl.setPixmap(self.pixmap)
			self.lbl.repaint()

		elif event.key() == Qt.Key_S:

			##############################################
			# find 
			# 
			# 
			##############################################

			start_new_thread(self.findTiles, (0, 0,))

		elif event.key() == Qt.Key_P:

			##############################################
			# shoot with defined white balance mode
			# 
			# capture image with defined self.rg_bg and show
			##############################################

			camera = picamera.PiCamera()

			# test manual white balance
			camera.awb_mode = 'off'
			camera.awb_gains = self.rg_bg
			# end

			with picamera.array.PiRGBArray(camera) as stream:
				camera.capture(stream, format='rgb')
				im = Image.fromarray(stream.array)
				scipy.misc.imsave('./0_photo.jpg', im)				
				camera.close()
				os.system('xdg-open ./0_photo.jpg')

		elif event.key() == Qt.Key_T:

			##############################################
			# test white balance modi 
			# 
			# iterate through various combinations of wb
			##############################################

			camera = picamera.PiCamera()
			camera.awb_mode = 'off'

			rg_bg = (2, 3)

			for rg in range(0,20):
				for bg in range(0,20):

					rg_x=rg/10
					bg_x=bg/10

					camera.awb_gains = (rg_x,bg_x)
					with picamera.array.PiRGBArray(camera) as stream:
						camera.capture(stream, format='rgb')
						im = Image.fromarray(stream.array)
						im.save('./preview_'+str(rg_x)+'_'+str(bg_x)+'.png')				

			camera.close()

			self.vbox.setContentsMargins(self.upper_left[0] + 10,self.PIX_PADDING + 10,240,112)
			self.pixmap = QPixmap("./src/board.jpg")
			self.pixmap = self.pixmap.scaledToWidth( self.upper_right[0]-self.upper_left[0] )			
			self.lbl.setPixmap(self.pixmap)
			self.lbl.repaint()


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

		self.painter.fillRect(0, 0,self.WIDTH, self.HEIGHT, self.BLACK_COLOR)
		self.painter.drawEllipse(self.upper_left[0]-10,self.upper_left[1]-10,20,20)
		self.DEFAULT_PEN.setColor(self.WHITE_COLOR)
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
		
		self.setStyleSheet("background-color:black;")
		
		self.setLayout(self.vbox)
		self.vbox.setAlignment(Qt.AlignHCenter)
		self.showFullScreen()
		self.setWindowTitle('DraughtsCV')
		self.show()
		
	def calibrate(self, ignore1, ignore2): # pythonmaster
		camera = picamera.PiCamera()

		#while True:
		with picamera.array.PiRGBArray(camera) as stream:
			camera.capture(stream, format='rgb')
			img = stream.array
			camera.close()


			#radius_range = (20,25) # radius of circles in pixels, from min to max
			radius_range = (42,48)
			# ((h_min, s_min, v_min),(h_max, s_max, v_max))

			hsv_color_ranges = {
				'blue': ((0.52,0.85,120.),(0.56,0.95,130.)),		# upper left circle
				'green': ((0.25,0.55,125.),(0.29,0.63,132.)),	# lower left circle
				'red': ((0.96,0.72,140.),(1.,0.79,154.)),		# lower right circle
				'black': ((0.05,0.19,40.),(0.15,0.30,50.))		# upper right circle
			}

			circle_coords = detect_colored_circles(img, radius_range, hsv_color_ranges, debug=True)

			if circle_coords is not None:

				self.calibrationPoints = numpy.array((circle_coords['blue'], circle_coords['green'], circle_coords['red'], circle_coords['black']))

				src = numpy.array((
					(0, 0), #upper left
					(0, 800), #lower left
					(800, 800), #lright
					(800, 0) #uright
				))

				test_image = imread('./src/board.jpg')
			
				transformer = tf.ProjectiveTransform()
				transformer.estimate(src, self.calibrationPoints)
				transformed_image = tf.warp(test_image, transformer, output_shape = (1280,1024))
				
				#print("Transformed Image: ",transformed_image)

				
				scipy.misc.imsave('./img/3_transformed.jpg', transformed_image)
				#break
			else: print('try it again ...')
		print(self.corners)

	# 
	# Detect draughts tiles (german: Spielstein) at the field
	#
	def findTiles(self, ignore1, ignore2): # pythonmaster

		if isinstance(self.calibrationPoints, (numpy.ndarray, numpy.generic) ):

			camera = picamera.PiCamera()

			# test manual white balance
			#camera.awb_mode = 'off'
			#camera.awb_gains = self.rg_bg
			# end

			with picamera.array.PiRGBArray(camera) as stream:
				camera.capture(stream, format='rgb')
				img = stream.array
				camera.close()

				src = numpy.array((
					(0, 0), #upper left
					(0, 800), #lower left
					(800, 800), #lright
					(800, 0) #uright
				))
				
				transformer = tf.ProjectiveTransform()
				transformer.estimate(src, self.calibrationPoints)
				board_image = tf.warp(img, transformer, output_shape = (800,800))

				scipy.misc.imsave('./board.jpg', board_image)
			
			print('board image captured')

		else:
			print('calibrationPoints not yet set')

if __name__ == '__main__':

	app = QApplication(sys.argv)

	screen_rect = app.desktop().screenGeometry()
	viewer = DraughtsGameWindow() # init ui
	sys.exit(app.exec_())