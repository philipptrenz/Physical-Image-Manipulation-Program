import os, shutil, pygame, numpy, time, threading, scipy.misc
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


def camstream():
    """
    This method is basically the main method. It contains the loop for camera images and
    starts an image processing thread, so it works independently and camera stream is not
    affected by image processing time.
    """
    global capture 
    global screen
    global overlay
    global warped_surface
    global screen_is_locked_manually
    global DEVICE

    overlay = scipy.misc.imread('overlay3.jpg', mode='RGBA')
    overlay = cv.scale_to_fit(overlay, SIZE)

    pygame.init()
    pygame.camera.init()

    available_cams = pygame.camera.list_cameras()
    
    DEVICE = ''
    def choose_cam():
        global DEVICE
        """
        User input method to choose a camera in case multiple cameras were found.
        """

        print('Please choose your camera, press')
        for i in range(len(available_cams)):
            print('\''+str(i)+'\' for camera on\''+available_cams[i]+'\'')

        display = pygame.display.set_mode(SIZE, 0)
        while True:
            for event in pygame.event.get():
                # it's the way pygame handles inputs ... sorry :'(
                if event.type == KEYDOWN and event.key == K_0:
                    DEVICE = available_cams[0]
                    return
                elif event.type == KEYDOWN and event.key == K_1:
                    DEVICE = available_cams[1]
                    return
                elif event.type == KEYDOWN and event.key == K_2:
                    DEVICE = available_cams[2]
                    return
                elif event.type == KEYDOWN and event.key == K_3:
                    DEVICE = available_cams[3]
                    return
                elif event.type == KEYDOWN and event.key == K_4:
                    DEVICE = available_cams[4]
                    return
                elif event.type == KEYDOWN and event.key == K_5:
                    DEVICE = available_cams[5]
                    return
                elif event.type == KEYDOWN and event.key == K_6:
                    DEVICE = available_cams[6]
                    return
                elif event.type == KEYDOWN and event.key == K_7:
                    DEVICE = available_cams[7]
                    return
                elif event.type == KEYDOWN and event.key == K_8:
                    DEVICE = available_cams[8]
                    return
                elif event.type == KEYDOWN and event.key == K_9:
                    DEVICE = available_cams[9]
                    return
                else:
                    print('Please type a number between 0 and '+str(len(available_cams)-1))

    if len(available_cams) == 0:
        print('We do need a camera, though.\nWe quit while you search. Bye!')
        pygame.quit()
        return
    elif len(available_cams) == 1:
        DEVICE = available_cams[0]
    else:
        choose_cam()
    

    camera = pygame.camera.Camera(DEVICE, SIZE)

    camera.start()
    display = pygame.display.set_mode(SIZE, 0)
    screen = pygame.surface.Surface(SIZE, 0, display)
    warped_surface = pygame.surface.Surface(SIZE, pygame.SRCALPHA)
    
    def wait_for_user():
        """
        Either calibrate or load calibration data from hsv_color_ranges.txt
        """
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
    
    # start image processing thread
    threading.Thread(target=ui).start()

    while capture:
        # camera stream loop, updates the screen

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
    """
    User selects tiles on the screen by clicking into the mid of each tile, repeatedly.
    From the received user inputs a color range as HSV color gets calculated for later 
    comparison of colors.
    The tiles should be moved with each iteration to optimize the color ranges.
    """
    global hsv_color_ranges

    temp = pygame.transform.rotate(screen, 90)
    img = numpy.copy(pygame.surfarray.pixels3d(temp))

    cv.save_image('calibrate_raw_'+str(counter), img)

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
    """
    warp the image according to the current tile locations. The whole image processing is done here.
    """
    global warped_surface
    counter = 0
    while capture:
        if not screen_is_locked_manually:
            
            start = time.time()
            temp = pygame.transform.rotate(screen.copy(), 90)
            img = numpy.copy(pygame.surfarray.pixels3d(temp))

            circle_coords = cv.detect_colored_circles(img, radius_range, hsv_color_ranges, counter=counter, debug=False)
            if circle_coords is not None:
                warped_array = cv.warp(overlay, circle_coords)

                path = 'doc/3_warped_array_'+str(counter)+'.png'

                scipy.misc.imsave(path, warped_array)
                warped_surface = pygame.transform.flip(pygame.image.load(path), True, False)

                warped_surface.set_alpha(150)
            else:
                print('put the tiles back, man!')

            counter += 1



def load_hsv_color_ranges():
    """
    Read color ranges from hsv_color_ranges.txt
    """
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
    """
    Save color ranges to hsv_color_ranges.txt
    """
    global hsv_color_ranges
    target = open('hsv_color_ranges.txt', 'w')
    target.write(str(hsv_color_ranges))


def wait_for_mouseclick():
    """
    Wait for the mouse click.
    Returns: Position of mouse as touple
    """
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONUP:
                pos = pygame.mouse.get_pos()
                return pos

if __name__ == '__main__':
    """
    Main method
    """
    dir = 'doc'
    if os.path.exists(dir):
        shutil.rmtree(dir)
    os.makedirs(dir)
    camstream()
