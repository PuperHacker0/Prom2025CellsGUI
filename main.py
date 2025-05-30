#TODO: Maybe debug messages should be printed to data logger output aside from just stdout debug()
#TODO: when calling get_message from serial, also call datalog to log it
#TODO: Ισως δεν δινονται ολα τα temperatures!!! αλλα ενδεχομενως μονο ενα ποσοστο

import kivy
from SerialReader import *
from Datalogger import *
from screeninfo import get_monitors
from kivy.uix.recycleview import RecycleView
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.properties import ListProperty
from kivy.uix.gridlayout import GridLayout
from kivy.config import Config
from kivy.uix.boxlayout import BoxLayout
import threaded, threading

DEBUG_MODE = True
WINDOW_SIZE = (None, None)

import os
if not DEBUG_MODE: #Disable kivy output log if not in debug mode
    os.environ["KIVY_NO_CONSOLELOG"] = '1'

#Set app layout through the .kv file, otherwise use a string with .load_string()
Builder.load_file("layout.kv")

def interpret_data(raw_data):
    d = raw_data.replace('\n', '').replace(' ', '') #remove all spaces and newlines (not needed anywhere)
    
    if d[0] != '{':
        print('[DEBUG] Message not starting with { found, assumed first message and skipped')
        return #TODO maybe turn this into an exception
    else:
        try:
            s = d.split(':')
            (message_type, message_content) = (s[0], s[1:])
            message_type = message_type[1:] #Remove the {
            print("Message type:", message_type)
            print("Message content:", message_content, '\n')
            #Dont take content like this, interpret it like a dict with json.loads()
            #TODO
        except Exception as e:
            print('[CRITICAL] Failed to interpret message')

class Segment(GridLayout):
    def set_texts(self, texts):
        self.clear_widgets() #Needed?

        try:
            for text in texts:
                #self.add_widget(Label(text = text, size_hint = (None, None), width = WINDOW_SIZE[0] // 8, height = WINDOW_SIZE[1] // 18))
                self.add_widget(Label(text = text, size_hint = (None, None), width = 205, height = 55))
                #TODO These are not set correctly, owing to window sizing imprecision. Why is that?
        except TypeError as e:
            print(f'[CRITICAL] (probably) Window size set incorrectly. Labels not created. ({e})')
        except Exception as e:
            print(f'[CRITICAL] Failed to create/update one or more segment labels ({e})')

class SegmentGrid(BoxLayout):
    def __init__(self, **kwargs):
        super(SegmentGrid, self).__init__(**kwargs)
        self.segments = []

        # Create 8 segments to begin with
        for i in range(8):
            segment = Segment()
            segment.set_texts([f"Cell pair {i * 18 + j}" for j in range(1, 19)])

            #ids is the dict which maps to the id segment_container which contains the segment layout
            self.ids.segment_container.add_widget(segment)
            self.segments.append(segment) #theoretically not needed UNLESS WE'RE UPDATING???

    def update_labels(self, serial_reader): #Call this from main or keep it running as a thread! when data has been interpreted
        running = True #TODO connect close window event to self.running = false

        while running:
            raw = serial_reader.get_message()

            if raw != None:
                data = interpret_data(raw)
                #TODO then update all cells accordingly (flag e.g. voltage, then array[])
                

class MyApp(App):
    def build(self):
        #Initialize and start the serial reader of the port and the data logger
        self.serial_reader = SerialReader(debug_mode = DEBUG_MODE) #todo: bug: no attribute specified port???
        self.data_logger = Datalogger("log.txt", debug_mode = DEBUG_MODE)

        self.serial_reader.start()
        self.data_logger.start()

        self.setWindowSize()
        self.title = "Prom Racing Navios 2025 TSAC 'στο τσακ' Viewer"
        self.icon = 'icon.ico' #When running app as a script, the taskbar icon will be the default python logo
        #But when running as an exectutable, it will automatically sync to the window icon

        self.segment_grid = SegmentGrid() #widget!

        self.data_update_thread = threading.Thread(target = self.segment_grid.update_labels(self.serial_reader))
        self.data_update_thread.start()

        return self.segment_grid
        '''
        layout = GridLayout(cols = 4, rows = 2) #4x2 segment array

        cellCounter = 1
        for i in range(1, 9): #For each of the segments (1 to 8)
            #print('Seg' + str(i))
            seg = GridLayout(cols = 2, rows = 9) #18 cells up (and their respective cells below) in "arrangement"
            #Pointless to arrange them like they are actually so we represent them like this

            #emptySeg = Label(text = '-') Careful! We can't do this because each box has an indiviual ID and
            #can't be linked multiple times, this is like a pointer
            #But we can create a function which creates new Labels each time tho as a shortcut

            if i == 4: #Top right segment has gaps on the top
                seg.add_widget(Label(text = '----'))
                seg.add_widget(Label(text = '----'))

            for k in range(18 - (i % 4 == 0) * 2): #18 cells, or 16 + the gaps on top/bottom if on the right border
                seg.add_widget(Label(text = 'Cell pair ' + str(cellCounter)))
                cellCounter = cellCounter + 1

            if i == 8: #Bottom right segment has gaps on the bottom
                seg.add_widget(Label(text = '---'))
                seg.add_widget(Label(text = '---'))
            
            layout.add_widget(seg)

        return layout
        ''' #Standard layout approach without .kv file (brute force)

    def __del__(self): #Kills the threads when closing the app (so that writing to files and other tasks finish)
        #TODO this does not work correctly! Maybe it deletes the class contents in another way?
        self.serial_reader.stop()
        self.data_logger.stop()
        #and close data_update thread

    def setWindowSize(self, w = 0, h = 0):
        if w > 0 and h > 0: #If width and height have both been specified manually
            Config.set('graphics', 'width', str(w))
            Config.set('graphics', 'height', str(h))

            if DEBUG_MODE:
                print('[DEBUG] Set screen size to manually specified ')
        else:
            #Set the window size based on the primary screen size (leave some space)
            fullscreen = False

            W = int(get_monitors()[0].width)
            H = int(get_monitors()[0].height)

            if DEBUG_MODE:
                print("[DEBUG] Found screen size: " + str(W) + 'x' + str(H) + '. Opening in ', end = '')

                if fullscreen:
                    print('fullscreen mode')
                else:
                    print("windowed mode")

            if not fullscreen: #Else W, H already set to the size of the screen
                coeff = 0.7
                W = int(W * coeff)
                H = int(H * coeff)

            Config.set('graphics', 'width', str(W))
            Config.set('graphics', 'height', str(H))

            self.window_size = (W, H)
            global WINDOW_SIZE
            WINDOW_SIZE = self.window_size
    
if __name__ == '__main__':
    #serial_reader, data_logger, and other threads are now defined inside the MyApp() class
    MyApp().run()