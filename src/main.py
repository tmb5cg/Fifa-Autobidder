import configparser
import os
import os.path
import platform
import queue
import threading
import time
import tkinter as tk
from importlib import import_module, reload
from os import path
from tkinter import *
from tkinter import ttk
from tkinter.ttk import Treeview

import autobidder
from autobidder import *
from autobidder import AutobidderTest
from helpers import *

LARGE_FONT= ("Verdana", 12)
SMALL_FONT = ("Verdana", 8)
NORM_FONT = ("Helvetica", 10)
HEADER_FONT = ("Helvetica", 12, "bold")

class GUI(tk.Tk):

    def __init__(self, *args, **kwargs):

        tk.Tk.__init__(self, *args, **kwargs)

        self.container = tk.Frame(self, bg="grey")

        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.parentQueue = queue.Queue()

        self.bidRoundTable = BidRoundTable(self.container, self)
        self.logsTable = LogsTable(self.container, self)
        self.userOptionsMenu = UserOptions(self.container, self)
        self.buttons = Buttons(self.container, self)
        self.userStatistics = UserStatistics(self.container, self)

        self.bidRoundTable.grid(row=0, column=0, sticky="nsew", padx="5", pady="5")
        self.logsTable.grid(row=1, column=0, sticky="nsew", padx="5", pady="5")
        self.userOptionsMenu.grid(row=0, column=1, sticky="nsew", padx="5", pady="5")
        self.userStatistics.grid(row=1, column=1, sticky="nsew", padx="5", pady="5")
        self.buttons.grid(row=2, column=1, sticky="nsew", padx="5", pady="5")


class UserStatistics(tk.Frame):

    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller

        tk.Frame.__init__(self, parent)

        # Create frame for autobidder and autobuyer within mainbots frame
        self.autobidderStatsFrame = tk.LabelFrame(self, text="Statistics")
        self.autobidderStatsFrame.grid(row=0, column=0)

        self.config = configparser.ConfigParser()
        self.config.read("./data/config.ini")

        statistics_list = self.config.options("Statistics")
        self.num_statistics = 0
        self.STATISTICS_LABELS = []

        for statistic_name in statistics_list:
            self.num_statistics += 1

            # Create left side label for the statistic
            stat_label = tk.Label(self.autobidderStatsFrame, text=statistic_name, font=NORM_FONT)
            stat_label.grid(row=self.num_statistics, column=0)

            # Get stats current value, and assign to stringvar
            stat_value = str(self.config.get("Statistics", statistic_name))
            stat_value_stringVar = tk.StringVar()
            stat_value_stringVar.set(stat_value)

            # Create label that tracks the stringvar, which we will pass to a list that function will update
            value_label = tk.Label(self.autobidderStatsFrame, textvariable=stat_value_stringVar, font=NORM_FONT)
            value_label.grid(row=self.num_statistics, column=1)

            self.STATISTICS_LABELS.append(stat_value_stringVar)

        self.update_statistics()
        

    def update_statistics(self):
        try:
            count = 0
            self.config.read("./data/config.ini")
            statistics_list = self.config.options("Statistics")
            for stat in statistics_list:
                curval = self.config.get("Statistics", stat)
                stat_label_string_var = self.STATISTICS_LABELS[count]
                stat_label_string_var.set(curval)
                count+=1

            self.after(2000, self.update_statistics)
        except:
            print("error in the new method lmao")

class Buttons(tk.Frame):

    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller

        tk.Frame.__init__(self, parent)

        self.loginButton = tk.Button(self, text='Login', width=12, command=self.login)
        self.startAutobidderButton = tk.Button(self, text='RUN BOT', width=12, command=self.startAutobidder)

        self.loginButton.grid(row=0, column=0, pady=10, columnspan=2)
        self.startAutobidderButton.grid(row=1, column=0, pady=10, columnspan=2)


        log_event(self.controller.parentQueue, " - - - - Bot started - - - - ")
        self.driver = create_driver()
        self.action = ActionChains(self.driver)

        self.config = configparser.ConfigParser()
        self.config.read("./data/config.ini")
        url = str(self.config.get("Other", "webapp_url"))
        # https://www.ea.com/fifa/ultimate-team/web-app/
        self.driver.get(url)

    def login(self):
        log_event(self.controller.parentQueue, "Auto logging in...")

        self.loginButton.config(state="disabled")
        self.master.configure(bg="green")

        self.thread = ThreadedClient(self.controller.parentQueue, "login", self.driver, self.controller.userOptionsMenu.GUI_OPTIONS)
        self.thread.start()
        self.periodiccall()
    
    def startAutobidder(self):
        log_event(self.controller.parentQueue, "Autobidder started")

        self.startAutobidderButton.config(state="disabled")
        self.startAutobidderButton.config(text = "RUNNING")
        self.master.configure(bg="green")

        self.thread = ThreadedClient(self.controller.parentQueue, "autobidder", self.driver, self.controller.userOptionsMenu.GUI_OPTIONS)
        self.thread.start()
        self.periodiccall()
    
    def periodiccall(self):
        self.checkqueue()
        if self.thread.is_alive():
            self.after(100, self.periodiccall)
        else:
            self.loginButton.config(state="active")
            self.startAutobidderButton.config(state="active")
            self.master.configure(bg="grey")

    def checkqueue(self):
        while self.controller.parentQueue.qsize():
            try:
                msg = self.controller.parentQueue.get(0)
                msg_body = str(msg[0])
                msg_type = str(msg[1])  # default is blank "", unless it is bidround over log

                if msg_type == "bidround":
                    # send it to logs table
                    line_split_into_string = msg_body.strip("\n").split(",")
    
                    self.controller.bidRoundTable.bidroundtable_object.insert('', 'end', values=line_split_into_string)
                    self.controller.bidRoundTable.bidroundtable_object.yview_moveto(1)

                else:
                    self.write_logs_tofile(msg_body)

            except queue.Empty:
                pass

    def write_logs_tofile(self, event):
        file_object = open('./data/gui_logs.txt', 'a', encoding="utf8")
        now = datetime.now()
        dt_string = now.strftime("[%I:%M:%S %p] ")
        full_log_print = str(dt_string + event)

        # for some reason need to put it into array
        table_msg = [full_log_print]
        self.controller.logsTable.logstable_object.insert('', 'end', values=table_msg)
        self.controller.logsTable.logstable_object.yview_moveto(1)

        full_log = dt_string + event + "\n"
        print(full_log_print)
        file_object.write(full_log)
        file_object.close()

        # self.controller.logsTable.logstable_object.yview_moveto(1)

class UserOptions(tk.Frame):

    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller

        tk.Frame.__init__(self, parent)

        # Create frame for autobidder and autobuyer within mainbots frame
        self.autobidderFrame = tk.LabelFrame(self, text="Settings")
        self.autobidderFrame.grid(row=0, column=0)

        self.config = configparser.ConfigParser()
        self.config.read("./data/config.ini")
        sections = self.config.sections()
        # print(sections)

        options = self.config.options("Settings")
        self.num_user_options = 0
        self.GUI_OPTIONS = [] 
        for useroption in options:
            self.num_user_options+=1
            value = self.config.get("Settings", useroption)

            labeltext = str(useroption) + ": "
            labeltext = labeltext.lower()

            label = tk.Label(self.autobidderFrame, text=labeltext, font=NORM_FONT)
            label.grid(row=self.num_user_options, column=0)
            
            sleep_time = [0, 1, 2, 3, 5, 8, 10]
            num_cycles = [1, 2, 3, 4, 5, 6]
            expiration_cutoff_mins = [2, 3, 4, 5, 6, 7, 10]
            margin = [100, 150, 200, 250, 300, 350, 400, 450]
            undercut_market_on_list = [0, 1]
            undercut_market_on_relist = [1, 0, 2]
            futbin_max_price = [800, 1000, 1200]
            platform = ["Xbox", "Playstation", "PC"]

            SPEEDCHOICE = []
            if useroption.lower() == "sleep_time":
                SPEEDCHOICE = sleep_time
            if useroption.lower() == "num_cycles":
                SPEEDCHOICE = num_cycles
            if useroption.lower() == "expiration_cutoff_mins":
                SPEEDCHOICE = expiration_cutoff_mins
            if useroption.lower() == "margin":
                SPEEDCHOICE = margin
            if useroption.lower() == "undercut_market_on_list":
                SPEEDCHOICE = undercut_market_on_list
            if useroption.lower() == "undercut_market_on_relist":
                SPEEDCHOICE = undercut_market_on_relist
            if useroption.lower() == "futbin_max_price":
                SPEEDCHOICE = futbin_max_price
            if useroption.lower() == "platform":
                SPEEDCHOICE = platform 

            useroption_lowered = useroption.lower()
            # autobidder_speed_option = tk.StringVar()
            autobidder_speed_option = tk.StringVar(name=useroption_lowered)
            autobidder_speed_option.set(SPEEDCHOICE[0])
            autobidder_speed_dropdown = OptionMenu(self.autobidderFrame, autobidder_speed_option, *SPEEDCHOICE)
            autobidder_speed_dropdown.grid(row = self.num_user_options, column = 1)
            self.GUI_OPTIONS.append(autobidder_speed_option)

        self.update_settings()
        # self.saveConfig()

    # Continuously update user settings
    def update_settings(self):
        try:
            self.config.read("./data/config.ini")
            count = 0
            options = self.config.options("Settings")
            for option in self.GUI_OPTIONS:
                option_name = options[count]

                # Get DISPLAYED value pulled from Dropdown memory object
                choice = option.get()

                # WRITE displayed value in writing to config.ini
                self.config.set("Settings", option_name, str(choice))

                # self.config.write(open("./data/config.ini", "w"))
                with open('./data/config.ini', 'w') as configfile:
                    self.config.write(configfile)
                
                count+=1
            # every 1 second update labels
            self.after(3000, self.update_settings)
        except:
            print("Error in updating settings")

class BidRoundTable(tk.Frame):

    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller

        tk.Frame.__init__(self, parent)

        self.title = tk.Label(self, text="Cycles", font=LARGE_FONT)

        # Player list table
        columns = ["Time", "Elapsed", "ID", "Won", "Lost", "Bids", "Requests", "Margin", "Sold", "Relisted", "Profit", "PPF"]
        self.bidroundtable_object = Treeview(self, columns=columns, show="headings", height=8)

        for col in columns:
            colwidth = 70
            self.bidroundtable_object.column(col, width=colwidth)
            self.bidroundtable_object.heading(col, text=col)

        # LOAD IN TABLE
        txt = open("./data/bid_rounds.txt", "r", encoding="utf8")
        for aline in txt:
            line = aline.strip("\n").split(",")
            condensed_row_to_insert = []
            for x in line:
                condensed_row_to_insert.append(x)
            self.bidroundtable_object.insert('', 'end', values=condensed_row_to_insert)
        txt.close()

        self.title.grid(row = 0, column = 0)
        self.bidroundtable_object.grid(row=1,column=0)

class LogsTable(tk.Frame):

    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller

        tk.Frame.__init__(self, parent)

        self.title = tk.Label(self, text="Logs", font=LARGE_FONT)

        # Player list table
        columns = ['log']
        self.logstable_object = Treeview(self, columns=columns, show="headings")
        self.logstable_object.column("log", width=800)

        # NOT GOING TO LOAD IN TABLE that way logs are preserved by each round - but always backed up to logs.txt

        self.title.grid(row=0, column=0)
        self.logstable_object.grid(row=1, column=0)

class ThreadedClient(threading.Thread):

    def __init__(self, queue, action, driver, GUI_OPTIONS):
        threading.Thread.__init__(self)
        self.queue = queue
        self.action = action
        self.driver = driver

        self.GUI_OPTIONS = GUI_OPTIONS

    def run(self):
        if (self.action == "autobidder"):
            importlib.reload(autobidder)
            from autobidder import AutobidderTest

            ab_test = AutobidderTest(self.driver, self.queue, self.GUI_OPTIONS)
            ab_test.test()
      
        if (self.action == "login"):
            time.sleep(5)
            
            self.config = configparser.ConfigParser()
            self.config.read("./data/config.ini")

            
            USER = {
                "email": self.config.get("Logins", "ea_email"),
                "password": self.config.get("Logins", "ea_password"),
            }

            EMAIL_CREDENTIALS = {
                "email": self.config.get("Logins", "email"),
                "password": self.config.get("Logins", "password"),
            }

            login(self.queue, self.driver, USER, EMAIL_CREDENTIALS)


if __name__ == '__main__':
    checkStartupFiles()
    clearGUIstats()
    app = GUI()
    app.title("TMB's FIFA 22 Autobidder")
    app.mainloop()
