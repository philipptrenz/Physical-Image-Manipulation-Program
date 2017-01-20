import pygame, numpy, time, threading, scipy.misc
import pygame.transform
import pygame.camera
from pygame.locals import *
import cv


DEVICE = '/dev/video0'
SIZE = (640, 480)
radius_range = (12,25)

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

    overlay = scipy.misc.imread('test/overlay.jpg', mode='RGBA')


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
        total = 3
        print('Do you want to load hsv calibration colors from file?\n Press y for yes and n for no')
        while capture:
            # paint once for calibrating
            screen = camera.get_image(screen) # screen is pygame surface object
            screen = pygame.transform.flip(screen, True, True)
            display.blit(screen, (0,0))
            pygame.display.flip() # actually update ...
            screen = pygame.transform.flip(screen, True, False)

            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    if event.key == K_y:
                        if load_hsv_color_ranges():
                            print('HSV color ranges got loaded')
                            return
                        else:
                            print('Could not read, calibration necessary')

                    if counter < total:
                        calibrate(screen, counter)
                        counter += 1
                        if counter < total:
                            print(counter, 'accomplished, move the tiles and click any key to get to the next round!')                        
                        else:
                            save_hsv_color_ranges()
                            return
                    else:
                        return


    wait_for_user()
    
    #calibrate(screen)

    threading.Thread(target=ui).start()

    while capture:
        screen_is_locked_manually = True
        screen = camera.get_image(screen) # screen is pygame surface object
        screen = pygame.transform.flip(screen, True, True)
        display.blit(screen, (0,0))
        if not warped_surface.get_locked(): 
            display.blit(warped_surface, (0,0))
        screen_is_locked_manually = False
        pygame.display.flip() # actually update ...
        screen = pygame.transform.flip(screen, True, False)

        for event in pygame.event.get():
            if event.type == QUIT:
                capture = False

    camera.stop()
    pygame.quit()
    return

def calibrate(screen, counter):
    global hsv_color_ranges

    temp = pygame.transform.rotate(screen, 90)
    img = numpy.copy(pygame.surfarray.pixels3d(temp))

    scipy.misc.imsave('test/calibrate_raw_'+str(counter)+'.png', img)

    searched_range = {'upper_left': None, 'lower_left': None, 'lower_right': None, 'upper_right': None}
    tolerance = radius_range[0]
    for key, touple in searched_range.items():
        print('Click in the middle of the ',key,' circle ...')
        pos = wait_for_mouseclick()
        searched_range[key] = ((pos[0]-tolerance, pos[1]-tolerance), (pos[0]+tolerance, pos[1]+tolerance))

    new_hsv_color_ranges = cv.calibrate_colors(img, radius_range, searched_range, counter)
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
        calibrate(screen, counter)
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
                warped_surface = pygame.transform.flip(pygame.image.load('test/warped_array.png'), True, False)
                warped_surface.set_alpha(150)
            else:
                print('put the tiles back, man!')



def load_hsv_color_ranges():
    try:
        hsv_color_ranges_new = eval(open('hsv_color_ranges.txt', 'r').read())
        if hsv_color_ranges_new is not None:
            global hsv_color_ranges
            hsv_color_ranges = hsv_color_ranges_new
            return True
        else:
            return False
    except FileNotFoundError:
        return False


def save_hsv_color_ranges():
    global hsv_color_ranges
    target = open('hsv_color_ranges.txt', 'a')
    target.write(str(hsv_color_ranges))


def wait_for_mouseclick():
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONUP:
                pos = pygame.mouse.get_pos()
                return pos

if __name__ == '__main__':
    camstream()
