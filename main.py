#TODO: Maybe debug messages should be printed to data logger output aside from just stdout debug()
#TODO: when calling get_message from serial, also call datalog to log it

import kivy
from SerialReader import *
from Datalogger import *
from screeninfo import get_monitors
from kivy.uix.recycleview import RecycleView
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.config import Config
from kivy.uix.boxlayout import BoxLayout
import threading
import DataContainer

DEBUG_MODE = True
WINDOW_SIZE = (None, None)

import os
if not DEBUG_MODE: #Disable kivy output log if not in debug mode
    os.environ["KIVY_NO_CONSOLELOG"] = '1'

#Set app layout through the .kv file, otherwise use a string with .load_string()
Builder.load_file("layout.kv")

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
                
class MyApp(App):
    def build(self):
        self.running = True

        #Initialize and start the serial reader of the port and the data logger
        self.serial_reader = SerialReader(debug_mode = DEBUG_MODE) #TODO: bug: no attribute specified port???
        self.data_logger = Datalogger("log.txt", debug_mode = DEBUG_MODE)

        self.serial_reader.start()
        self.data_logger.start()

        self.setWindowSize()
        self.title = "Prom Racing Navios 2025 TSAC 'στο τσακ' Viewer"
        self.icon = 'icon.ico' #When running app as a script, the taskbar icon will be the default python logo
        #But when running as an exectutable, it will automatically sync to the window icon

        self.segment_grid = SegmentGrid() #widget!

        self.data_container = DataContainer(DEBUG_MODE)
        self.data_update_thread = threading.Thread(target = self.update_data)
        self.data_update_thread.start()

        return self.segment_grid

    #TODO connect close window event to self.running = false

    def __del__(self): #Kills the threads when closing the app (so that writing to files and other tasks finish)
        #TODO this does not work correctly! Maybe it deletes the class contents in another way?
        self.serial_reader.stop()
        self.data_logger.stop()
        self.running = False
        self.data_update_thread.join()
        #and close data_update thread

    def update_data(self): #TODO
        while self.running:
            #1) Ask reader if there is data available
            raw = self.serial_reader.get_message() #no-stall

            #2) Interpret the data in the DataContainer class
            if raw != None:
                self.data_container.interpret_data(raw)
                
                #3) Update the graphical interface accordingly by asking the DataContainer for info
                    #TODO then update all cells accordingly (flag e.g. voltage, then array[])

    def setWindowSize(self, w = 0, h = 0):
        if w > 0 and h > 0: #If width and height have both been specified manually
            Config.set('graphics', 'width', str(w))
            Config.set('graphics', 'height', str(h))

            if DEBUG_MODE:
                print('[DEBUG] Set screen size to manually specified')
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