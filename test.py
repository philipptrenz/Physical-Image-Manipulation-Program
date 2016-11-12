#!/usr/bin/env python3

import sys
import io
import os
import picamera

import time
from time import sleep

import numpy
import picamera.array
from PIL import Image

from PyQt5.QtWidgets import QApplication
from pyqt import FreakingQtImageViewer

from skimage.transform import hough_ellipse
from skimage.filters import roberts, sobel, scharr, prewitt


def capture():
	with picamera.array.PiRGBArray(camera) as stream:
		camera.capture(stream, format='rgb')
		img = stream.array
		print(img)
		im = Image.fromarray(img).convert('LA')
		im.save('./tmp.png')

		result = hough_ellipse(im, min_size=15, max_size=90)
		print('detected')
		result.tolist()
		print(result)



if __name__ == '__main__':
        camera = picamera.PiCamera()

        app = QApplication(sys.argv)
        viewer = FreakingQtImageViewer(capture)
        sys.exit(app.exec_())

