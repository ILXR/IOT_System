import matplotlib.pyplot as plt
from scipy import signal
import numpy as np
import json
import glob
import os

CHANNELS = 5
COLORS = ["red", "orange", "hotpink", "green", "c", "blue", "purple", "black"]

def get_data(file_path):
    with open(file_path, "r") as f:
        all_lines = f.readlines()
        length = len(all_lines)
        all_data = []
        for i in range(CHANNELS):
            all_data.append([])
        for line in all_lines:
            val = line.split(",")
            for i in range(CHANNELS):
                all_data[i].append(float(val[i]))
        all_data = np.array(all_data)
        print(all_data)
    return all_data

def show_data(all_data,title):
    plt.figure()
    plt.xlabel("time")
    plt.ylabel("capacity")
    plt.suptitle(title)
    for i in range(CHANNELS):
        plt.plot(all_data[i, :], color=COLORS[i],
                 label="Channel-{}".format(i+1))
    plt.legend(loc='best')

def display():
    file = "./data"
    all_data = get_data(file)
    show_data(all_data, file)

display()
plt.show()