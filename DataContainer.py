import json

MAX_CELL_VOLTAGE = 4.3
MIN_CELL_VOLTAGE = 3.0
MAX_CELL_TEMP = 60

class DataContainer():
    def __init__(self, debug):
        self.segment_sensors = 16
        self.cell_pairs = 140
        self.info_panel_labels = 16

        self.debug_mode = debug
        
        self.last_updated_list_ID = 0

        self.temperatures = [0 for i in range(self.cell_pairs)] #140 numbers, ID2
        self.voltages = [0 for i in range(self.cell_pairs)] #140 numbers, ID3
        self.volt_or_temp_warnings = [False for _ in range(self.cell_pairs)]

        self.humidities = [0 for i in range(self.segment_sensors)] #16 numbers, ID1
        self.pec_errors = [0 for i in range(self.segment_sensors)] #16 numbers, ID4
        self.balancing = [0 for i in range(self.cell_pairs)] #140 numbers, ID5
        self.accumulator_info = {} #Dict, ID6
        self.isabelle_info = {} #Dict, ID7
        self.elcon_info = {} #Dict, ID8

        self.info_panel_data_categories = ["Ams_Error", "Imd_Error", "AIR_P_Supp", "AIR_M_Supp", "AIR_P_State", "AIR_M_State",\
            "over60_dclink", "V_Side_Voltage", "Current", "Target_Voltage", "Output_Voltage", "Target_Current", "Output_Current",\
                "Elcon_connected", "Target_charge_state", "Elcon_charge_status"]
        self.accumulator_info_idxs = (0, 6)
        self.isabelle_info_idxs = (7, 8)
        self.elcon_info_idxs = (9, 15)

        self.info_panel_data_values = ['N/A'] * self.info_panel_labels

    def generate_cell_temp_volt_warnings(self):
        #This is called when voltages OR temps have just been updated and we want to see whether any cell has gone bad
        for idx in range(self.cell_pairs):
            self.volt_or_temp_warnings[idx] = ((self.voltages[idx] > MAX_CELL_VOLTAGE) or (self.voltages[idx] < MIN_CELL_VOLTAGE)\
                                               or (self.temperatures[idx] != '-' and self.temperatures[idx] > MAX_CELL_TEMP))
            #Make sure to ignore the dashes in the places where the temperature is 0 or 255, only process cells with a value
            
    def update_info_panel_data_values(self):
        data_range = (None, None)
        subject_dict = {}
        if self.last_updated_list_ID == 6: #Accumulator info
            data_range = self.accumulator_info_idxs
            subject_dict = self.accumulator_info
        elif self.last_updated_list_ID == 7: #Isabelle info
            data_range = self.isabelle_info_idxs
            subject_dict = self.isabelle_info
        elif self.last_updated_list_ID == 8: #Elcon info
            data_range = self.elcon_info_idxs
            subject_dict = self.elcon_info
        else:
            raise Exception('Invalid info panel update')
        
        #Get the range of the data inside the list and which dict they're in, and then the prorcess of updating the info is the same
        for i in range(data_range[0], data_range[1] + 1): #+1 because we want to reach up to the last index
            data_to_request = self.info_panel_data_categories[i]
            data_read = 'N/A'

            if data_to_request in subject_dict:
                data_read = subject_dict[data_to_request]
            #else just skip this one piece of info as N/A and continue
            self.info_panel_data_values[i] = data_read

    def string_to_list(self, s):
        return [float(n) for n in s[1:len(s) - 1].split(',')] #Remove the brackets and convert remaining numbers to floats, pack them in a list
    
    def string_to_dict(self, s):
        return json.loads(s)
    
    def remove_zeroes(self, list):
        new_list = []
        for i in list:
            if i != 0:
                new_list.append(i)
        print(new_list)
        return new_list

    def interpret_data(self, raw_data):
        d = raw_data.replace('\n', '').replace(' ', '') #remove all spaces and newlines (that are not needed anywhere)

        if d[0] != '{':
            print('[DEBUG] Message not starting with { found in queue, check data format!')
            return
        else:
            try:
                first = d.split(':')[0]
                message_type = first[2:len(first) - 1] #Get first part, remove the { and "" (so, remove an extra 3 chars)
                message_content = d[((3 + len(message_type)) + 1):len(d) - 1] #Get second part, (first part + 3 chars) and remove the }

                if self.debug_mode:
                    print("Message type:", message_type)
                    #print("Message content:", message_content, '\n')
                    #pass

                if message_type == 'Humidities': #TODO
                    #print('Read humidities, ignored for now...')
                    return
                    self.last_updated_list_ID = 1
                    self.humidities = self.string_to_list(message_content)
                elif message_type == 'Temperatures':
                    self.last_updated_list_ID = 2

                    #Don't update with new faulty input if there is an issue with it
                    new_temps = self.string_to_list(message_content)[:self.cell_pairs]

                    if len(new_temps) < self.cell_pairs:
                        raise Exception('Too few temperature values provided!')
                    
                    self.temperatures = new_temps

                    for i in range(len(self.temperatures)):
                        if self.temperatures[i] == 0 or self.temperatures[i] == 255:
                            self.temperatures[i] = '-' #Remove the readings in the cells where there are no temp sensors
                    
                    self.generate_cell_temp_volt_warnings() #First remove the 0 readings then proceed

                elif message_type == 'Voltages':
                    self.last_updated_list_ID = 3
                    
                    #Don't update with new faulty input if there is an issue with it
                    new_volts = self.remove_zeroes(self.string_to_list(message_content))[:self.cell_pairs]
                    #We'll always be receiving 144 numbers, 4 of them are 0s (dead cells), so skip them and continue
                    #Ensure then that we're sending 140 numbers only
                    
                    if len(new_volts) < self.cell_pairs:
                        raise Exception('Too few voltage values provided!')
                    
                    self.voltages = new_volts
                    self.generate_cell_temp_volt_warnings()
                elif message_type == 'PEC_Errors': #TODO
                    #print('Read PEC_Errors, ignored for now...')
                    return
                    self.last_updated_list_ID = 4
                    self.pec_errors = self.string_to_list(message_content)
                elif message_type == 'Balancing': #TODO
                    #print('Read balancing, ignored for now...')
                    pass
                    self.last_updated_list_ID = 5
                    self.balancing = self.string_to_list(message_content)
                elif message_type == 'AccumulatorInfo':
                    self.last_updated_list_ID = 6
                    self.accumulator_info = self.string_to_dict(message_content) #Restore end char for dict form
                    self.update_info_panel_data_values()
                elif message_type == 'IsabelleInfo':
                    self.last_updated_list_ID = 7
                    self.isabelle_info = self.string_to_dict(message_content)
                    self.update_info_panel_data_values()
                elif message_type == 'ElconInfo':
                    self.last_updated_list_ID = 8
                    self.elcon_info = self.string_to_dict(message_content)
                    self.update_info_panel_data_values()
                else:
                    raise Exception('Unknown data identifier')
            except Exception as e:
                print(f'[CRITICAL] Failed to interpret message ({e}): ' + message_type)

    def get_last_updated_data(self):
        packet = [self.last_updated_list_ID]

        if self.last_updated_list_ID == 1:
            packet.append(self.humidities)
        if self.last_updated_list_ID == 2:
            packet.append(self.temperatures)
        if self.last_updated_list_ID == 3:
            packet.append(self.voltages)
        if self.last_updated_list_ID == 4:
            packet.append(self.pec_errors)
        if self.last_updated_list_ID == 5:
            packet.append(self.balancing)
        if self.last_updated_list_ID == 6:
            packet.append(self.accumulator_info)
        if self.last_updated_list_ID == 7:
            packet.append(self.elcon_info)

        return packet