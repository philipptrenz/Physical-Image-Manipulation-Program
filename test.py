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


global WIDTH, HEIGHT

def rgb2gray(rgb_img):
	return numpy.dot(rgb_img[...,:3],[0.2989,0.5870,0.1140])

def circle_detection(rgb_img):
	image_rgb = numpy.array(rgb_img, copy=True)
	print('new image')
	image_gray = rgb2gray(image_rgb)
	print('gray image')
	edges = canny(image_gray, sigma=15.0, low_threshold=0.55, high_threshold=0.8)
	scipy.misc.imsave('outfile.jpg', edges)
	print('edges')
	# Detect two radii
	hough_radii = numpy.arange(40, 70, 1)
	hough_res = hough_circle(edges, hough_radii)
	print('hough_circle finished')
	centers = []
	accums = []
	radii = []
	count = 0
	num_peaks = 8

	for radius, h in zip(hough_radii, hough_res): # iterieren durch circles (h)
		# For each radius, extract two circles
		peaks = peak_local_max(h, num_peaks=num_peaks)
		count = count + 1
		print('peak_local_max finished ', count)
		centers.extend(peaks)
		print('extend1')
		accums.extend(h[peaks[:, 0], peaks[:, 1]]) # wie 'gut' ??
		print('extend2')
		radii.extend([radius] * num_peaks)
		print('extend3')
	print('loop 1 ',len(accums))

	for idx in numpy.argsort(accums)[::-1][:20]: # nach quali sortieren (beste 10)
		center_x, center_y = centers[idx]
		radius = radii[idx]
		print('radius: ' + str(radius))
		cx, cy = circle_perimeter(center_y, center_x, radius)
		image_rgb[cy, cx] = (220, 20, 20)
	print('done')
	return image_rgb

def capture():
	with picamera.array.PiRGBArray(camera) as stream:
		camera.capture(stream, format='rgb')
		img = stream.array
		img = circle_detection(img)
		im = Image.fromarray(img)#.convert('LA')
		im.save('./tmp.png')

		#original_img = numpy.array(img, copy=True)
		#gray_img = rgb2gray(img)
		#ellipseDetection(img)

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