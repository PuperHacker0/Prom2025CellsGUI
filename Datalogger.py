''' Async datalogger class
To use the datalogger, first create a datalogger instanace
Then use the start() method to start the logging thread
Use the write() method to send data to write. The data needs to be convertible to string type
When done use the stop() method to stop the logger
    Note: stop() does not terminate the datalogger instance itself.
    It just stops the logger thread, so no data will be written to the file from the moment the method is called.
    However, we can still keep using the datalogger instance, for example to write messages to it but not have them stored in a file
    Restarting the logger with the start() method will resume logging to the file
    clear_log() can also be called AFTER stopping() the datalogger thread
The functions marked _ are not meant to be called by the user.
'''

import threading
import time
from queue import Queue, Empty, Full

class Datalogger():
    def __init__(self, filename = 'session_log.txt', buffer_size = 10, buffer_sampling_limit = True, buff_sampl_freq = 10, debug_mode = False):
        #Create the inner queue where the data will be stored
        self.buffer = Queue()
        self.buffer_limit = buffer_size

        #Set the output filename for the log file
        self.output_filename = filename
        
        #Create the inner thread which will be run when starting the logger
        self.thread = threading.Thread(target = self.__write_to_file)
        self.flush_buffer = False

        self.buffer_sampling_freq_limited = buffer_sampling_limit
        self.buffer_sampling_frequency = buff_sampl_freq #Check the queue for messages 5 times per second IF ENABLED

        self.debug_mode = debug_mode

    def start(self):
        self.thread.start()
        self.write('<--DATALOGGER STARTED-->')

        if self.debug_mode:
            print('[DEBUG] Datalogger: Datalogger thread has started')
    
    def stop(self):
        self.write('-->DATALOGGER STOPPED<--')

        time.sleep(1) #For some reason it needs some time before we can kill it
        self.flush_buffer = True

    def clear_log(self):
        f = open(self.output_filename, "w")
        f.write("\n")
        f.close()

        if self.debug_mode:
            print("[DEBUG] Datalogger: Log file cleared")

    def write(self, data):
        try:
            self.buffer.put_nowait((self.__get_timestamp_string(), data)) #A message is the time + the data
        except Exception as e:
            print('[DEBUG] Datalogger: Failed to write to buffer')
            

    def __write_to_file(self):
        #Thread function to be kept running, it will terminate once the flush flag is set to true
        while True:
            if self.buffer.qsize() > self.buffer_limit or self.flush_buffer: #Write to file when enough messages have come
                f = open(self.output_filename, "a")

                try:
                    for i in range(self.buffer_limit):
                        datum = self.buffer.get_nowait() #Removes AND returns the item from the queue
                        
                        f.write(datum[0] + ' ' + str(datum[1]) + '\n\n') #Datum[1]'s format can be processed/changed here
                        #Data needs to be convertible to string
                except Empty:
                    pass #Nothing to write, complete this write cycle
                except Exception as e:
                    if self.debug_mode:
                        print(f"[DEBUG] Datalogger: Buffer write FAILED ({e}). Datalogger stopped.")
                    return

                f.close()

                if self.debug_mode:
                    print("[DEBUG] Datalogger: Successfully wrote queue to file")
                    self.write('[DEBUG] Datalogger: (delayed message) Wrote chunk of size ' + str(self.buffer_limit))

                #Terminate the thread right after the queue has been emptied so that the remaining messages won't be lost
                if self.flush_buffer:
                    self.flush_buffer = False

                    if self.debug_mode:
                        print('[DEBUG] Datalogger: Datalogger thread stopped')
                    
                    return
                    
                if self.buffer_sampling_freq_limited:
                    time.sleep(1 / self.buffer_sampling_frequency) #buffer sampling interval
                #Don't race with the other threads to ask if the buffer has been updated

    def __get_timestamp_string(self):
        return time.strftime("[%H:%M:%S]", time.localtime())

#Example
if __name__ == "__main__":
    d = Datalogger()
    d.start()

    for i in range(700):
        d.write(i)

    d.stop()