#Threaded (async) serial reader class
#Will try all COM ports and see if any one sends data

import threading
from queue import Queue, Empty
import serial
import time

class SerialReader(threading.Thread):
    def __init__(self, baudrate = 112500, bytesize = 8, debug_mode = False, specified_port = -1):
        super().__init__() #First initialize the thread object itself
        self.thread = threading.Thread(target = self.async_read_from_port)
        
        self.queue = Queue()

        self.debug_mode = debug_mode

        #COM Port properties
        self.COM_port_number = specified_port
        self.serial_port = None
        self.baudrate = baudrate
        self.bytesize = bytesize

        self.connect_to_port() #Will connect to user set port if it is specified, otherwise it will try to find a port that sends data
        
    def start(self):
        self.running = True
        self.thread.start()

    def stop(self):
        self.running = False #Automatically kills the thread
        
        try:
            self.serial_port.close()
        except Exception as e:
            pass #We'll disconnect anyway so it doesn't matter
        
        if self.debug_mode:
            print("[DEBUG] Disconnected from serial port")

    def connect_to_port(self):
        if self.COM_port_number != -1:
            self.COM_port_number = "COM" + str(self.COM_port_number)
        else:
            self.COM_port_number = None

        #No need to close a previously opened port, as this is currently the first instance created

        conn_success = False

        while (not conn_success):        
            if self.COM_port_number != None: #Port to connect to is provided manually so connect to that one
                try:
                    self.serial_port = serial.Serial(port = self.COM_port_number, baudrate = self.baudrate, bytesize = self.bytesize)
                    conn_success = True
                except Exception as e:
                    print("[CRITICAL] Failed to connect to manually provided port! Retrying in 5 sec...")
                    time.sleep(5)
                    
            else: #Find the connected port if not manually provided
                for p in range(0, 20):
                    try:
                        self.serial_port = serial.Serial(port = "COM" + str(p), baudrate = self.baudrate, bytesize = self.bytesize)
                        conn_success = True
                        self.COM_port_number = "COM" + str(p)
                    except Exception as e:
                        pass #This port didn't work, try the next ones
                
                if conn_success == False: #None of the ports worked!
                    print("[CRITICAL] Failed to detect any connected port! Retrying in 5 sec...")
                    time.sleep(5)
        
        if conn_success and self.debug_mode:
            print("[DEBUG] SerialReader: Successfully established connection to", self.COM_port_number)

    def async_read_from_port(self):
        previous_successful_read_time = time.time() #Start time at the beginning
        
        while self.running:
            try:
                if self.serial_port.in_waiting > 0:
                    #Read until } (end of message) and remove intermittent newlines
                    data = self.serial_port.read_until(b'}').decode('utf-8').replace("\n", "")

                    if data == '}':
                        continue
                    
                    if len(data) != 0:
                        if self.debug_mode:
                            print('[DEBUG] Read message: ' + str(data))

                        self.queue.put(data)
                        previous_successful_read_time = time.time()
                    else:
                        current_time = time.time()

                        if current_time - previous_successful_read_time > 10:
                            print("[CRITICAL] Haven't received message from port for 10 seconds. Retrying in 5 sec...")
                            time.sleep(5)
            except Exception as e:
                if str(e) == "byref() argument must be a ctypes instance, not 'NoneType'":
                    pass
                else:
                    print(f"[CRITICAL] Error ({e}) while reading data from port")

    def get_message(self): #Return 1 message at a time
        try:
            return self.queue.get_nowait() #Non-blocking
        except Exception as e: #Queue is empty
            return None
    
    #For testing/debugging
    def _debug_write_to_port(self, message):
        self.serial_port.write(message)