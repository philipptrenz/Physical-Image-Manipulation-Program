
import math
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

from skimage import data
from skimage import transform as tf

margins = dict(hspace=0.01, wspace=0.01, top=1, bottom=0, left=0, right=1)

text = data.text()

src = np.array((
	(0, 0), #upper left
	(0, 1024), #lower left
	(1280, 1024), #lright
	(1280, 0) #uright
))
dst = np.array((
    (155, 15),
    (65, 40),
    (260, 130),
    (360, 95)
))

tform3 = tf.ProjectiveTransform()
tform3.estimate(src, dst)
warped = tf.warp(text, tform3, output_shape=(50, 300))

fig, (ax1, ax2) = plt.subplots(nrows=2, figsize=(8, 3))
fig.subplots_adjust(**margins)
plt.gray()
ax1.imshow(text)
ax1.plot(dst[:, 0], dst[:, 1], '.r')
ax1.axis('off')
ax2.imshow(warped)
ax2.axis('off')

plt.show()

# -------------------------------------------------






class Transform():

	def __init__(self, output_width, output_height):
		self.output_width = output_width
		self.output_height = output_height


	def transformPlaygroudImage(self, image, topleft, bottomleft, bottomright, topright):
		"""
		Inputs: Image to transform, coordinates of corners as tuples.
		E.g. topleft = (200,20) and bottomleft = (180, 400)
		"""
		image_in = np.array((
			topleft,
			bottomleft,
			bottomright,
			topright
		))
		image_out = np.array((
			(0, 0),
			(0, self.output_height),
			(self.output_width, self.output_height),
			(self.output_width, 0)
		))

		transformer = tf.ProjectiveTransform()
		transformer.estimate(image_out, image_in)

		transformed_image = tf.warp(image, transformer, output_shape=(self.output_width, self.output_height))

		return transformed_image.astype(int)

if __name__ == '__main__':
	

	t = Transform(1024, 1024)

	im = Image.open('./outfile.jpg')

	im_transformed = t.transformPlaygroudImage(im, (423,270), (400,830), (1040,560), (1010,24))

	im_new = Image.fromarray(im_transformed)
	im.save('./transformed.png')



