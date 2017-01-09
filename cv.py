#!/usr/bin/env python3

import sys, io, os, time, threading

import numpy
import scipy.misc
from skimage import color
from skimage.io import imread
from skimage.util import img_as_ubyte
from skimage.feature import canny, peak_local_max
from skimage.transform import hough_ellipse, hough_circle
from skimage.draw import ellipse_perimeter, circle_perimeter


def detect_colored_circles(rgb_img, radius_range, hsv_color_ranges, debug=False):
	"""
	TODO: Desicption
	"""

	min_radius, max_radius = radius_range

	start_all = time.time()
	save_image('0_photo', rgb_img)


	# convert image to gray
	print('convert rgb image to grayscale ...')
	start = time.time()
	gray_img = rgb2gray(rgb_img)
	print('finished, duration: ',time.time()-start,'seconds')
	print()


	# find edges in image
	print('find edges in grayscale image ...')
	start = time.time()
	edges_img = canny(gray_img, sigma=15.0, low_threshold=0.55, high_threshold=0.8)
	print('finished, duration: ',time.time()-start,'seconds')
	save_image('1_edges', edges_img)
	print()
	

	# find circles from edge_image
	print('find circles in image ...')
	start = time.time()
	hough_radii, hough_res = find_circles(edges_img, min_radius, max_radius)
	print('finished, duration: ',time.time()-start,'seconds')
	print("#Circles: ", count_circles_of_2d_array(hough_res))
	print()


	# 
	print('eliminating with peak_local_max ...')
	start = time.time()
	centers, accums = find_best_circles(hough_radii, hough_res, circles_per_area=16)
	print('finished, duration: ',time.time()-start,'seconds')
	print("#Circles: ", len(accums))
	print()


	# hsv color debug
	if debug: debug_points(centers, accums, rgb_img)


	print('finding coordinates by color of circles ...')
	start = time.time()
	color_coords_dictionary, debug_img = find_circles_by_color(centers, accums, rgb_img, hsv_color_ranges)
	print('finished, duration: ',time.time()-start,'seconds')



	print('#Circles: ',count_circles_of_dictionary_with_arrays(color_coords_dictionary))
	color_not_found = False
	for key, array in color_coords_dictionary.items():
		print('\t',key,':\t',len(array))
		if len(array) == 0: color_not_found = True
	save_image('2_detected_circles', debug_img)
	print()


	if color_not_found:
		print('less than 4 corners for calibration detected, quitting')
		return None


	print('calculating coordinates by building average of circles with same color ...')
	start = time.time()
	color_coords = calc_coordinate_averages(color_coords_dictionary)
	print('finished, duration: ',time.time()-start,'seconds')
	print()

	print('total duration: ',time.time()-start_all,'seconds')
	print('Coordiantes: ',color_coords)

	return color_coords



def find_circles(edges_img, min_radius, max_radius):
	
	hough_radii = numpy.arange(min_radius, max_radius, 1) # Ellipsen - Radius
	hough_res = hough_circle(edges_img, hough_radii) # gibt für jeden index (radius) koordinaten

	return (hough_radii, hough_res)

def find_best_circles(hough_radii, hough_res, circles_per_area=16):
	"""
	circles_per_area: take the x best circles 		
	"""
	centers = []
	accums = []

	# Alle Kreise unterschiedlicher Radii in ein Array
	# Menge der Kreise reduzieren vor peak_local_max:
	# 	Schmeisse alle heraus, die weniger als 5 mal auftreten
	# 	DANACH schmeisse alle "doppelten" heraus (Abstand < 0.8 * radius)
	for radius, h in zip(hough_radii, hough_res): # iterieren durch circles (h)
		# For each radius, extract num_peaks circles
		peaks = peak_local_max(h, num_peaks=circles_per_area) # beste X kreise fuer radius
		centers.extend(peaks)
		accums.extend(h[peaks[:, 0], peaks[:, 1]]) # wie 'gut' ??
	
	return (centers, accums)


def find_circles_by_color(centers, accums, rgb_img, hsv_color_ranges):

	debug_img = numpy.zeros((len(rgb_img), len(rgb_img[0]), 3), dtype=numpy.uint8)	# start with black image
	coords = { "blue": [], "green": [], "red": [], "white": [] }

	for idx in numpy.argsort(accums)[::-1][:]: # nach quali sortieren (beste x)
		center_y, center_x = centers[idx]
		pixel_color = rgb_img[center_y, center_x]

		# if valid color was found, add it to coords list to specific color key
		found_color = find_colors(pixel_color, hsv_color_ranges, False)	# string of color, 'blue', 'green', 'red' or 'white'
		if found_color is not None: 
			coords[found_color].append(centers[idx])
			debug_img = add_circle_outlines_to_image(debug_img, center_y, center_x, 23, pixel_color) # 23 is radius
		else:
			# draw also all circles not matching the specific colors, but in dark gray
			debug_img = add_circle_outlines_to_image(debug_img, center_y, center_x, 23, (30,30,30))

	return (coords, debug_img)


def calc_coordinate_averages(coord_arrays):
	"""
	Calculate average of all coord touples for the correct color of the corner

	gets: dictionary with color key and value is array of coords in (y,x)
	returns: dictionary with color key and value is array of coords in (x,y)!!!
	"""
	# TODO: Sort out all circles not matching specific pixel range
	coords = {}
	for key, array in coord_arrays.items():
		temp = numpy.average(array, axis=0) 
		coords[key] = (int(temp[1]), int(temp[0]))
	return coords


#########################################################################################################
#########################################################################################################


def add_circle_outlines_to_image(image, center_y, center_x, radius, color):
	"""
	This method draws a outline of a circle with the given position, color and radius to the image
	"""
	# paramters: y, x, radius; returns y, x
	cy, cx = circle_perimeter(center_y, center_x, radius, method='bresenham', shape=(len(image), len(image[0])))
	image[cy, cx] = color
	return image # needed?

def find_colors(pixel_color, hsv_color_ranges, debug=False):
	"""
	This method compares colors to red, green, blue and white
	using the HSV color model to be able to detect colors more or
	less reliable, even for various light situations from a photo

	parameters: triple of rgb values
	returns: string of color ('blue', 'green', 'red', 'white') or None
	"""

	hsv = rgb2hsv(pixel_color)

	couldbe = {}
	for color, color_range in hsv_color_ranges.items():	# for every hsv color range in hsv_color_ranges
		couldbe[color] = 0
		for i in range(0,3): # for every channel
			## if hsv channel between hsv color range_min and range_max
			if color_range[0][i] <= hsv[i] <= color_range[1][i]: couldbe[color] +=1

	# save all colors where score in couldbe is 3, so all channels have matched
	# should not happen, but this is good for debugging the hsv color ranges
	possible_colors = []
	for color, weight in couldbe.items():
		if weight == 3:	# matches all three channels
			possible_colors.append(color)

	if len(possible_colors) == 0:
		if debug: print('COLOR: matches no color\t\t',pixel_color, ' (rgb)\t\t',hsv,'(hsv)')
		return None

	elif len(possible_colors) == 1:
		if debug: print('COLOR: should be', possible_colors[0], '\t\t',pixel_color, ' (rgb)')
		return possible_colors[0]

	elif len(possible_colors) > 1:
		print('COLOR: CONFLICT! matches multiple colors (',possible_colors,')\t\t',pixel_color,' (rgb)\t',hsv,'(hsv)')
		return None

def rgb2hsv(rgb):
	# convert RGB to HSV
	# rgb2hsv just accepts image arrays, so we make an array with one pixel
	x = numpy.zeros((1,1,3))
	x[0,0] = rgb
	return color.rgb2hsv(x)[0][0]

def debug_points(centers, accums, image):
	"""
	This function lists hsv color values of all detected circle centers, sorted by given coord ranges
	"""
	# define areas to search for, there are just temporary correct!
	# don't move camera or monitor when set!
	# ((x_min, y_min)(x_max, y_max))
	searched_range = {	
		'upper_left': ((160, 60), (250, 130)), 
		'lower_left': ((190, 930),  (290, 1020)), 
		'lower_right': ((1060, 900), (1160, 980)), 
		'upper_right': ((1050, 30),  (1140, 110))
	}
	correct_coords = {'upper_left': [], 'lower_left': [], 'lower_right': [], 'upper_right': []}

	# coords is (y,x)
	def in_range(coords, key):
		in_picture = 0 <= coords[0] <= len(image) and 0 <= coords[1] <= len(image[0])
		x_okay = searched_range[key][0][0] <= coords[1] <= searched_range[key][1][0]
		y_okay = searched_range[key][0][1] <= coords[0] <= searched_range[key][1][1]
		return in_picture and x_okay and y_okay

	# iterate over all circles, then look for all 4 positions if coord is in range
	for idx in numpy.argsort(accums)[::-1][:]: # nach quali sortieren (beste x)
		for key, value in searched_range.items():
			if in_range(centers[idx],key): correct_coords[key].append(centers[idx])

	print('\nCOLOR DEBUG:')
	print('\tListing circles depending on in code given ranges')
	print('\tBe careful, has to fit your current setup or picture!')
	for key, coords in correct_coords.items():
		print('\t',key, ' hsv colors:')
		for i in range(len(coords)):
			coord = coords[i]
			print('\t\t',rgb2hsv(image[coord[0], coord[1]]))	# print hsv color of coord in image
	total_circles = len(correct_coords["upper_left"])+len(correct_coords["lower_left"])+len(correct_coords["lower_right"])+len(correct_coords["upper_right"])
	print('\t#Circles: ',total_circles)
	print('\t\t','upper_left',':\t',len(correct_coords['upper_left']))
	print('\t\t','lower_left',':\t',len(correct_coords['lower_left']))
	print('\t\t','lower_right',':\t',len(correct_coords['lower_right']))
	print('\t\t','upper_right',':\t',len(correct_coords['upper_right']))

	print('COLOR DEBUG: END\n')

def count_circles_of_2d_array(array):
	total_circles = 0
	for row in range(len(array)):
		total_circles += len(array[row])
	return total_circles

def count_circles_of_dictionary_with_arrays(dictionary):
	total_circles = 0
	for key, array in dictionary.items():
		total_circles += len(array)
	return total_circles

def rgb2gray(rgb_img):
	"""
	python magic
	converting a rgb image array to grayscale array
	"""
	temp = numpy.array(rgb_img, copy=True)
	return numpy.dot(temp[...,:3],[0.2989,0.5870,0.1140])

def save_image(name, image):
	# save images to file in thread
	def save():
		path = './img/'+name	+'.jpg'
		scipy.misc.imsave(path, image)
	threading.Thread(target=save).start()


#########################################################################################################
#########################################################################################################


if __name__ == '__main__':
	print('NOTE: THIS IS JUST FOR TESTING PURPOSES')
	print('Import the main function via \'from cv import detect_colored_circles\'')
	path = './img/0_photo.jpg'

	radius_range = (20,25) # radius of circles in pixels

	# ((h_min, s_min, v_min),(h_max, s_max, v_max))
	hsv_color_ranges = {
		'blue': ((0.59,0.95,188.),(0.62,1.1,242.)),
		'green': ((0.32,0.98,225.),(0.41,1.1,240.)),
		'red': ((0.97,0.84,210.),(1.0,1.1,250.)),
		'white': ((0.12,0.2,225.),(0.6,0.45,245.))
	}

	rgb_img = imread(path)
	print('points detection from file',path,'with circle radii from',radius_range[0],'to',radius_range[1],'\n') 	
	detect_colored_circles(rgb_img, radius_range, hsv_color_ranges)
