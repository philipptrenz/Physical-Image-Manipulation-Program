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


def ellipseDetection(rgb_img):
	# copy picture, convert to grayscale and detect edges
	image_rgb = numpy.array(rgb_img, copy=True)
	print('new image')
	image_gray = rgb2gray(image_rgb)
	print('gray image')
	edges = canny(image_gray, sigma=2.0, low_threshold=10, high_threshold=50)
	print('edges')
	# Perform a Hough Transform
	# The accuracy corresponds to the bin size of a major axis.
	# The value is chosen in order to get a single high accumulator.
	# The threshold eliminates low accumulators
	result = hough_ellipse(edges, accuracy=20, threshold=250, min_size=100, max_size=120)
	print('ellipses')
	result.sort(order='accumulator')
	print('sorted')
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

def circle_detection(rgb_img):
	image_rgb = numpy.array(rgb_img, copy=True)
	print('new image')
	image_gray = rgb2gray(image_rgb)
	print('gray image')
	edges = canny(image_gray, sigma=15.0, low_threshold=0.55, high_threshold=0.8)
	scipy.misc.imsave('outfile.jpg', edges)
	print('edges')
	# Detect two radii
	hough_radii = numpy.arange(30, 80, 1)
	hough_res = hough_circle(edges, hough_radii)
	print('hough_circle finished')
	centers = []
	accums = []
	radii = []

	for radius, h in zip(hough_radii, hough_res):
	    # For each radius, extract two circles
	    num_peaks = 2
	    peaks = peak_local_max(h, num_peaks=num_peaks)
		print('peak_local_max finished')
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