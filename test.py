#!/usr/bin/env python3

import sys
import io
import os

import time
from time import sleep

import numpy
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


global WIDTH, HEIGHT, CELL_SIZE, CELLS_PER_ROW = 8

def rgb2gray(rgb_img):
	return numpy.dot(rgb_img[...,:3],[0.2989,0.5870,0.1140])

def circle_detection(rgb_img, edgesAlready=False):
	if not edgesAlready:
		image_rgb = numpy.array(rgb_img, copy=True)
		print('new image')
		image_gray = rgb2gray(image_rgb)
		print('gray image')
		edges = canny(image_gray, sigma=15.0, low_threshold=0.55, high_threshold=0.8)
		scipy.misc.imsave('outfile.jpg', edges)
		print('edges')
	else:
		edges = rgb_img
		image_rgb = numpy.array(edges, copy=True)
	# Detect two radii
	hough_radii = numpy.arange(45, 60, 1) # Ellipsen - Radius
	hough_res = hough_circle(edges, hough_radii) # gibt für jeden index (radius) koordinaten
	num = 0
	sum = 0
	while num < 15:
		sum += len(hough_res[num])
		num = num + 1
	print("#Circles: ", sum)
	centers = []
	accums = []
	radii = []
	count = 0
	num_peaks = 8
	count2 = 0
	# Alle Kreise unterschiedlicher Radii in ein Array
	# Menge der Kreise reduzieren vor peak_local_max:
	# 	Schmeisse alle heraus, die weniger als 5 mal auftreten
	# 	DANACH schmeisse alle "doppelten" heraus (Abstand < 0.8 * radius)
	
	for radius, h in zip(hough_radii, hough_res): # iterieren durch circles (h)
		# For each radius, extract 8 circles
		peaks = peak_local_max(h, num_peaks=num_peaks) # beste 8 kreise fuer radius
		count = count + 1
		print('peak_local_max finished ', count)
		centers.extend(peaks)
		print('extend1')
		accums.extend(h[peaks[:, 0], peaks[:, 1]]) # wie 'gut' ??
		print('extend2')
		radii.extend([radius] * num_peaks)
		print('extend3')
		count2 = count2 + 1
	print('erste loop: ', count2)
	count2 = 0
	print('loop 1 ',len(accums))
	for idx in numpy.argsort(accums)[::-1][:]: # nach quali sortieren (beste 10)
		count2 = count2 + 1
		center_x, center_y = centers[idx]
		radius = radii[idx]
		print('radius: ' + str(radius))
		cx, cy = circle_perimeter(center_y, center_x, radius)
		if edgesAlready:
			image_rgb[cy, cx] = 50
		else: 
			image_rgb[cy, cx] = (220, 20, 20)
	print('done -> ', count2)
	return image_rgb
	

def capture(cam):
	if cam:
		import picamera
		import picamera.array
		camera = picamera.PiCamera()
		with picamera.array.PiRGBArray(camera) as stream:
			camera.capture(stream, format='rgb')
			img = stream.array
			img = circle_detection(img)
			im = Image.fromarray(img) #.convert('LA')
			im.save('./tmp.png')
			camera.close()
	else:
			img = numpy.asarray(Image.open("./outfile.jpg"))
			img = circle_detection(img, True)
			im = Image.fromarray(img) #.convert('LA')
			im.save('./tmp.png')
		

if __name__ == '__main__':

	app = QApplication(sys.argv)

	screen_rect = app.desktop().screenGeometry()
	WIDTH, HEIGHT, CELL_SIZE = screen_rect.width(), screen_rect.height(), WIDTH / CELLS_PER_ROW
	
	

	viewer = FreakingQtImageViewer(capture)
	sys.exit(app.exec_())
	
	
	
	
def circle_detection_old(rgb_img, edgesAlready=False):
	if not edgesAlready:
		image_rgb = numpy.array(rgb_img, copy=True)
		print('new image')
		image_gray = rgb2gray(image_rgb)
		print('gray image')
		edges = canny(image_gray, sigma=15.0, low_threshold=0.55, high_threshold=0.8)
		scipy.misc.imsave('outfile.jpg', edges)
		print('edges')
	else:
		edges = rgb_img
		image_rgb = numpy.array(edges, copy=True)
	# Detect two radii
	hough_radii = numpy.arange(45, 60, 1) # Ellipsen - Radius
	hough_res = hough_circle(edges, hough_radii) # gibt für jeden index (radius) koordinaten
	num = 0
	sum = 0
	while num < 15:
		sum += len(hough_res[num])
		num = num + 1
	print("#Circles: ", sum)
	centers = []
	accums = []
	radii = []
	count = 0
	num_peaks = 8
	count2 = 0
	for radius, h in zip(hough_radii, hough_res): # iterieren durch circles (h)
		# For each radius, extract 8 circles
		peaks = peak_local_max(h, num_peaks=num_peaks) # beste 8 kreise fuer radius
		count = count + 1
		print('peak_local_max finished ', count)
		centers.extend(peaks)
		print('extend1')
		accums.extend(h[peaks[:, 0], peaks[:, 1]]) # wie 'gut' ??
		print('extend2')
		radii.extend([radius] * num_peaks)
		print('extend3')
		count2 = count2 + 1
	print('erste loop: ', count2)
	count2 = 0
	print('loop 1 ',len(accums))
	for idx in numpy.argsort(accums)[::-1][:]: # nach quali sortieren (beste 10)
		count2 = count2 + 1
		center_x, center_y = centers[idx]
		radius = radii[idx]
		print('radius: ' + str(radius))
		cx, cy = circle_perimeter(center_y, center_x, radius)
		if edgesAlready:
			image_rgb[cy, cx] = 50
		else: 
			image_rgb[cy, cx] = (220, 20, 20)
	print('done -> ', count2)
	return image_rgb