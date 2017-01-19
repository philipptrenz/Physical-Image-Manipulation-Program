import pygame, numpy, time, threading, scipy.misc
import pygame.transform
import pygame.camera
from pygame.locals import *
import cv


DEVICE = '/dev/video1'
SIZE = (640, 480)
radius_range = (22,30)

capture = True
screen = None

hsv_color_ranges = None
overlay = None
warped_surface = None

screen_is_locked_manually = False

#warped_array = None

def camstream():
    global capture 
    global screen
    global overlay
    global warped_surface
    global screen_is_locked_manually

    overlay = scipy.misc.imread('0.jpg', mode='RGBA')


    pygame.init()
    pygame.camera.init()

    print(pygame.camera.list_cameras())

    display = pygame.display.set_mode(SIZE, 0)
    camera = pygame.camera.Camera(DEVICE, SIZE)
    camera.start()
    screen = pygame.surface.Surface(SIZE, 0, display)
    warped_surface = pygame.surface.Surface(SIZE, pygame.SRCALPHA)
    

    def wait_for_user():
        global screen
        while capture:
            # paint once for calibrating
            screen = camera.get_image(screen) # screen is pygame surface object
            display.blit(screen, (0,0))
            screen = pygame.transform.flip(screen, True, False)

            pygame.image.save(screen, 'image.jpg')
            pygame.display.flip() # actually update ...
            for event in pygame.event.get():
                if event.type == KEYDOWN or event.type == MOUSEBUTTONUP:
                    return

    wait_for_user()
    
    calibrate(screen)

    threading.Thread(target=ui).start()

    while capture:
        screen_is_locked_manually = True
        screen = camera.get_image(screen) # screen is pygame surface object
        display.blit(screen, (0,0))
        if not warped_surface.get_locked(): 
            display.blit(warped_surface, (0,0))
        screen = pygame.transform.flip(screen, True, False)
        screen_is_locked_manually = False
        pygame.display.flip() # actually update ...

        for event in pygame.event.get():
            if event.type == QUIT:
                capture = False

    camera.stop()
    pygame.quit()
    return



debug_ranges = None
def calibrate(screen):
    global hsv_color_ranges

    temp = pygame.transform.rotate(screen, 90)
    img = numpy.copy(pygame.surfarray.pixels3d(temp))

    scipy.misc.imsave('test/to_calibrate.png', img)

    searched_range = {'upper_left': None, 'lower_left': None, 'lower_right': None, 'upper_right': None}
    tolerance = radius_range[0]
    for key, touple in searched_range.items():
        print('Click in the middle of the ',key,' circle ...')
        pos = wait_for_mouseclick()
        searched_range[key] = ((pos[0]-tolerance, pos[1]-tolerance), (pos[0]+tolerance, pos[1]+tolerance))

    global debug_ranges
    debug_ranges = searched_range
    hsv_color_ranges = cv.calibrate_colors(img, radius_range, searched_range)

    if hsv_color_ranges is None:
        print('please try again ...')
        calibrate(screen)

def ui():
    global warped_surface
    x = 0
    while capture:
        if not screen_is_locked_manually:
            x += 1
            start = time.time()
            temp = pygame.transform.rotate(screen.copy(), 90)
            img = numpy.copy(pygame.surfarray.pixels3d(temp))

            circle_coords = cv.detect_colored_circles(img, radius_range, hsv_color_ranges, debug_ranges, debug=False)
            if circle_coords is not None:
                warped_array = cv.warp(overlay, circle_coords)

                scipy.misc.imsave('test/warped_array.png', warped_array)
                warped_surface = pygame.image.load('test/warped_array.png')
            else:
                print('put the tiles back, man!')

def wait_for_mouseclick():
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONUP:
                return pygame.mouse.get_pos()

"""
def warp(img, edges):

    my_time = 0

    width = len(img[1])
    height = len(img)

    warped = pygame.Surface(SIZE, pygame.SRCALPHA)
    warped.set_alpha(0)
    pxarray = pygame.PixelArray(warped)

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
            
            start = time.time()         
            pxarray[int(x_new), int(y_new)] = (img[y,x][0], img[y,x][1], img[y,x][2], 255)
            my_time += time.time()-start
    
    print('Warp time finished, duration: ',my_time,'seconds \t\t <----')
    return warped
"""

if __name__ == '__main__':
    camstream()
