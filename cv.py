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



def rgb2gray(rgb_img):
	return numpy.dot(rgb_img[...,:3],[0.2989,0.5870,0.1140])

def circle_detection(rgb_img, radMin, radMax, edgesAlready=False):
	if not edgesAlready:
		image_rgb = numpy.array(rgb_img, copy=True)
		image_gray = rgb2gray(image_rgb)
		print('to gray image converted')
		edges = canny(image_gray, sigma=15.0, low_threshold=0.55, high_threshold=0.8)
		scipy.misc.imsave('outfile.jpg', edges)
		print('to edges image converted')
	else:
		edges = rgb_img
		image_rgb = numpy.array(edges, copy=True)
	# Detect two radii
	hough_radii = numpy.arange(radMin, radMax, 1) # Ellipsen - Radius
	hough_res = hough_circle(edges, hough_radii) # gibt für jeden index (radius) koordinaten
	num = 0
	sum = 0
	while num < 5:
		sum += len(hough_res[num])
		num = num + 1
	print("#Circles: ", sum)
	print('now sorting out with peak_local_max ...')
	centers = []
	accums = []
	count = 0
	num_peaks = 16
	# Alle Kreise unterschiedlicher Radii in ein Array
	# Menge der Kreise reduzieren vor peak_local_max:
	# 	Schmeisse alle heraus, die weniger als 5 mal auftreten
	# 	DANACH schmeisse alle "doppelten" heraus (Abstand < 0.8 * radius)
	
	for radius, h in zip(hough_radii, hough_res): # iterieren durch circles (h)
		# For each radius, extract num_peaks circles
		peaks = peak_local_max(h, num_peaks=num_peaks) # beste 8 kreise fuer radius
		count += 1
		#print('peak_local_max finished ', count)
		centers.extend(peaks)
		#print('extend1')
		accums.extend(h[peaks[:, 0], peaks[:, 1]]) # wie 'gut' ??
		#print('extend2')
	
	print("#Circles: ", len(accums))
	print('now sorting out by ignoring special areas in the image ...')
	
	# debug -->
	# for debug: draw all circles as shapes to image
	# 1. new image
	offset = 0
	debug_img = numpy.zeros((1024+2*offset, 1280+2*offset, 3), dtype=numpy.uint8)
	image_shape=(1024+2*offset, 1280+2*offset)
	# debug -->

	###
	### worked @ commit: bb7b4ee4e1c8249f449ffcdcee95d05fd5523d00
	###

	###
	# Definitions for color detection
	#



	###

	accepted_centers = []
	for idx in numpy.argsort(accums)[::-1][:]: # nach quali sortieren (beste x)
		is_accepted_circle = False
		center_y, center_x = centers[idx]
		if(not(center_x > 400 and center_x < 880)): # ignore mid-centers (x)
			if(not(center_y > 304 and center_y < 720)): # ignore mid-centers (y)
				if(not(center_x >= 1275 or center_y >= 1019 or center_x < 5 or center_y < 5)):
					is_accepted_circle = True
					accepted_centers.append(centers[idx])

					# debug -->
					# paramters: y, x, radius; returns y, x
					cy, cx = circle_perimeter(center_y+offset, center_x+offset, 23, method='bresenham', shape=image_shape)
					pixel_color = image_rgb[center_y, center_x]
					debug_img[cy, cx] = pixel_color
					#print('  accepted circle drawn', center_x, center_y)
					# <-- debug end

					# HSV color test

					x = numpy.zeros((1,1,3)) # Make a 10 by 20 by 30 array
					x[0,0] = pixel_color
					hsv = color.rgb2hsv(x)
					print('hsv color: ',x[0,0])

					# end

		# debug -->
		# draw also all unaccepted circles
		if not is_accepted_circle:
			# paramters: y, x, radius; returns x, y
			cx, cy = circle_perimeter(center_y+offset, center_x+offset, 23, method='bresenham', shape=image_shape)
			debug_img[cx, cy] = (30,30,30)
			#print('unaccepted circle drawn', center_x, center_y)
		# <-- debug end
					
	print("#Circles: ", len(accepted_centers))
	# debug -->
	scipy.misc.imsave('./circles_detected_debug.png', debug_img)
	# <-- debug end

	if (len(accepted_centers) == 0):
		print('no f***ing circle, damn ...')
		return

	return (image_rgb, accepted_centers)
