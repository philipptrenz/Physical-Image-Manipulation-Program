import pygame, numpy, time, threading, scipy.misc
import pygame.transform
import pygame.camera
from pygame.locals import *
import cv


DEVICE = '/dev/video1'
SIZE = (640, 480)
radius_range = (15,30)

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
        counter = 0
        total = 4
        print('you have to accomplish',total,'calibration rounds\npress any key to start\n')
        while capture:
            # paint once for calibrating
            screen = camera.get_image(screen) # screen is pygame surface object
            display.blit(screen, (0,0))
            screen = pygame.transform.flip(screen, True, False)

            pygame.image.save(screen, 'image.jpg')
            pygame.display.flip() # actually update ...

            for event in pygame.event.get():
                if event.type == KEYDOWN or event.type == MOUSEBUTTONUP:
                    if counter < total:
                        calibrate(screen)
                        print(counter, 'accomplished, move the tiles and click any key to get to the next round!')
                        counter += 1
                    else:
                        return


    wait_for_user()
    
    #calibrate(screen)

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

    new_hsv_color_ranges = cv.calibrate_colors(img, radius_range, searched_range)
    if new_hsv_color_ranges is not None:
        if hsv_color_ranges is None:
            hsv_color_ranges = new_hsv_color_ranges
        else:
            for key, old in hsv_color_ranges.items():
                new = new_hsv_color_ranges[key]
                
                h_min = new[0][0] if new[0][0] < old[0][0] else old[0][0]
                s_min = new[0][1] if new[0][1] < old[0][1] else old[0][1] 
                v_min = new[0][2] if new[0][2] < old[0][2] else old[0][2]
                
                h_max = new[1][0] if new[1][0] > old[1][0] else old[1][0]
                s_max = new[1][1] if new[1][1] > old[1][1] else old[1][1] 
                v_max = new[1][2] if new[1][2] > old[1][2] else old[1][2]

                hsv_color_ranges[key] = ((h_min,s_min,v_min),(h_max,s_max,v_max))

    if hsv_color_ranges is None:
        print('please try again ...')
        calibrate(screen)
    return

def ui():
    global warped_surface
    x = 0
    while capture:
        if not screen_is_locked_manually:
            x += 1
            start = time.time()
            temp = pygame.transform.rotate(screen.copy(), 90)
            img = numpy.copy(pygame.surfarray.pixels3d(temp))

            circle_coords = cv.detect_colored_circles(img, radius_range, hsv_color_ranges, debug=False)
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
