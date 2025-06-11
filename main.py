#ATTENTION!!!!!!!!!!!!!!!!!!!!!!!!COM PORT FIXED TO 1 for virtual testing

#Important: changing the order of (0), (1), (2), (3) results in undefined behavior

#TODO take all graphics related classes to a new class
#TODO improve handling of unused cells, conditions are scattered all around (e.g. change in position!!!)
#TODO maybe the order of traversal of the cells should also be a function too in case the layout is different or the sensors are positioned differently

#Define fundamental variables of the app (0)
FORCE_WINDOW_SIZE = None #Overrides forced fullscreen 
FORCE_FULLSCREEN = False
DEBUG_MODE = True
CELL_VOLTAGE_DECIMALS = 1

#First, set environment variables, these will lock first (1)
import os
if not DEBUG_MODE: #Disable kivy output log if not in debug mode
    os.environ["KIVY_NO_CONSOLELOG"] = '1'

#Then, set kivy window size, this will lock next (2)
import SetWindowSize #First set window size and other parameters because once kivy loads these lock
WINDOW_SIZE = SetWindowSize.set_window_size(FORCE_WINDOW_SIZE, DEBUG_MODE, FORCE_FULLSCREEN)

#Then, import everything kivy-related (3)
import kivy
from SerialReader import *
from Datalogger import *
from kivy.uix.recycleview import RecycleView
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
import threading
from DataContainer import *
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import ListProperty, NumericProperty
from kivy.graphics import Color, Rectangle, Line

#Set app layout through the .kv file, otherwise use a string with .load_string()
Builder.load_file("layout.kv")

class OutlinedLabel(Label):
    #Default settings
    border_color = ListProperty([1, 1, 1, 1])
    border_width = NumericProperty(1.5)
    background_color = ListProperty([0.2, 0.2, 0.2, 1])

    #We don't need a function to directly modify these values, since we're just making new labels

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos = self.update_canvas, size = self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.background_color)
            Rectangle(pos = self.pos, size = self.size)
            Color(*self.border_color)
            Line(rectangle = (self.x, self.y, self.width, self.height), width = self.border_width)

class Segment(GridLayout):
    def add_placeholders(self):
        self.configure_cells([f"Cell pair {j}" for j in range(1, 19)])

    def configure_cells(self, texts, warnings = None, segment_number = -1): #Update label text and label color if warnings arise
        self.clear_widgets() #Erase previous labels and update
        #Don't re-create and re-link 142 widgets, just create new segments and add them to the already existing structure for efficiency

        try:
            font_size = 30 #Large numbers
            border_color = (1, 1, 1, 0.7) #Faded white outline
            border_width = 1.5
            size_hint = (1, 1) # Fill cell out
            text_color = (1, 1, 1, 1) #White text
            
            for i in range(18):
                background_color = (0, 0.2, 0, 1)

                if (segment_number == 3 and (i == 0 or i == 1)) or (segment_number == 7 and (i == 16 or i == 17)):
                    background_color = (0, 0, 0, 1) #Color unused cells black
                
                elif (warnings is not None) and i < len(warnings) and warnings[i]: #If there's an overtemp/overvolt warning, set the cell color to red
                   background_color = (1, 0, 0, 1) #Careful to skip the last 2 unused cells, the first 2 already filtered out

                self.add_widget(OutlinedLabel(text = texts[i], color = text_color, background_color = background_color,\
                    font_size = font_size, border_color = border_color, border_width = border_width, size_hint = size_hint))

        except Exception as e:
            print(f'[CRITICAL] Failed to create/update one or more segment labels ({e})')

class SegmentGrid(BoxLayout):
    def __init__(self, **kwargs):
        super(SegmentGrid, self).__init__(**kwargs)
        self.segments = []

        # Create 8 segments to begin with
        for i in range(8):
            segment = Segment()
            segment.add_placeholders()

            #ids is the dict which maps to the id segment_container which contains the segment layout
            self.ids.segment_container.add_widget(segment)
            self.segments.append(segment) #TODO theoretically not needed UNLESS WE'RE UPDATING???
    
    def get_label_text_from_data(self, volts, temps, x, y):
        #Special cases: top right (2) and bottom left (2) unused cells
        if (x == 3 and (y == 0 or y == 1)) or (x == 7 and (y == 16 or y == 17)):
            return '' #Empty cell
        
        #For all the other cells, linearize the 2D indices to the 1D data arrays we have
        #Careful because the data array has 140 entries but the GUI has 144 cells (4 empty)
        #So we need to go 2 indices back in the array, for all the cells after the 2 top right unused ones
        arr_idx_1D = (18 * x) + y - 2 * int(x >= 3)
        return f"{volts[arr_idx_1D]}V | {temps[arr_idx_1D]}°C" #Return the cell's label to the caller

    def get_segment_1D_range(self, i): #Filter the top right unused cells
        a = 18 * i - 2 * int(i >= 3)
        b = 18 * (i + 1) - 2 * int(i >= 3)

        return a, b

    def float_arr_to_n_decimals(self, floats, n):
        return [int(f * 10**n) / 10**n for f in floats]

    def update_segments_volts_temps(self, data_container): #First obvious update function for each of the individual cells
        #Limit data count to cell_count if more values are provided
        cell_pairs = data_container.cell_pairs
        volts = self.float_arr_to_n_decimals(data_container.voltages, CELL_VOLTAGE_DECIMALS)
        temps = data_container.temperatures
        warnings = data_container.volt_or_temp_warnings

        #Update each individual segment. Segments are built left to right, top to bottom
        # 1 2 3 4
        # 5 6 7 8
        for i in range(8):
            #Generate texts for each segment
            segment_texts = [self.get_label_text_from_data(volts, temps, i, j) for j in range(18)]

            (a, b) = self.get_segment_1D_range(i) #Pass the part of the warnings array that concerns this segment
            self.segments[i].configure_cells(segment_texts, warnings[a:b], i)

    #TODO tap a cell and you also get general SEGMENT HUMIDIDTY, balancing, etc
                
class MyApp(App):
    def build(self):
        Window.bind(on_request_close = self.on_request_close)

        self.running = True

        #Initialize and start the serial reader of the port and the data logger
        self.serial_reader = SerialReader(debug_mode = DEBUG_MODE, specified_port = 1)
        self.data_logger = Datalogger("log.txt", debug_mode = DEBUG_MODE, buffer_size = 3) #Write every 3 messages

        self.serial_reader.start()
        self.data_logger.start()

        self.title = "Prom Racing Navios 2025 'στο τσακ' TSAC Viewer"
        self.icon = 'icon.ico' #When running app as a script, the taskbar icon will be the default python logo
        #But when running as an exectutable, it will automatically sync to the window icon

        self.segment_grid = SegmentGrid() #widget!

        self.data_container = DataContainer(debug = DEBUG_MODE)
        self.data_update_thread = threading.Thread(target = self.update_data)
        self.data_update_thread.start()

        return self.segment_grid
    
    def on_request_close(self, *largs, **kwargs): #Call "destructor" from UI button
        #Kills the threads when closing the app (so that writing to files and other tasks finish)
        self.serial_reader.stop()
        self.data_logger.stop()

        self.running = False
        self.data_update_thread.join()
        if DEBUG_MODE:
            print('[DEBUG] Data update thread: Data reader thread stopped')

    def update_data(self):
        while self.running:
            #1) Ask reader if there is data available
            raw = self.serial_reader.get_message() #no-stall
            time.sleep(0.1) #Don't race with the write thread

            #2) Write to file and interpret the data in the DataContainer class
            if raw is not None:
                self.data_logger.write(raw)

                self.data_container.interpret_data(raw)

                #3) Update the graphical interface accordingly by asking the DataContainer for info
                    #TODO then update all cells accordingly (flag e.g. voltage, then array[])
                
                #Update individual cells if voltages of tempratures update
                if self.data_container.last_updated_list_ID in [2,3]:
                    #self.segment_grid.update_segments_volts_temps(self.data_container)
                    Clock.schedule_once(lambda dt: self.segment_grid.update_segments_volts_temps(self.data_container)) #For thread safety

                #More updates... TODO
    
if __name__ == '__main__':
    #serial_reader, data_logger, and other threads are now defined inside the MyApp() class
    MyApp().run()