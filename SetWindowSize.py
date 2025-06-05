from screeninfo import get_monitors
from kivy.config import Config

def get_window_size(FORCE_WINDOW_SIZE, DEBUG_MODE, FORCE_FULLSCREEN):
    W, H = 0, 0

    try:
        if FORCE_WINDOW_SIZE is not None: #manually specified monitor size
            W, H = int(FORCE_WINDOW_SIZE[0]), int(FORCE_WINDOW_SIZE[1])
            
            if DEBUG_MODE:
                print(f'[DEBUG] Set screen size to manually specified ({W}x{H})')
        else:
            #if not fixed, find monitor dimensions
            W = int(get_monitors()[0].width)
            H = int(get_monitors()[0].height)
            
            coeff = 0.7
            if FORCE_FULLSCREEN:
                coeff = 1.0

            if DEBUG_MODE:
                print("[DEBUG] Found screen size: " + str(W) + 'x' + str(H) + '. Opening in ', end = '')

                if FORCE_FULLSCREEN:
                    print('fullscreen mode')
                else:
                    print("windowed mode")

            W, H = int(W * coeff), int(H * coeff)
        
    except Exception as e:
        print(f'[CRITICAL] Setting window size failed. ({e})')
    
    return (W, H)

def set_window_size(FORCE_WINDOW_SIZE, DEBUG_MODE, FORCE_FULLSCREEN):
    #Set window size BEFORE importing other Kivy modules
    (w, h) = get_window_size(FORCE_WINDOW_SIZE, DEBUG_MODE, FORCE_FULLSCREEN)
    
    Config.set('graphics', 'width', str(w))
    Config.set('graphics', 'height', str(h))
    Config.set('graphics', 'resizable', '0') #make window non-resizable

    return (w, h)