#ATTENTION!!!!!!!!!!!!!!!!!!!!!!!!COM PORT FIXED TO 1 for virtual testing

#Important: changing the order of (0), (1), (2), (3) results in undefined behavior

#Define fundamental variables of the app (0)
FORCE_WINDOW_SIZE = None #Overrides forced fullscreen 
FORCE_FULLSCREEN = False
DEBUG_MODE = True

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

#Set app layout through the .kv file, otherwise use a string with .load_string()
Builder.load_file("layout.kv")

class Segment(GridLayout):
    def add_placeholders(self):
        self.set_texts([f"Local Cell Pair {j}" for j in range(1, 19)])

    def set_texts(self, texts):
        self.clear_widgets() #Erase previous labels and update
        #Don't re-create and re-link 142 widgets, just create new segments and add them to the already existing structure for efficiency

        try:
            for text in texts:
                #self.add_widget(Label(text = text, size_hint = (None, None), width = WINDOW_SIZE[0] // 8, height = WINDOW_SIZE[1] // 18))
                self.add_widget(Label(text = text, size_hint = (None, None), width = 205, height = 55))
                #BUG These are not set correctly, owing to window sizing imprecision. Why is that?
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
            self.segments.append(segment) #theoretically not needed UNLESS WE'RE UPDATING???
    
    def generate_segment_label_from_data(self, volts, temps, x, y):
        #Special cases: top right (2) and bottom left (2) unused cells
        if (x == 3 and (y == 0 or y == 1)) or (x == 7 and (y == 16 or y == 17)):
            return "" #Empty cell
        
        offset = 0 #Only 140 numbers to be placed BUT 144 cells total, we need to keep an offset when we skip the unused cells
        if x >= 3:
            offset = -2 #Go back 2 cells because 2 will be missing

        return f"{volts[18 * x + y + offset]}V | {temps[18 * x + y + offset]}`C"

    def update_segments_volts_temps(self, data_container): #First obvious update function for each of the individual cells
        #Limit data count to cell_count if more values are provided
        cell_pairs = data_container.cell_pairs
        volts = data_container.voltages[:cell_pairs]
        temps = data_container.temperatures[:cell_pairs]

        #Update each individual segment. Segments are built left to right, top to bottom
        # 1 2 3 4
        # 5 6 7 8
        for i in range(8):
            segment_texts = [self.generate_segment_label_from_data(volts, temps, i, j) for j in range(18)]
            self.segments[i].set_texts(segment_texts)

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