from pyrevit import DB 
import csv
import os
import io

red =  DB.Color(255, 0, 0)
black = DB.Color(0,0,0)

pipe_colors = [
    DB.Color(119, 187, 17),
    DB.Color(0, 170, 221),
    DB.Color(0, 255, 0),
    DB.Color(255, 255, 0),
    DB.Color(255, 0, 255),
    DB.Color(0, 255, 255),
    DB.Color(255, 130, 0),
    DB.Color(130, 0, 255),
    DB.Color(130, 130, 0),
    DB.Color(238, 0, 102),
    DB.Color(0, 66, 130 ),
    DB.Color(192, 192, 192),
]

class PipeData:
    def __init__(self, name, size, max_fu, color):
        self.name = name
        self.size = size
        self.max_fu = max_fu
        self.color = color

def get_csv_file_path(file_name):
    absolute_path = os.path.dirname(os.path.abspath(__file__))
    relative_path = "fixture_unit_values\Wisconsin\Domestic-Water\Copper_Type-L"
    file_path = os.path.join(absolute_path, relative_path, file_name)
    return file_path

def initialize_pipe_data_array(row):
    pipe_data = [row[0]]
    for i in range(1,len(row)):
        # Pipe size header is arranged like "size_1/2_0.042" so that the display name and size can be extracted automatically
        pipe_size_header_values = row[i].split("_")
        pipe_name = pipe_size_header_values[1]
        pipe_size = float(pipe_size_header_values[2])

        # Use the colors we have declared and loop back to the start once we reach the end of the list
        pipe_color = pipe_colors[i % len(pipe_colors)]

        pipe_data.append(PipeData(pipe_name, pipe_size, None, pipe_color))
    return pipe_data

def process_row_values(row):
    processed_row = []

    for value in row:
        v = None
        try:
            v = float(value)
        except:
            v = None

        processed_row.append(v)

    return processed_row

def get_pipe_data(pressure_loss):
    pipe_data = []
    
    file_name = "FT.csv"

    csv_path = get_csv_file_path(file_name)
    
    with io.open(csv_path, encoding='utf-8-sig') as csvfile:
        reader = csv.reader(csvfile, dialect="excel")
        for row in reader:
            if reader.line_num == 1:
                pipe_data = initialize_pipe_data_array(row)
                continue
        
            processed_row = process_row_values(row)

            if processed_row[0] > pressure_loss:
                # The first value in the row is the pressure loss over 100' of pipe.
                # If we exceed our maximum allowable pressure loss then we are done.
                break
            
            # We want to skip the first value since it is the pressure loss
            for i in range(1, len(processed_row)):
                # Some pipe sizes have a maximum fixture unit value and the rest of the values in the table are blank, so we want to keep the maximum valid vlaue
                value = processed_row[i]
                if value is not None:
                    pipe_data[i].max_fu = processed_row[i]

        # [0] was pressure loss so we don't need it anymore. We will replace it with a 0 Fixture unit indicator
        pipe_data[0]=PipeData("No Flow", 0, 0, black)

        # We will add one more 'size' indicator to show whether we exceeded the maximum value we can reach
        pipe_data.append(PipeData("Over", 0, 999999999, red))

        return pipe_data
