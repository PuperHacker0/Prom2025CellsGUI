from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ListProperty, NumericProperty
from kivy.graphics import Color, Rectangle, Line

CELL_VOLTAGE_DECIMALS = 3

#Change this class if cell arrangement changes
class CellArrangement:
    def is_unused_cell_idx(x, y):
        return (x == 3 and (y == 0 or y == 1)) or (x == 7 and (y == 16 or y == 17))

    def array_traversal_index_mapping(x, y):
        #ITERATOR FUNCTION: Change the order of traversal function in case the layout or sensor positions change
        #Here we create the standard winding order of traversal (see image)

        result = 0
        if x >= 4: #U shape (bottom segments)
            result += 18 * (x - 4) #Add as many cells as are before us (bottom segments only)

            if y % 2 == 0: #y is even (left column going down)
                result += y // 2
            else:
                result += 18 - (y + 1) // 2 #y is odd (right column going up)
            
            if result > 61: #-2 for the bottom 2 cells for the rightmost column
                result -= 2
        else: #Π shape (upper segments)
            result += 18 * (4 + (3 - x)) #Add 4 bottom segment cells +whichever are up

            if y % 2: #Right column going up (odds)
                result += (18 - (y + 1)) // 2
            else: #Left column going down (evens)
                result += 9 + y // 2

            if result > 80: #Subtract all 4 unused cells
                result -= 4
            else:
                result -= 2 #Subtract only the bottom right 2 unused cells
        return result

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
            font_size = 24 #Large numbers
            border_color = (1, 1, 1, 0.7) #Faded white outline
            border_width = 1.5
            size_hint = (1, 1) # Fill cell out
            text_color = (1, 1, 1, 1) #White text
            
            for i in range(18):
                background_color = (0, 0.2, 0, 1)
                    
                if CellArrangement.is_unused_cell_idx(segment_number, i):
                    background_color = (0, 0, 0, 1) #Color unused cells black
                
                elif (warnings is not None) and i < len(warnings) and warnings[i]: #If there's an overtemp/overvolt warning, set the cell color to red
                   background_color = (1, 0, 0, 1) #Careful to skip the last 2 unused cells, the first 2 already filtered out

                self.add_widget(OutlinedLabel(text = texts[i], color = text_color, background_color = background_color,\
                    font_size = font_size, border_color = border_color, border_width = border_width, size_hint = size_hint))

        except Exception as e:
            print(f'[CRITICAL] Failed to create/update one or more segment labels ({e})')

class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super(MainLayout, self).__init__(**kwargs)
        self.segments = []

        # Create 8 segments to begin with
        for i in range(8):
            segment = Segment()
            segment.add_placeholders()

            #ids is the dict which maps to the id segment_container which contains the segment layout
            self.ids.segment_container.add_widget(segment)
            self.segments.append(segment)
        
        for i in range(16): #Placeholders at first
            label = OutlinedLabel(text = 'Status data ' + str(i), font_size = 20, border_color = (1, 1, 1, 0.7),\
                border_width = 2, size_hint = (1, 1), color = (1, 1, 1, 1), background_color = (0.1, 0.1, 0.1, 1))
            self.ids.info_panel.add_widget(label)

    def get_label_text_from_data(self, volts, temps, x, y):
        #Special cases: top right (2) and bottom left (2) unused cells
        if CellArrangement.is_unused_cell_idx(x, y):
            return '' #Empty cell
        
        #For all the other cells, linearize the 2D indices to the 1D data arrays we have
        #Careful because the data array has 140 entries but the GUI has 144 cells (4 empty)
        #So we need to go 2 indices back in the array, for all the cells after the 2 top right unused ones
        arr_idx_1D = CellArrangement.array_traversal_index_mapping(x, y)

        if temps[arr_idx_1D] == '-': #If temp sensor unavailable, return just the voltage
            return f"{volts[arr_idx_1D]}V"
        else:
            return f"{volts[arr_idx_1D]}V   {temps[arr_idx_1D]}°C" #Return the cell's label to the caller

    def get_segment_1D_range(self, i): #Filter the top right unused cells
        a = 18 * i - 2 * int(i >= 3)
        b = 18 * (i + 1) - 2 * int(i >= 3)

        return a, b

    def float_arr_to_n_decimals(self, floats, n):
        return [int(f * 10**n) / 10**n for f in floats]

    def update_segments_volts_temps(self, data_container): #First obvious update function for each of the individual cells
        #print("\n\nUPDATING VOLTS OR TEMPS\n\n")
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

    def update_info_panel(self, data_container):
        self.ids.info_panel.clear_widgets() #Erase previous labels to update
        
        #These are duplicate settings for now, we can generalize them in the class in the future
        font_size = 20
        border_color = (1, 1, 1, 0.7) #Faded white outline
        border_width = 2
        size_hint = (1, 1) # Fill cell out
        text_color = (1, 1, 1, 1) #White text
        background_color = (0.1, 0.1, 0.1, 1)

        data_categories = data_container.info_panel_data_categories[:] # [:] used to make copies of the lists in DataContainer
        data_values = data_container.info_panel_data_values[:] # [:] so as not to mutate the data

        #First process the data values, because these depend on the data_categories which relate exactly to the dicts in the code
        #Add postfix units of measurement
        for i in range(len(data_values)):
            if data_categories[i] in ["V_Side_Voltage", "Target_Voltage", "Output_Voltage"]:
                data_values[i] += 'V'
            elif data_categories[i] in ["Current", "Target_Current", "Output_Current"]:
                data_values[i] += 'A'
            #We can later assign postfixes to the other info panel variables too...

        #Then, process the data labels themselves now that a change here won't affect the data value processing
        data_categories = [x.replace('_', ' ') for x in data_categories] #Remove underscores, .upper() is another idea

        texts = [data_categories[i] + ': ' + data_values[i] for i in range(16)]

        for i in range(16): #TODO these should not be hardcoded
            self.ids.info_panel.add_widget(OutlinedLabel(text = texts[i], color = text_color, background_color = background_color,\
                font_size = font_size, border_color = border_color, border_width = border_width, size_hint = size_hint))