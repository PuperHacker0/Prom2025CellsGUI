#Important: the order of (0), (1), (2), (3) is specific
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
from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window
import threading

#Finally, import all our custom modules (4)
from SerialReader import *
from Datalogger import *
from DataContainer import *
from Graphics import *

#Set app layout through the .kv file, otherwise use a string with .load_string()
Builder.load_file("layout.kv")

class MyApp(App):
    def build(self):
        Window.bind(on_request_close = self.on_request_close)

        self.running = True

        #Initialize and start the serial reader of the port and the data logger
        self.serial_reader = SerialReader(debug_mode = DEBUG_MODE) #, specified_port = 1) #Change the input port to debug
        self.data_logger = Datalogger("serial_input_log.txt", debug_mode = DEBUG_MODE, buffer_size = 10) #Write every n messages

        self.serial_reader.start()
        self.data_logger.start()

        self.title = "Prom Racing Navios 2025 'στο τσακ' TSAC Viewer"
        self.icon = 'icon.ico' #When running app as a script, the taskbar icon will be the default python logo
        #But when running as an exectutable, it will automatically sync to the window icon

        self.main_layout = MainLayout() #widget!

        self.data_container = DataContainer(debug = DEBUG_MODE)
        self.data_update_thread = threading.Thread(target = self.update_data)
        self.data_update_thread.start()

        return self.main_layout
    
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
            time.sleep(0.1) #Avoid racing with the write thread

            #2) Write raw data to file and interpret the data in the DataContainer class
            if raw is not None:
                self.data_logger.write(raw)

                self.data_container.interpret_data(raw)

                #3) Update the graphical interface accordingly by asking the DataContainer for info                
                #Update individual cells if voltages of tempratures update
                if self.data_container.last_updated_list_ID in [2, 3]: #TEMPERATURE AND VOLTAGE CELL UPDATES
                    Clock.schedule_once(lambda dt: self.main_layout.update_segments_volts_temps(self.data_container)) #For thread safety
                elif self.data_container.last_updated_list_ID in [6, 7, 8]: #INFO PANEL UPDATES
                    Clock.schedule_once(lambda dt: self.main_layout.update_info_panel(self.data_container))

                #More updates... TODO
    
if __name__ == '__main__':
    #serial_reader, data_logger, and other threads are now defined inside the MyApp() class instead of inside of main
    MyApp().run()