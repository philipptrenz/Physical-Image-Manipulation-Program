#!/usr/bin/env python3

import sys, io, os, time, threading

import numpy
import scipy.misc
from skimage import color
from skimage.io import imread
from skimage.util import img_as_ubyte
from skimage.feature import canny, peak_local_max, corner_fast, corner_foerstner, corner_harris, corner_kitchen_rosenfeld, corner_moravec, corner_shi_tomasi
from skimage.transform import hough_ellipse, hough_circle
from skimage.draw import ellipse_perimeter, circle_perimeter
from skimage.filters import roberts, sobel, scharr, prewitt

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
	#edges_img = corner_fast(gray_img, n=9, threshold=1.2)
	#edges_img = corner_foerstner(gray_img)[0]
	#edges_img = corner_harris(gray_img, method='k', k=0.05, eps=1e-06, sigma=1)
	#edges_img = corner_kitchen_rosenfeld(gray_img, mode='constant', cval=0)
	#edges_img = corner_moravec(gray_img, window_size=1)
	#edges_img = corner_shi_tomasi(gray_img, sigma=0.1)
	#edges_img = roberts(gray_img)
	#edges_img = sobel(gray_img)
	#edges_img = scharr(gray_img)
	#edges_img = prewitt(gray_img)
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
	centers, accums, radii = circles_per_radiuss(hough_radii, hough_res, circles_per_area=16)
	print('finished, duration: ',time.time()-start,'seconds')
	print("#Circles: ", len(accums))
	print()


	# hsv color debug
	if debug: debug_points(centers, accums, rgb_img)


	print('finding coordinates by color of circles ...')
	start = time.time()
	color_coords_dictionary, debug_img = find_circles_by_color(centers, accums, radii, rgb_img, hsv_color_ranges, debug)
	print('finished, duration: ',time.time()-start,'seconds')



	print('#Circles: ',count_circles_of_dictionary_with_arrays(color_coords_dictionary))
	color_not_found = False
	for key, array in color_coords_dictionary.items():
		print('\t',key,':\t',len(array))
		if len(array) == 0: color_not_found = True
	save_image('2_detected_circles', debug_img)
	print()

	print('total duration: ',time.time()-start_all,'seconds')
	print()

	if color_not_found:
		print('less than 4 corners for calibration detected, quitting')
		return None

	color_coords = calc_coordinate_averages(color_coords_dictionary)
	print('Coordiantes: ',color_coords)
	return color_coords

def detect_colored_circles_no_prints(rgb_img, radius_range, hsv_color_ranges, debug=False):
	"""
	TODO: Desicption
	"""

	min_radius, max_radius = radius_range

	# convert image to gray
	gray_img = rgb2gray(rgb_img)

	# find edges in image
	edges_img = canny(gray_img, sigma=15.0, low_threshold=0.55, high_threshold=0.8)

	# find circles from edge_image
	hough_radii, hough_res = find_circles(edges_img, min_radius, max_radius)

	# 
	centers, accums, radii = circles_per_radiuss(hough_radii, hough_res, circles_per_area=16)

	color_coords_dictionary, debug_img = find_circles_by_color(centers, accums, radii, rgb_img, hsv_color_ranges, debug)

	color_not_found = False
	for key, array in color_coords_dictionary.items():
		if len(array) == 0: color_not_found = True

	if color_not_found:
		print('less than 4 corners for calibration detected, quitting')
		return None

	color_coords = calc_coordinate_averages(color_coords_dictionary)
	return color_coords

def find_circles(edges_img, min_radius, max_radius):
	
	hough_radii = numpy.arange(min_radius, max_radius, 1) # Liste von Radii von min_radius bis max_radius in Schritten von 1
	hough_res = hough_circle(edges_img, hough_radii) # gibt für jeden index (radius) koordinaten

	return (hough_radii, hough_res)

def circles_per_radiuss(hough_radii, hough_res, circles_per_area=16):
	"""
	circles_per_area: take the x best circles 		
	"""
	centers = []
	accums = []
	radii = []

	# Alle Kreise unterschiedlicher Radii in ein Array
	# Menge der Kreise reduzieren vor peak_local_max:
	# 	Schmeisse alle heraus, die weniger als 5 mal auftreten
	# 	DANACH schmeisse alle "doppelten" heraus (Abstand < 0.8 * radius)
	for radius, h in zip(hough_radii, hough_res): # iterieren durch circles (h)
		# For each radius, extract num_peaks circles
		peaks = peak_local_max(h, num_peaks=circles_per_area) # beste X kreise fuer radius
		centers.extend(peaks)
		accums.extend(h[peaks[:, 0], peaks[:, 1]]) # wie 'gut' ??
		radii.extend([radius] * circles_per_area)
		#
	
	return (centers, accums, radii)

def find_circles_by_color(centers, accums, radii, rgb_img, hsv_color_ranges, debug):

	debug_img = numpy.zeros((len(rgb_img), len(rgb_img[0]), 3), dtype=numpy.uint8)	# start with black image
	coords = {}
	for color, array in hsv_color_ranges.items():	# initialize coords 
		coords[color] = []

	for idx in numpy.argsort(accums)[::-1][:]: # nach quali sortieren (beste x)
		center_y, center_x = centers[idx]
		pixel_color = rgb_img[center_y, center_x]
		# if valid color was found, add it to coords list to specific color key
		found_color = find_colors(pixel_color, hsv_color_ranges, debug)	# string of color, 'blue', 'green', 'red' or 'white'
		if found_color is not None: 
			coords[found_color].append(centers[idx])
			debug_img = add_circle_outlines_to_image(debug_img, center_y, center_x, radii[idx], pixel_color) 
		else:
			if debug:
				# draw also all circles not matching the specific colors, but in dark gray
				debug_img = add_circle_outlines_to_image(debug_img, center_y, center_x, radii[idx], (255,255,255))
				print('@ coord (x,y)', center_x, ', ', center_y, '\n')

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
			if color_range[0][i] > color_range[1][i]:
				# its red, so from 0 to max or min to 1
				if (0. <= hsv[i] <= color_range[1][i]) or (color_range[0][i] <= hsv[i] <= 1.): couldbe[color] += 1
			else:
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

def debug_points(centers, accums, image, searched_range=None):
	"""
	This function lists hsv color values of all detected circle centers, sorted by given coord ranges
	"""
	# define areas to search for, there are just temporary correct!
	# don't move camera or monitor when set!
	# ((x_min, y_min)(x_max, y_max))
	if searched_range is None:
		searched_range = {	
			'upper_left': ((240, 110), (290, 150)), 
			'lower_left': ((170, 360),  (220, 400)), 
			'lower_right': ((400, 340), (450, 390)), 
			'upper_right': ((510, 150),  (560, 190))
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


def calibrate_colors(rgb_img, radius_range, searched_range):
	min_radius, max_radius = radius_range

	# convert image to gray
	gray_img = rgb2gray(rgb_img)

	# find edges in image
	edges_img = canny(gray_img, sigma=15.0, low_threshold=0.55, high_threshold=0.8)

	# find circles from edge_image
	hough_radii, hough_res = find_circles(edges_img, min_radius, max_radius)

	# 
	centers, accums, radii = circles_per_radiuss(hough_radii, hough_res, circles_per_area=16)

	def in_range(coords, key):
		in_picture = 0 <= coords[0] <= len(rgb_img) and 0 <= coords[1] <= len(rgb_img[0])
		x_okay = searched_range[key][0][0] <= coords[1] <= searched_range[key][1][0]
		y_okay = searched_range[key][0][1] <= coords[0] <= searched_range[key][1][1]
		return in_picture and x_okay and y_okay
	
	# initialize
	correct_colors= {}
	hsv_color_ranges = {}
	for key, coord_range in searched_range.items():
		correct_colors[key] = []
		hsv_color_ranges[key] = None

	for idx in numpy.argsort(accums)[::-1][:]: # nach quali sortieren (beste x)
		center_y, center_x = centers[idx]
		
		# get all circle centers to the correct array
		for key, coord_range in searched_range.items():
			if in_range(centers[idx], key):
				# get rgb color of center
				rgb_color = rgb_img[center_y, center_x]
				hsv_color = rgb2hsv(rgb_color)
				correct_colors[key].append(hsv_color)

	for key, color_array in correct_colors.items():
		if len(color_array) == 0: 
			print('at least one color not detected')
			return None

	for key, color_array in correct_colors.items():

		h_min = None
		s_min = None
		v_min = None
		h_max = None
		s_max = None
		v_max = None

		for i in range(len(color_array)):
			hsv = color_array[i]

			h_min = hsv[0] if h_min is None or h_min > hsv[0] else h_min
			s_min = hsv[1] if s_min is None or s_min > hsv[1] else s_min
			v_min = hsv[2] if v_min is None or v_min > hsv[2] else v_min

			h_max = hsv[0] if h_max is None or h_max < hsv[0] else h_max
			s_max = hsv[1] if s_max is None or s_max < hsv[1] else s_max
			v_max = hsv[2] if v_max is None or v_max < hsv[2] else v_max

		print(h_min, s_min, v_min, h_max, s_max, v_max)
		#correct_colors[key] = ((h_min-0.1, s_min-0.1, v_min-20),(h_max+0.1, s_max+0.1, v_max+20))
		correct_colors[key] = ((h_min, s_min, v_min),(h_max, s_max, v_max))

	return correct_colors

#########################################################################################################
#########################################################################################################

def warp(img, edges):

    width = len(img[1])
    height = len(img)

    warped = numpy.empty((width, height, 3), dtype=numpy.uint8)

    for x in range(width):
        x_share = x / width
        x_share_comp = 1 - x_share

        y_start = edges['upper_left'][1] * x_share_comp + edges['upper_right'][1] * x_share
        y_end = edges['lower_left'][1] * x_share_comp + edges['lower_right'][1] * x_share

        for y in range(height):
            y_share = y / height
            y_share_comp = 1 - y_share

            x_start = edges['upper_left'][0] * y_share_comp + edges['lower_left'][0] * y_share
            x_end = edges['upper_right'][0] * y_share_comp + edges['lower_right'][0] * y_share

            x_len = x_end - x_start
            y_len = y_end - y_start

            x_new = x_start + x_share * x_len
            y_new = y_start + y_share * y_len
                   
            warped[int(x_new), int(y_new)] = (img[y,x][0], img[y,x][1], img[y,x][2])
    
    return warped

#########################################################################################################
#########################################################################################################


if __name__ == '__main__':
	print('\n')
	print('NOTE: THIS IS JUST FOR TESTING PURPOSES')
	print('Import the main function via \'from cv import detect_colored_circles\'')
	path = 'img/0_photo.jpg'

	radius_range = (20,25) # radius of circles in pixels
	hsv_color_ranges = {
		'lower_right': ((0.52,0.4,100.),(0.78,1.,255.)),		# upper left circle
		'upper_left': ((0.24,0.4,100.),(0.47,1.,255.)),	# lower left circle
		'upper_right': ((0.86,0.4,100.),(0.10,1.,255.)),		# lower right circle
		'lower_left': ((0.0,0.,0.),(1.,1.,60.))		# upper right circle
	}

	rgb_img = imread(path)
	overlay = scipy.misc.imread('0.jpg')
	print('points detection from file',path,'with circle radii from',radius_range[0],'to',radius_range[1],'\n') 	

	c = 0
	while c < 10:
		c +=1
		start = time.time()
		circle_coords = detect_colored_circles_no_prints(rgb_img, radius_range, hsv_color_ranges, debug=False)
		if circle_coords is not None:
			warped = warp(overlay, circle_coords)
			print('duration: ',time.time()-start,'seconds')
			scipy.misc.imsave('test.png', warped)
		else:
			print('error')

