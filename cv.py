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
					print('hsv color: ',x[0,0],' @ ',center_x,center_y,' (x,y)')

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


#########################################################################################################
#########################################################################################################
#########################################################################################################
#########################################################################################################
#########################################################################################################
#########################################################################################################
## NEW # NEW # NEW # NEW # NEW # NEW # NEW # NEW # NEW # NEW # NEW # NEW # NEW # NEW # NEW # NEW # NEW ##




def calibration_points_detection(rgb_img, radMin, radMax, edgesAlready=False):
	"""
	TODO: Desicption
	"""

	# mapping of calibration points and related colors
	calibration_points = {"upper_left":"blue", "lower_left":"green", "lower_right":"red", "upper_right":"white"}
	
	# detect circles on the given rgb_img in the range of radius (from radMin to radMax)
	centers, accums = circle_detection_for_calibration_points(rgb_img, radMin, radMax, edgesAlready)

	print('now sorting out by ignoring special areas in the image and collection after colors')

	# for debug: draw all circles as shapes to new black image
	debug_img = numpy.zeros((1024, 1280, 3), dtype=numpy.uint8)	# start with black image

	coords = { "blue": [], "green": [], "red": [], "white": [] }
	for idx in numpy.argsort(accums)[::-1][:]: # nach quali sortieren (beste x)
		is_accepted_circle = False
		center_y, center_x = centers[idx]
		if(not(center_x > 400 and center_x < 880)): # ignore mid-centers (x)
			if(not(center_y > 304 and center_y < 720)): # ignore mid-centers (y)
				#if(not(center_x >= 1275 or center_y >= 1019 or center_x < 5 or center_y < 5)): # should not longer be needed

				is_accepted_circle = True
				pixel_color = rgb_img[center_y, center_x]

				debug_img = add_circle_outlines_to_image(debug_img, center_y, center_x, 23, pixel_color)
				#print('  accepted circle drawn', center_x, center_y)

				# if valid color was found, add it to coords list to specific color key
				found_color = find_colors(pixel_color)
				if found_color is not None: coords[found_color].append(centers[idx])

		# draw also all unaccepted circles in dark gray
		if not is_accepted_circle:
			debug_img = add_circle_outlines_to_image(debug_img, center_y, center_x, 23, (30,30,30))
			#print('unaccepted circle drawn', center_x, center_y)
					
	# save debug image to file
	scipy.misc.imsave('./circles_detected_debug.png', debug_img)


	if len(coords["blue"]) == 0 or len(coords["green"]) == 0 or len(coords["red"]) == 0 or len(coords["white"]) == 0:
		print('less than 4 corners for calibration detected, returning -1')
		return -1

	# calculate average of all coord touples for the correct color of the  
	# corner, switchit from (y,x) to (x,y) and round the touple values 
	temp = numpy.average(coords[calibration_points["upper_left"]], axis=0) 
	upper_left = (int(temp[1]), int(temp[0]))

	temp = numpy.average(coords[calibration_points["lower_left"]], axis=0) 
	lower_left = (int(temp[1]), int(temp[0]))

	temp = numpy.average(coords[calibration_points["lower_right"]], axis=0) 
	lower_right = (int(temp[1]), int(temp[0]))

	temp = numpy.average(coords[calibration_points["upper_right"]], axis=0) 
	upper_right = (int(temp[1]), int(temp[0]))
	
	# return 
	return numpy.array((upper_left, lower_left, lower_right, upper_right))


def circle_detection_for_calibration_points(rgb_img, radMin, radMax, edgesAlready):

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

	return (centers, accums)

def add_circle_outlines_to_image(image, center_y, center_x, radius, color):
	"""
	This method draws a outline of a circle with the given position, color and radius to the image
	"""
	# paramters: y, x, radius; returns y, x
	cy, cx = circle_perimeter(center_y, center_x, radius, method='bresenham', shape=(len(image), len(image[0])))
	image[cy, cx] = color
	return image # needed?


def find_colors(pixel_color):
	"""
	This method compares colors to red, green, blue and white
	using the HSV color model to be able to detect colors more or
	less reliable, even for various light situations from a photo

	parameters: triple of rgb values
	returns: string of color ('blue', 'green', 'red', 'white') or None
	"""

	# convert RGB to HSV
	# rgb2hsv just accepts image arrays, so we make an array with one pixel
	x = numpy.zeros((1,1,3))
	x[0,0] = pixel_color
	hsv = color.rgb2hsv(x)[0][0]
	#print('hsv color: ',x[0,0])

	# TODO: Check code

	# HSV color range based on experiments
	# be aware that the bigger value of each channel has to be right!!!
	range_blue = ([0,60,185],[4,85,245])
	range_green = ([0,225,0],[4,245,95])
	range_red = ([210,0,0],[250,30,50])
	range_white = ([170,210,135],[250,235,250])

	couldbe = { "blue":0, "green":0, "red":0, "white":0 }

	# check for every channel of the color if the color is in the range of blue, green, ...
	for i in range(0,2):
		if range_blue[0][i] <= hsv[i] <= range_blue[1][i]: couldbe["blue"] += 1
		if range_green[0][i] <= hsv[i] <= range_green[1][i]: couldbe["green"] += 1
		if range_red[0][i] <= hsv[i] <= range_red[1][i]: couldbe["red"] += 1
		if range_white[0][i] <= hsv[i] <= range_white[1][i]: couldbe["white"] += 1

	# save all colors where score in couldbe is 3, so all channels have matched
	# should not happen, but this is good for debugging the hsv color ranges
	possible_colors = []
	for key, value in couldbe.items():
		if value == 3:
			possible_colors.append(key)

	if len(possible_colors) == 0:
		print(pixel_color, ' (rgb) / ',hsv,'(hsv)\t\t not in range of any valid color')
		return None

	elif len(possible_colors) == 1:
		print(pixel_color, ' (rgb) / ',hsv,'(hsv)\t\t should be', possible_colors)
		return possible_colors[0]

	elif len(possible_colors) > 1:
		print('COLOR CONFLICT: ',pixel_color, ' (rgb) / ',hsv,'(hsv)\t\t matches more than one color: ', possible_colors)
		return None



