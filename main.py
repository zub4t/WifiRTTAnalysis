import json
import csv
import os
import tkinter as tk
from tkinter import filedialog
from functools import partial
import math
import threading
import time
import matplotlib.pyplot as plt
import numpy as np
import itertools
import random


class TeseWindow(tk.Tk):
    ap_locations_rect_id = {}
    ap_locations_coordinate = {}
    control = {}
    experience_options = []
    mobile_information = {}
    def __init__(self):
        super().__init__()
        self.title("WiFi RTT Analysis")
        self.geometry("1100x700")
        # Create a canvas
        self.canvas = tk.Canvas(self, width=1100, height=700)
        self.canvas.pack()
        self.create_grid(10,6)

        # Create a menu bar
        self.menubar = tk.Menu(self)
        self.config(menu=self.menubar)

        # Create a File menu with options to Exit and Save
        file_menu = tk.Menu(self.menubar)
        self.menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Import configuration file", command=self.import_json_configuration)
        file_menu.add_command(label="Import mobile location", command=self.import_json_mobile_location)
        file_menu.add_command(label="Import data", command=self.import_data)
        file_menu.add_command(label="Import data to visualize", command= threading.Thread(target=self.import_data_animated).start)

        file_menu.add_command(label="Exit", command=self.quit)

        # Create Analysis menu
        analysis_menu = tk.Menu(self.menubar)
        self.menubar.add_cascade(label="Analysis", menu=analysis_menu)
        analysis_menu.add_command(label="Plot", command=self.plot_scatter)


        # Control Variable

    def plot_scatter(self):
        fig, ax = plt.subplots()
        for exp in self.include_menu_exp_variables:
            for ap in self.include_menu_ap_variables:
                if(self.include_menu_ap_variables[ap].get()):

                    number_of_colors = 80
                    colors = itertools.cycle(["#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)])
                                              for i in range(number_of_colors)])
                    data_y = self.data[exp][ap]
                    exp_x = next(xx for xx in self.mobile_information if xx["name"] == exp)
                    rect1_x1, rect1_y1 = self.ap_locations_coordinate[ap]
                    rect1_x1 = rect1_x1 /100
                    rect1_y1 = rect1_y1 / 100
                    rect2_x1 = exp_x["xCoordinate"]
                    rect2_y1 = exp_x["yCoordinate"]

                    distance = math.sqrt((rect1_x1 - rect2_x1) ** 2 + (rect1_y1 - rect2_y1) ** 2)

                    data_x = [distance] * len(self.data[exp][ap])
                    if (len(data_x) > 0):
                        ax.scatter(data_x, data_y, s=20, color=next(colors) ,alpha=0.6)
                        ax.plot(data_x, range(0,len(data_y)), color="gray",alpha=0.2)
                        # Add an annotation to the bounding box
                        random_float = np.random.uniform(low=-1, high=1)
                        xmin = (data_x[0])
                        ymin = min(data_y)

                        plt.annotate(f'{ap}_{exp}',
                                     xy=(xmin, ymin), xycoords='data',
                                     xytext=(xmin + 1 + random_float, ymin - 1 + random_float), textcoords='data',
                                     arrowprops=dict(arrowstyle="->",
                                                     connectionstyle="arc3"))


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
        fig.savefig('ftm_responder_1.png')



    def create_grid(self,x_units,y_units):
        # Draw x-axis
        self.canvas.create_line(0, 0, 1000, 0, width=2)

        # Draw y-axis
        self.canvas.create_line(0, 0, 0, 600, width=2)

        # Display unit steps on x-axis
        for i in range(1, 11):
            self.canvas.create_text(i*100, 22, text=str(i))

        # Display unit steps on y-axis
        for i in range(1, 7):
            self.canvas.create_text(22, i*100, text=str(i))

    def __draw_distances(self):

        if (hasattr(self, "mobile_location") and hasattr(self,"ap_locations_rect_id")):
            rect2_x1, rect2_y1, rect2_x2, rect2_y2 = self.canvas.coords(self.mobile_location)
            for ap in self.ap_locations_rect_id:
                # Extract the x1, y1, x2, y2 coordinates of the two rectangles
                rect1_x1, rect1_y1, rect1_x2, rect1_y2 = self.canvas.coords( self.ap_locations_rect_id[ap])
                # Draw the line between the two rectangles
                line = self.canvas.create_line(rect1_x1, rect1_y1, rect2_x1, rect2_y1, width=1, fill="gray")
                # Calculate the distance between the two rectangles
                distance = math.sqrt((rect1_x1 - rect2_x1) ** 2 + (rect1_y1 - rect2_y1) ** 2) /100
                # Find the midpoint of the line
                x = (rect2_x1 + rect1_x1) / 2
                y = (rect2_y1 + rect1_y1) / 2

                # Create a text label for the distance

                text = self.canvas.create_text(x, y, text=f"{distance: .2f}", font=("Arial", 10),fill="red")

    def import_json_mobile_location(self):

        filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filename:
            with open(filename, "r") as f:
                data = json.load(f)
                self.mobile_information = data
                self.create_experience_menu(data)
                self.control["mobile_location_file"] = True

    def create_experience_menu(self, data):
        for item in data:
            self.experience_options.append(item["name"])
        experience_menu = tk.Menu(self.menubar)
        self.menubar.add_cascade(label="Experience", menu=experience_menu)

        for item in self.experience_options:
            exp_x = next(xx for xx in data if xx["name"] == item)
            x_coordinate = exp_x["xCoordinate"]
            y_coordinate = exp_x["yCoordinate"]
            experience_menu.add_command(label=item,
                                        command=partial(self.__draw_mobile_location, x_coordinate, y_coordinate))

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
            self.__draw_aps()
        self.include_menu_ap = tk.Menu(self.menubar)
        self.include_menu_ap_variables = {}
        self.menubar.add_cascade(label="Include", menu=self.include_menu_ap)
        for ap in self.ap_locations_coordinate:
            self.include_menu_ap_variables[ap] = tk.BooleanVar()
            self.include_menu_ap.add_checkbutton(label=ap, onvalue=1, offvalue=0,
                                                 variable=self.include_menu_ap_variables[ap])

    def __draw_aps(self):
        self.ap_locations_rect_id.clear()
        for ap, coord in self.ap_locations_coordinate.items():
            x = coord[0]
            y = coord[1]
            ap_id = self.canvas.create_rectangle(x,y, (x + 10 ) , (y+ 10), fill="red")
            self.ap_locations_rect_id[ap] = ap_id
            self.canvas.create_text( x+ 5,y+ 15, text=ap)

    def __draw_mobile_location(self, x_coordinate, y_coordinate):
        self.canvas.delete("all")
        self.__draw_aps()
        self.create_grid(10, 6)
        coord = (x_coordinate * 100, y_coordinate * 100)
        self.mobile_location = self.canvas.create_rectangle(*coord, *(coord + (10, 10)), fill="blue")
        self.__draw_distances()

    def import_data(self):
        self.control["configuration_file"] = True
        self.data = {}
        self.include_menu_exp = tk.Menu(self.menubar)
        self.include_menu_exp_variables = {}
        self.menubar.add_cascade(label="Include EXP", menu=self.include_menu_exp)

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

    def __draw_mobile_location(self,x_coordinate,y_coordinate):
        self.canvas.delete("all")
        self.__draw_aps()
        self.create_grid(10, 6)
        x = int(float(x_coordinate * 100))
        y = int(float(y_coordinate * 100))
        self.mobile_location = self.canvas.create_rectangle(x, y, x + 10, y + 10, fill="blue")
        self.__draw_distances()
    def import_data_animated(self):
        ap_locations_animation_text = {}
        for ap in self.ap_locations_coordinate:
            x = self.ap_locations_coordinate[ap][0]
            y = self.ap_locations_coordinate[ap][1]
            text = self.canvas.create_text(x, y + 30, text=f"", font=("Arial", 14), fill="purple")
            ap_locations_animation_text[ap] = text

        filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if filename:
            with open(filename, 'r') as file:
                reader = csv.reader(file, skipinitialspace=True)
                next(reader)  # skip the first line
                c = 0
                for row in reader:
                    c+=1
                    text_x, text_y = self.canvas.coords(ap_locations_animation_text[row[10]])
                    self.canvas.delete(ap_locations_animation_text[row[10]])
                    text = self.canvas.create_text(text_x, text_y , text=f"{float(row[4]): .2f}", font=("Arial", 10), fill="purple")
                    ap_locations_animation_text[row[10]] = text
                    if(c% len(self.ap_locations_coordinate) == 0):
                        time.sleep(0.3)

if __name__ == "__main__":
    window = TeseWindow()
    window.mainloop()
