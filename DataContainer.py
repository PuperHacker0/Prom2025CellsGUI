import json

class DataContainer():
    def __init__(self, debug):
        self.segment_sensors = 16
        self.cell_pairs = 140

        self.debug_mode = debug
        
        self.last_updated_list_ID = 0
        self.humidities = [0 for i in range(self.segment_sensors)] #16 numbers ID1
        self.temperatures = [0 for i in range(self.cell_pairs)] #140 numbers ID2
        self.voltages = [0 for i in range(self.cell_pairs)] #140 numbers ID3
        self.pec_errors = [0 for i in range(self.segment_sensors)] #16 numbers ID4
        self.balancing = [0 for i in range(self.cell_pairs)] #140 numbers ID5
        self.accumulator_info = {} #ID6
        self.isabelle_info = {} #ID7
        self.elcon_info = {} #ID8

    def string_to_list(self, s):
        return [int(n) for n in s[1:len(s) - 1].split(',')] #Remove the brackets and convert remaining numbers to ints, pack them in a list
    
    def string_to_dict(self, s):
        return json.loads(s)
    
    MESSAGE_INTERPRETATION_FAILURE_COUNT = 0
    def interpret_data(self, raw_data):
        d = raw_data.replace('\n', '').replace(' ', '') #remove all spaces and newlines (that are not needed anywhere)
        
        if d[0] != '{':
            print('[DEBUG] Message not starting with { found, assumed first message and skipped')
            MESSAGE_INTERPRETATION_FAILURE_COUNT += 1

            if MESSAGE_INTERPRETATION_FAILURE_COUNT >= 10:
                print('[CRITICAL] >=10 Messages not interpreted correctly. Counter was reset. Check connections...')
                MESSAGE_INTERPRETATION_FAILURE_COUNT = 0
            
            return
        else:
            try:
                first = d.split(':')[0]
                message_type = first[2:len(first) - 1] #Get first part, remove the { and "" (so, remove an extra 3 chars)
                message_content = d[((3 + len(message_type)) + 1):len(d) - 1] #Get second part, (first part + 3 chars) and remove the }

                if message_type in ['AccumulatorInfo', 'IsabelleInfo', 'ElconInfo']:
                    message_content += '}'

                if self.debug_mode:
                    print("Message type:", message_type)
                    print("Message content:", message_content, '\n')

                if message_type == 'Humidities': #TODO
                    self.last_updated_list_ID = 1
                    self.humidities = self.string_to_list(message_content)
                elif message_type == 'Temperatures':
                    self.last_updated_list_ID = 2
                    self.temperatures = self.string_to_list(message_content)
                elif message_type == 'Voltages':
                    self.last_updated_list_ID = 3
                    self.voltages = self.string_to_list(message_content)
                elif message_type == 'PEC_Errors':
                    self.last_updated_list_ID = 4
                    self.pec_errors = self.string_to_list(message_content)
                elif message_type == 'Balancing':
                    self.last_updated_list_ID = 5
                    self.balancing = self.string_to_list(message_content)
                elif message_type == 'AccumulatorInfo':
                    self.last_updated_list_ID = 6
                    self.accumulator_info = self.string_to_dict(message_content) #Restore end char for dict form
                elif message_type == 'IsabelleInfo':
                    self.last_updated_list_ID = 7
                    self.isabelle_info = self.string_to_dict(message_content)
                elif message_type == 'ElconInfo':
                    self.last_updated_list_ID = 8
                    self.elcon_info = self.string_to_dict(message_content)
                else:
                    raise Exception('Unknown data identifier')
            except Exception as e:
                print(f'[CRITICAL] Failed to interpret message ({e})')

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