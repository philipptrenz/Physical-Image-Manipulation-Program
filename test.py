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

from skimage import data, color
from skimage.feature import canny
from skimage.transform import hough_ellipse
from skimage.draw import ellipse_perimeter


global WIDTH, HEIGHT

def rgb2gray(rgb_img):
	return numpy.dot(rgb_img[...,:3],[0.2989,0.5870,0.1140])


def ellipseDetection(rgb_img):
	# copy picture, convert to grayscale and detect edges
	image_rgb = numpy.array(rgb_img, copy=True)
	image_gray = color.rgb2gray(image_rgb)
	edges = canny(image_gray, sigma=2.0, low_threshold=0.55, high_threshold=0.8)
	# Perform a Hough Transform
	# The accuracy corresponds to the bin size of a major axis.
	# The value is chosen in order to get a single high accumulator.
	# The threshold eliminates low accumulators
	result = hough_ellipse(edges, accuracy=20, threshold=250, min_size=100, max_size=120)
	result.sort(order='accumulator')
	print(result)

	# Estimated parameters for the ellipse
	#best = list(result[-1])
	#yc, xc, a, b = [int(round(x)) for x in best[1:5]]
	#orientation = best[5]
	"""
	# Draw the ellipse on the original image
	cy, cx = ellipse_perimeter(yc, xc, a, b, orientation)
	image_rgb[cy, cx] = (0, 0, 255)
	# Draw the edge (white) and the resulting ellipse (red)
	edges = color.gray2rgb(edges)
	edges[cy, cx] = (250, 0, 0)"""

def capture():
	with picamera.array.PiRGBArray(camera) as stream:
		camera.capture(stream, format='rgb')
		img = stream.array
		im = Image.fromarray(img)#.convert('LA')
		im.save('./tmp.png')

		#original_img = numpy.array(img, copy=True)
		#gray_img = rgb2gray(img)
		ellipseDetection(img)

	#result = hough_ellipse(gray_img, min_size=15, max_size=90)
	#print('detected')
	#result.tolist()
	#print(result)

if __name__ == '__main__':
	camera = picamera.PiCamera()

	app = QApplication(sys.argv)

	screen_rect = app.desktop().screenGeometry()
	WIDTH, HEIGHT = screen_rect.width(), screen_rect.height()

	viewer = FreakingQtImageViewer(capture)
	sys.exit(app.exec_())