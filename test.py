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


def capture():
	with picamera.array.PiRGBArray(camera) as stream:
		camera.capture(stream, format='wb')
		img = stream.array
		print(img)
		im = Image.fromarray(img)
		im.save('./tmp.jpg')

if __name__ == '__main__':
        camera = picamera.PiCamera()

        app = QApplication(sys.argv)
        viewer = FreakingQtImageViewer(capture)
        sys.exit(app.exec_())

