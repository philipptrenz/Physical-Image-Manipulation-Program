import pygame, numpy, time, threading
import pygame.transform
import pygame.camera
from pygame.locals import *
from cv import detect_colored_circles, detect_colored_circles_no_prints, calibrate_colors
import scipy.misc


DEVICE = '/dev/video0'
SIZE = (640, 480)
radius_range = (20,25)

capture = True
screen = None

hsv_color_ranges = None
image_surface = None

overlay = None

flipFlag = False

#warped_array = None

def camstream():
    global capture 
    global screen
    global overlay
    global image_surface
    global flipFlag
    #global warped_array

    #warped_array = numpy.empty((SIZE[0], SIZE[1], 3), dtype=numpy.uint8)

    overlay = scipy.misc.imread('0.jpg')

    image_surface = pygame.Surface(SIZE, pygame.SRCALPHA)
    image_surface.set_alpha(0)

    pygame.init()
    pygame.camera.init()
    display = pygame.display.set_mode(SIZE, 0)
    camera = pygame.camera.Camera(DEVICE, SIZE)
    camera.start()
    screen = pygame.surface.Surface(SIZE, 0, display)
    
    # paint once for calibrating
    screen = camera.get_image(screen) # screen is pygame surface object
    display.blit(screen, (0,0))
    screen = pygame.transform.flip(screen, True, False)
    pygame.display.flip() # actually update ...

    # paint another time for calibrating
    screen = camera.get_image(screen) # screen is pygame surface object
    display.blit(screen, (0,0))
    screen = pygame.transform.flip(screen, True, False)
    pygame.display.flip() # actually update ...
    
    calibrate(screen)

    threading.Thread(target=ui).start()

    while capture:
        screen = camera.get_image(screen) # screen is pygame surface object
        flipFlag = False
        display.blit(screen, (0,0))
        display.blit(image_surface, (0,0))
        #pygame.surfarray.blit_array(display, warped_array)
        screen = pygame.transform.flip(screen, True, False)
        flipFlag = True
        pygame.display.flip() # actually update ...

        for event in pygame.event.get():
            if event.type == QUIT:
                capture = False

    camera.stop()
    pygame.quit()
    return


def calibrate(screen):
    global hsv_color_ranges

    temp = pygame.transform.rotate(screen, 90)
    img = numpy.copy(pygame.surfarray.pixels3d(temp))

    searched_range = {'upper_left': None, 'lower_left': None, 'lower_right': None, 'upper_right': None}
    tolerance = radius_range[0]
    for key, touple in searched_range.items():
        print('Click in the middle of the ',key,' circle ...')
        pos = wait_for_mouseclick()
        searched_range[key] = ((pos[0]-tolerance, pos[1]-tolerance), (pos[0]+tolerance, pos[1]+tolerance))

    hsv_color_ranges = calibrate_colors(img, radius_range, searched_range)

    print(hsv_color_ranges)

    if hsv_color_ranges is None:
        print('please try again ...')
        calibrate()

def ui():
    global flipFlag
    global image_surface
    while capture:
        while flipFlag is False:
            time.sleep(0.001)
        temp = pygame.transform.rotate(screen.copy(), 90)
        img = numpy.copy(pygame.surfarray.pixels3d(temp))

        circle_coords = detect_colored_circles_no_prints(img, radius_range, hsv_color_ranges, debug=False)

        if circle_coords is not None:
            image_surface = warp(overlay, circle_coords)
            #global warped_array
            #warped_array = warp(overlay, circle_coords)
            flipFlag = False
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

"""def warp(img, edges):

    width = len(img[1])
    height = len(img)

    array = numpy.empty((width, height, 3), dtype=numpy.uint8)

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
                   
            array[int(x_new), int(y_new)] = (img[y,x][0], img[y,x][1], img[y,x][2])
    
    #return warped
    return array"""

if __name__ == '__main__':
    camstream()
