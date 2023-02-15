import json
import csv
import os
import tkinter as tk
from tkinter import filedialog
from functools import partial
import math
from scipy.optimize import least_squares
import matplotlib.pyplot as plt
import numpy as np
import itertools
import random


class TeseWindow(tk.Tk):
    """
        When the rectangle was instantiated this dictionary will link AP name with rectangle drawn on the canvas
        {'FTM_responder_1': 31, 'FTM_responder_2': 33, 'FTM_responder_3': 35, 'FTM_responder_4': 37, 'FTM_responder_5': 39, 'FTM_responder_6': 41}
    """
    ap_locations_rect_id = {}
    """
        Links AP name with its coordinates. The coordinates are multiplied by 100. Which means at the real world 'FTM_responder_1' is positioned at (8.1, 4.8)
        {'FTM_responder_1': (81.0, 48.0), 'FTM_responder_2': (500.0, 600.0), 'FTM_responder_3': (1000.0, 248.0), 'FTM_responder_4': (500.0, 300.0), 'FTM_responder_5': (269.0, 600.0), 'FTM_responder_6': (1000.0, 540.0)}
    """
    ap_locations_coordinate = {}
    """
        Variable that has what information already was imported. There is no explict use.
    """
    control = {}
    """
        This variable holds a list of experience names that was imported. Change the current experience will change the mobile location on the canvas
        ['EXP_1', 'EXP_2', 'EXP_3', 'EXP_4', 'EXP_5', 'EXP_6']
    """
    experience_options = []
    """
        Holds a list of dictionary that relate experience with the mobile location coordinate
        [{'name': 'EXP_1', 'xCoordinate': 2.1, 'yCoordinate': 2.1, 'zCoordinate': 0}, {'name': 'EXP_2', 'xCoordinate': 10, 'yCoordinate': 1, 'zCoordinate': 0}, {'name': 'EXP_3', 'xCoordinate': 3, 'yCoordinate': 0.36, 'zCoordinate': 0.73}, {'name': 'EXP_4', 'xCoordinate': 0.5, 'yCoordinate': 0.96, 'zCoordinate': 0.93}, {'name': 'EXP_5', 'xCoordinate': 5, 'yCoordinate': 6, 'zCoordinate': 0}, {'name': 'EXP_6', 'xCoordinate': 8.2, 'yCoordinate': 0, 'zCoordinate': 0.73}]
    """
    mobile_information = {}
    """
        Holds the id for tracker the rectangle role playing as the mobile in the canvas
    """
    mobile_location_id_rect = 0

    """
        The Data variable will contain the ranging distance information regarding all experience and all APs 
        {'EXP_1': {'FTM_responder_6': [7.934, 7.812, 7.907, 7.818, 7.91, 7.931,...]},
        {'FTM_responder_4': [7.934, 7.812, 7.907, 7.818, 7.91, 7.931,...]}......,
        
        {'EXP_2': {'FTM_responder_6': [7.934, 7.812, 7.907, 7.818, 7.91, 7.931,...]},
        {'FTM_responder_4': [7.934, 7.812, 7.907, 7.818, 7.91, 7.931,...]}}
    
    """
    data = {}
    """
        This variable will contain  a dictionary that link EXP and checkbox in the GUI. This variable is used to plot only the EXPs selected
        {'EXP_1': <tkinter.BooleanVar object at 0x000002C8EDF19B10>, 'EXP_2': <tkinter.BooleanVar object at 0x000002C8EDF19850>, 'EXP_3': <tkinter.BooleanVar object at 0x000002C8EDF19C50>}
    """
    include_menu_exp_variables = {}

    """
        This variable will contain  a dictionary that link AP and checkbox in the GUI. This variable is used to plot only the APs selected
        {'FTM_responder_1': <tkinter.BooleanVar object at 0x000002C8EDF18290>, 'FTM_responder_2': <tkinter.BooleanVar object at 0x000002C8EDF18490>, 'FTM_responder_3': <tkinter.BooleanVar object at 0x000002C8EDF18550>, 'FTM_responder_4': <tkinter.BooleanVar object at 0x000002C8EDF18590>, 'FTM_responder_5': <tkinter.BooleanVar object at 0x000002C8EDF18610>, 'FTM_responder_6': <tkinter.BooleanVar object at 0x000002C8EDF18690>}
    """
    include_menu_ap_variables = {}

    must_include_LMS_line = None
    def __init__(self):
        super().__init__()
        self.title("WiFi RTT Analysis")
        self.geometry("1100x700")
        # Create a canvas
        self.canvas = tk.Canvas(self, width=1100, height=700)
        self.canvas.pack()
        self.create_grid(10,6)
        self.menubar = tk.Menu(self)
        self.config(menu=self.menubar)
        self.create_menu_file()
        self.create_menu_analysis()


    def create_menu_analysis(self):
        self.must_include_LMS_line = tk.BooleanVar()
        analysis_menu = tk.Menu(self.menubar)
        self.menubar.add_cascade(label="Analysis", menu=analysis_menu)
        analysis_menu.add_command(label="Plot", command=self.plot_scatter)
        analysis_menu.add_checkbutton(label="Must Include LMS line", onvalue=1, offvalue=0,
                                              variable=self.must_include_LMS_line)

    def create_menu_file(self):
        # Create a File menu with options to Exit and Save
        file_menu = tk.Menu(self.menubar)
        self.menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Import configuration file", command=self.import_json_configuration)
        file_menu.add_command(label="Import mobile location", command=self.import_json_mobile_location)
        file_menu.add_command(label="Import data", command=self.import_data)
        file_menu.add_command(label="Exit", command=self.quit)

    def create_experience_menu(self, data):
        for item in data:
            self.experience_options.append(item["name"])
        experience_menu = tk.Menu(self.menubar)
        self.menubar.add_cascade(label="Mobile location at position", menu=experience_menu)
        for item in self.experience_options:
            exp_x = next(xx for xx in data if xx["name"] == item)
            x_coordinate = exp_x["xCoordinate"]
            y_coordinate = exp_x["yCoordinate"]
            experience_menu.add_command(label=item,
                                        command=partial(self.draw_mobile_location, x_coordinate, y_coordinate))

    # Define the function to be minimized
    def func(self,params, x, y):
        m, b = params
        y_pred = m * x + b
        return y_pred - y


    def plot_scatter(self):
        fig, ax = plt.subplots()
        all_data_x = []
        all_data_y = []
        for exp in self.include_menu_exp_variables:
            if(self.include_menu_exp_variables[exp].get()):
                for ap in self.include_menu_ap_variables:
                    if(self.include_menu_ap_variables[ap].get()):

                        number_of_colors = 80
                        colors = itertools.cycle(["#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)])
                                                  for i in range(number_of_colors)])
                        data_y = self.data[exp][ap]
                        exp_x = next(xx for xx in self.mobile_information if xx["name"] == exp)
                        rect1_x1, rect1_y1 = self.ap_locations_coordinate[ap]
                        rect1_x1 = rect1_x1 / 100
                        rect1_y1 = rect1_y1 / 100
                        rect2_x1 = float(exp_x["xCoordinate"].replace(',','.'))
                        rect2_y1 = float(exp_x["yCoordinate"].replace(',','.'))

                        distance = math.sqrt((rect1_x1 - rect2_x1) ** 2 + (rect1_y1 - rect2_y1) ** 2)

                        data_x = [distance] * len(self.data[exp][ap])
                        all_data_x+= data_x
                        all_data_y+= data_y
                        if (len(data_x) > 0):
                            ax.scatter(data_x, data_y, s=20, color=next(colors) ,alpha=0.6)
                            ax.plot(data_x, range(0,len(data_y)), color="gray",alpha=0.2)
                            # Add an annotation to the bounding box
                            random_float = np.random.uniform(low=-1, high=1)
                            xmin = (data_x[0])
                            ymin = min(data_y)

                            '''plt.annotate(f'{ap}_{exp}',
                                         xy=(xmin, ymin), xycoords='data',
                                         xytext=(xmin + 1 + random_float, ymin - 1 + random_float), textcoords='data',
                                         arrowprops=dict(arrowstyle="->",
                                                 connectionstyle="arc3"))
                            '''
        if(self.must_include_LMS_line.get()):
            # Define the initial guess for the parameters
            params0 = [1, 1]

            # Use the least_squares function to find the line of best fit
            result = least_squares(self.func, params0, args=(np.array(all_data_x), np.array(all_data_y)))

            # Extract the optimal values of m and b from the result
            m, b = result.x
            print(f'm={m} b={b}')
            LMS_y_values = [y*m+b for y in range(0, 100) ]
            ax.plot(range(0, 100), LMS_y_values, color="red")

        ax.plot(range(0, 100), range(0, 100), c='purple')
        ax.set(xlim=(0, 16), xticks=np.arange(start=0, stop=16, step=1),
               ylim=(0, 16), yticks=np.arange(start=0, stop=16, step=0.5))

        ax.set_xlabel("Ground of Truth Distances Values")
        ax.set_ylabel("FTM Distances Values")
        ax.set_title("FTM vs Ground Truth")
        plt.rc('xtick', labelsize=8)
        plt.rc('ytick', labelsize=8)
        plt.rc('legend', fontsize=10)  # legend fontsize
        font = {'family': 'monospace',
                'weight': 'bold',
                'size': 'larger'}
        plt.show()
        fig.savefig('output.png')



    def create_grid(self,x_units,y_units):
        # Draw x-axis
        self.canvas.create_line(0, 0, x_units *100, 0, width=2)

        # Draw y-axis
        self.canvas.create_line(0, 0, 0, y_units * 100, width=2)

        # Display unit steps on x-axis
        for i in range(1, 11):
            self.canvas.create_text(i*100, 22, text=str(i))

        # Display unit steps on y-axis
        for i in range(1, 7):
            self.canvas.create_text(22, i*100, text=str(i))

    def draw_distances(self):
        if (hasattr(self, "mobile_location_id_rect") and hasattr(self,"ap_locations_rect_id")):
            rect2_x1, rect2_y1, rect2_x2, rect2_y2 = self.canvas.coords(self.mobile_location_id_rect)
            for ap in self.ap_locations_rect_id:
                # Extract the x1, y1, x2, y2 coordinates of the two rectangles
                rect1_x1, rect1_y1, rect1_x2, rect1_y2 = self.canvas.coords(self.ap_locations_rect_id[ap])
                # Draw the line between the two rectangles
                line = self.canvas.create_line(rect1_x1, rect1_y1, rect2_x1, rect2_y1, width=1, fill="gray")
                # Calculate the distance between the two rectangles
                distance = math.sqrt((rect1_x1 - rect2_x1) ** 2 + (rect1_y1 - rect2_y1) ** 2) /100
                # Find the midpoint of the line
                x = (rect2_x1 + rect1_x1) / 2
                y = (rect2_y1 + rect1_y1) / 2
                #Create a text label for the distance
                self.canvas.create_text(x, y, text=f"{distance: .2f}", font=("Arial", 10),fill="red")

    def import_json_mobile_location(self):
        filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filename:
            with open(filename, "r") as f:
                data = json.load(f)
                self.mobile_information = data
                self.create_experience_menu(data)
                self.control["mobile_location_file"] = True



    def import_json_configuration(self):
        filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filename:
            with open(filename, "r") as f:
                data = json.load(f)
                for entry in data:
                    x = (float(entry["xCoordinate"]) * 100)
                    y = (float(entry["yCoordinate"]) * 100)
                    self.ap_locations_coordinate[entry["SSID"]] = (x, y)
            self.control["configuration_file"] = True
            self.draw_aps()
        self.include_menu_ap = tk.Menu(self.menubar)
        self.menubar.add_cascade(label="Consider  selected APs when plotting", menu=self.include_menu_ap)
        for ap in self.ap_locations_coordinate:
            self.include_menu_ap_variables[ap] = tk.BooleanVar()
            self.include_menu_ap.add_checkbutton(label=ap, onvalue=1, offvalue=0,
                                                 variable=self.include_menu_ap_variables[ap])

    def draw_aps(self):
        self.ap_locations_rect_id.clear()
        for ap, coord in self.ap_locations_coordinate.items():
            x = coord[0]
            y = coord[1]
            ap_id = self.canvas.create_rectangle(x,y, (x + 10 ) , (y+ 10), fill="red")
            self.ap_locations_rect_id[ap] = ap_id
            self.canvas.create_text( x+ 5,y+ 15, text=ap)


    def import_data(self):
        self.control["configuration_file"] = True
        self.include_menu_exp = tk.Menu(self.menubar)
        self.menubar.add_cascade(label="Consider selected EXPs when plotting", menu=self.include_menu_exp)
        filenames = filedialog.askopenfilenames(filetypes=[("CSV files", "*.csv")])
        for filename in filenames:
            if filename:
                name_without_path_or_extension = os.path.splitext(os.path.basename(filename))[0]
                self.data[name_without_path_or_extension] = {}
                with open(filename, 'r') as file:
                    reader = csv.reader(file, skipinitialspace=True)
                    next(reader)  # skip the first line
                    for row in reader:
                        if(not ((row[10] in  self.data[name_without_path_or_extension]) )):
                            self.data[name_without_path_or_extension][row[10]] = []
                        self.data[name_without_path_or_extension][row[10]].append(float(row[4]))

                self.include_menu_exp_variables[name_without_path_or_extension] = tk.BooleanVar()
                self.include_menu_exp.add_checkbutton(label=f"{name_without_path_or_extension}", onvalue=1, offvalue=0, variable=self.include_menu_exp_variables[name_without_path_or_extension])

    def draw_mobile_location(self,x_coordinate,y_coordinate):
        self.canvas.delete("all")
        self.draw_aps()
        self.create_grid(10, 6)
        x = int(float(x_coordinate.replace(',','.')) * 100)
        y = int(float(y_coordinate.replace(',','.')) * 100)
        self.mobile_location_id_rect = self.canvas.create_rectangle(x, y, x + 10, y + 10, fill="blue")
        self.draw_distances()

if __name__ == "__main__":
    window = TeseWindow()
    window.mainloop()
