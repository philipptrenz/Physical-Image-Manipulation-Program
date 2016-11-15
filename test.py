#!/usr/bin/env python3

import sys
import io
import os
import picamera

import time
from time import sleep

import numpy
import picamera.array
import matplotlib
from PIL import Image

from PyQt5.QtWidgets import QApplication
from pyqt import FreakingQtImageViewer

from skimage.transform import hough_ellipse
from skimage.filters import roberts, sobel, scharr, prewitt

global WIDTH, HEIGHT

def rgb2gray(rgb_img):
	gray_img = []
	numpy.dot(rgb_img[...,:3],[0.2989,0.5870,0.1140], gray_img)
	return gray_img

def capture():
	with picamera.array.PiRGBArray(camera) as stream:
		camera.capture(stream, format='rgb')
		img = stream.array
	im = Image.fromarray(img)#.convert('LA')
	gray_img = rgb2gray(img)
	im.save('./tmp.png')

	result = hough_ellipse(gray_img, min_size=15, max_size=90)
	print('detected')
	result.tolist()
	print(result)

if __name__ == '__main__':
	camera = picamera.PiCamera()

	app = QApplication(sys.argv)

	screen_rect = app.desktop().screenGeometry()
	WIDTH, HEIGHT = screen_rect.width(), screen_rect.height()

	viewer = FreakingQtImageViewer(capture)
	sys.exit(app.exec_())