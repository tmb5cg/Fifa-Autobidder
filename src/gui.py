from cProfile import label
from datetime import datetime
import importlib
from posixpath import split
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk

import configparser
from turtle import color

from helpers import checkStartupFiles, create_driver, getFilters, log_event, setup_adblock, login, clearGUIstats, checkStartupFiles

import autobidder
from autobidder import *
from autobidder import Autobidder


NORM_FONT = ("Helvetica", 10)

class GUI(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self)

        # Make the app responsive
        for index in [0, 1, 2]:
            self.columnconfigure(index=index, weight=1)
            self.rowconfigure(index=index, weight=1)

        # Create message queue
        self.parentQueue = queue.Queue()
        
        # Create value lists
        self.sleep_time_list = [0, 1, 2, 3, 5, 8, 10]
        self.num_cycles_list = [1, 2, 3, 4, 5, 6]
        self.expiration_cutoff_mins_list = [2, 3, 4, 5, 6, 7, 10]
        self.margin_list = [100, 150, 200, 250, 300, 350, 400, 450]
        self.undercut_market_on_list_list = [0, 1]
        self.undercut_market_on_relist_list = [1, 0, 2]
        self.futbin_max_price_list = [800, 1000, 1200]
        self.platform_list = ["Xbox", "Playstation", "PC"]

        # Read initial config state on start, load into variables
        self.config = configparser.ConfigParser(allow_no_value=True)
        self.config.read("./data/settings.ini")

        # Create variables for email password and futbin URL
        self.emailVar = tk.StringVar(name="email")
        self.emailVar.set(str(self.config.get("Logins", "email")))

        self.passwordVar = tk.StringVar(name="password")
        self.passwordVar.set(str(self.config.get("Logins", "password")))

        self.futbinURLVar = tk.StringVar(name="futbinURL")
        self.futbinURLVar.set(str(self.config.get("Other", "futbin_url")))

        self.autoInputVar = tk.IntVar(name="autoinputVar")
        self.autoInputVar.set(int(self.config.get("Other", "autoinput")))

        # Create variables for bot statistics
        stats_options = self.config.options("Statistics")
        self.GUI_STATS_VARS = []
        for useroption in stats_options:
            var = tk.StringVar(name=str(useroption))
            value = self.config.get("Statistics", useroption)
            var.set(str(value))
            self.GUI_STATS_VARS.append(var)

        # Create variables for bot settings
        stats_options = self.config.options("Settings")
        self.GUI_SETTINGS_VARS = []
        for useroption in stats_options:
            # Create var
            var = tk.StringVar(name=useroption)
            value = self.config.get("Settings", useroption)
            var.set(str(value))        
            self.GUI_SETTINGS_VARS.append(var)

        # Create variables for bot filters
        options = self.config.options("Other")
        webapp_options = ['quality', 'rarity', 'league', 'club', 'country', 'position']
        self.GUI_URL_VARS = []
        for useroption in options:
            if useroption in webapp_options:
                value = self.config.get("Other", useroption)
                labeltext = str(useroption) + ": "
                labeltext = labeltext.lower()

                var = tk.StringVar(name=str(useroption))
                var.set(str(value))

                self.GUI_URL_VARS.append(var)

        # Create widgets :)
        self.setup_widgets()
        clearGUIstats()
        checkStartupFiles()
        self.update_settings()
        self.initialize_driver()

    def setup_widgets(self):
        # - - - - - - - STATISTICS  - - - - - - - 
        # Create a Frame
        self.statistics_frame = ttk.LabelFrame(self, text="Statistics", padding=(5, 10))
        self.statistics_frame.grid( row=0, column=0, padx=(20, 10), pady=(20, 10), sticky="nsew")

        # Assign vars
        self.NUM_STATISTICS = 0
        for stat in self.GUI_STATS_VARS:
            self.NUM_STATISTICS += 1

            label_name = str(stat) + ": "
            splitted = label_name.replace("_", " ").split(" ")
            label_name = str(splitted[0].capitalize()) + " " + str(splitted[1].capitalize())

            # Create left side label for the statistic using stringvars name
            stat_label = ttk.Label(self.statistics_frame, text=label_name, font=NORM_FONT)
            stat_label.grid(row=self.NUM_STATISTICS, column=0, padx=5, pady=3, sticky="nsew")

            # Create label that tracks the stringvar, which we will pass to a list that function will update
            value_label = ttk.Label(self.statistics_frame, textvariable=stat, font=NORM_FONT)
            value_label.grid(row=self.NUM_STATISTICS, column=1, padx=5, pady=3, sticky="nsew")

        #  - - - - - - -  SETTINGS - - - - - - - 
        # Create a Frame
        self.settings_frame = ttk.LabelFrame(self, text="Settings", padding=(20, 10))
        self.settings_frame.grid(row=0, column=1, padx=(20, 10), pady=(20, 10), sticky="nsew")

        # Assign vars
        self.NUM_SETTINGS = 0
        for stat in self.GUI_SETTINGS_VARS:
            self.NUM_SETTINGS += 1

            label_name = str(stat) + ": "
            splitted = label_name.replace("_", " ").split(" ")
            final_label = ''
            for word in splitted:
                if word != "market":
                    final_label += (str(word.capitalize()) + " ")

            # Create left side label for the statistic using stringvars name
            stat_label = ttk.Label(self.settings_frame, text=final_label, font=NORM_FONT)
            stat_label.grid(row=self.NUM_SETTINGS, column=0, padx=5, pady=3, sticky="nsew")

            self.DROPDOWN = []
            if str(stat) == "sleep_time": self.DROPDOWN = self.sleep_time_list
            if str(stat) == "num_cycles": self.DROPDOWN = self.num_cycles_list
            if str(stat) == "expiration_cutoff_mins": self.DROPDOWN = self.expiration_cutoff_mins_list
            if str(stat) == "margin": self.DROPDOWN = self.margin_list
            if str(stat) == "undercut_market_on_list": self.DROPDOWN = self.undercut_market_on_list_list
            if str(stat) == "undercut_market_on_relist": self.DROPDOWN = self.undercut_market_on_relist_list
            if str(stat) == "futbin_max_price": self.DROPDOWN = self.futbin_max_price_list
            if str(stat) == "platform": self.DROPDOWN = self.platform_list 

            # Create right side option menu, assign stringvar
            optionmenu = ttk.OptionMenu(self.settings_frame, stat, str(self.config["Settings"][str(stat)]), *self.DROPDOWN)
            optionmenu.grid(row=self.NUM_SETTINGS, column=1, padx=5, pady=3, sticky="nsew")


        # - - - - - - - FUTBIN URL  - - - - - - - 
        # Create a Frame
        self.filters_frame_top = ttk.LabelFrame(self, text="Filters Holder", padding=(20, 10))
        self.filters_frame_top.grid( row=0, column=2, padx=(20, 10), pady=(20, 10), sticky="nsew")

        self.filters_frame = ttk.LabelFrame(self.filters_frame_top, text="Current Filters:", padding=(20, 10))
        self.filters_frame.grid( row=0, column=0, padx=(10, 5), pady=(6, 1), sticky="nsew")

        # Entry
        self.entry = ttk.Entry(self.filters_frame_top, textvariable=self.futbinURLVar)
        self.entry.grid(row=1, column=0, padx=5, pady=(10, 10), sticky="ew")

        # Auto enter filters input
        self.autoinput = ttk.Checkbutton(self.filters_frame_top, text="Auto enter filters (beta)", style="Switch.TCheckbutton", variable=self.autoInputVar, onvalue=1, offvalue=0)
        self.autoinput.grid(row=2, column=0, padx=5, pady=10, sticky="nsew")

        # Assign vars
        self.NUM_FILTERS = 0
        for filter in self.GUI_URL_VARS:
            self.NUM_FILTERS += 1

            label_name = str(filter) + ": "
            splitted = label_name.replace("_", " ").split(" ")
            label_name = str(splitted[0].capitalize()) + " " + str(splitted[1].capitalize())

            # Create left side label for the filter using stringvars name
            filter_label = ttk.Label(self.filters_frame, text=label_name, font=NORM_FONT)
            filter_label.grid(row=self.NUM_FILTERS, column=0, padx=5, pady=3, sticky="nsew")

            # Create label that tracks the stringvar, which we will pass to a list that function will update
            value_label = ttk.Label(self.filters_frame, textvariable=filter, font=NORM_FONT)
            value_label.grid(row=self.NUM_FILTERS, column=1, padx=5, pady=3, sticky="nsew")


        #  - - - - - - -  START BOT BUTTONS - - - - - - - 
        # Create a Frame
        self.buttons_frame = ttk.LabelFrame(self, text="Buttons", padding=(20, 10))
        self.buttons_frame.grid(row=0, column=3, padx=(20, 10), pady=(20, 10), sticky="nsew")

        # Button Login
        self.loginButton = ttk.Button(self.buttons_frame, text="Login", command=self.login)
        self.loginButton.grid(row=0, column=0, columnspan=2, padx=5, pady=10, sticky="nsew")

        # Button Start bot
        self.startButton = ttk.Button(self.buttons_frame, text="Start Bot", command=self.startBot)
        self.startButton.grid(row=1, column=0, columnspan=2, padx=5, pady=10, sticky="nsew")

        # Button Discord
        self.button = ttk.Button(self.buttons_frame, text="Join Discord")
        self.button.grid(row=2, column=0, padx=5, columnspan=2, pady=10, sticky="nsew")

        # Button Help
        self.button = ttk.Button(self.buttons_frame, text="Help")
        self.button.grid(row=3, column=0, columnspan=2, padx=5, pady=10, sticky="nsew")

        # Entry email
        self.emailEntryLabel = ttk.Label(self.buttons_frame, text="Email: ", font=NORM_FONT)
        self.emailEntryLabel.grid(row=4, column=0, padx=5, pady=3, sticky="nsew")     

        self.emailEntry = ttk.Entry(self.buttons_frame, textvariable=self.emailVar)
        self.emailEntry.grid(row=4, column=1, padx=5, pady=(10, 10), sticky="ew")

        # Entry password
        self.passwordEntryLabel = ttk.Label(self.buttons_frame, text="Password: ", font=NORM_FONT)
        self.passwordEntryLabel.grid(row=5, column=0, padx=5, pady=3, sticky="nsew")  

        self.passwordEntry = ttk.Entry(self.buttons_frame, textvariable=self.passwordVar, show="*")
        self.passwordEntry.grid(row=5, column=1, padx=5, pady=(10, 10), sticky="ew")

        #  - - - - - - -  BID ROUNDS TABLE - - - - - - - 
        # Create a Frame
        self.logs_frame = ttk.LabelFrame(self, text="Logs", padding=(20, 10))
        self.logs_frame.grid(row=1, column=0, columnspan=4, padx=(20, 10), pady=10, sticky="nsew")

        columns = ["Time", "Elapsed", "ID", "Won", "Lost", "Bids", "Requests", "Margin", "Sold", "Relisted", "Profit", "PPF"]  
        self.bidrounds_table = ttk.Treeview(self.logs_frame, columns=columns, show="headings", height=3)

        for col in columns:
            colwidth = 70
            self.bidrounds_table.column(col, width=colwidth)
            self.bidrounds_table.heading(col, text=col)

        # LOAD IN TABLE
        txt = open("./data/bid_rounds.txt", "r", encoding="utf8")
        for aline in txt:
            line = aline.strip("\n").split(",")
            condensed_row_to_insert = []
            for x in line:
                condensed_row_to_insert.append(x)
            self.bidrounds_table.insert('', 'end', values=condensed_row_to_insert)
        txt.close()

        self.bidrounds_table.grid(row=1,column=0, pady=5)


        #  - - - - - - -  LOGS TABLE - - - - - - - 
        columns = ["Live Logs"]  
        self.logs_table = ttk.Treeview(self.logs_frame, columns=columns, show="headings", height=3)

        for col in columns:
            colwidth = 840
            self.logs_table.column(col, width=colwidth)
            self.logs_table.heading(col, text=col)

        self.logs_table.grid(row=2, column=0)

    def initialize_driver(self):
        log_event(self.parentQueue, " - - - - Bot started - - - - ")
        self.driver = create_driver()
        setup_adblock(self.driver)
        

    # Continuously update user settings
    def update_settings(self):
        try:
            self.checkqueue()
        except:
            print("Error checking queue")

        try:
            self.config.read("./data/settings.ini")

            for option in self.GUI_STATS_VARS:
                # GET current stat value in config.ini
                stat_value = self.config.get("Statistics", str(option))

                # SET updated value to stringVar
                option.set(str(stat_value))

            for option in self.GUI_SETTINGS_VARS:
                # Get DISPLAYED value pulled from Dropdown memory object
                choice = option.get()

                # WRITE displayed value in writing to config.ini
                self.config.set("Settings", str(option), str(choice))

            # Update email, pwd, Futbin URL
            pwd_on_gui = self.passwordVar.get()
            email_on_gui = self.emailVar.get()

            self.config.set("Logins", "email", str(email_on_gui))
            self.config.set("Logins", "password", str(pwd_on_gui))

            # Check if URL has changed
            url_on_gui = str(self.futbinURLVar.get())
            url_on_disk = str(self.config.get("Other", "futbin_url"))

            if (url_on_gui != url_on_disk):
                # Run futbin function
                filters = getFilters(url_on_gui)

                for f in self.GUI_URL_VARS:
                    f.set("")
                    f_name = str(f)
                    self.config.set("Other", f_name, "")

                    if f_name in filters:
                        self.config.set("Other", f_name, str(filters[f_name]))
                        f.set(str(filters[f_name]))

                log_event(self.parentQueue, "Successfully updated Futbin filters")

            self.config.set("Other", "futbin_url", str(url_on_gui))
            self.config.set("Other", "autoinput", str(self.autoInputVar.get()))

            with open("./data/settings.ini", 'w') as configfile:
                self.config.write(configfile)

            # every 1 second update labels
            self.after(3000, self.update_settings)
        except:
            print("Error updating GUI, restart")

    def checkqueue(self):
        while self.parentQueue.qsize():
            try:
                msg = self.parentQueue.get(0)

                if (msg[1] == True):
                    # Send to table
                    msg = msg[0]
                    line_split_into_string = msg.strip("\n").split(",")
    
                    self.bidrounds_table.insert('', 'end', values=line_split_into_string)
                    self.bidrounds_table.yview_moveto(1)
                    hs = open("./data/bid_rounds.txt", "a", encoding="utf8")
                    hs.write(msg + "\n")
                    hs.close()
                else:
                    self.write_logs_tofile(msg[0])

            except queue.Empty:
                pass

    def write_logs_tofile(self, event):
        file_object = open('./data/output.txt', 'a', encoding="utf8")
        currentTime = datetime.now()
        dt_string = currentTime.strftime("[%I:%M:%S %p] ")
        full_log_print = str(dt_string + event + "\n")
        print(str(dt_string + event))

        msg_for_table = [event]
        self.logs_table.insert('', 'end', values=msg_for_table)
        self.logs_table.yview_moveto(1)
        
        file_object.write(full_log_print)
        file_object.close()

    def periodiccall(self):
        if self.thread.is_alive():
            self.after(100, self.periodiccall)
        else:
            self.loginButton.config(state="active")
            self.startButton.config(state="active")
            self.startButton.config(style="", text="Start bot")
            # self.master.configure(bg="grey")
        
    def login(self):
        log_event(self.parentQueue, "Logging in...")
        self.loginButton.config(state="disabled")

        self.thread = ThreadedClient(self.parentQueue, "login", self.driver)
        self.thread.start()
        self.periodiccall()

    def startBot(self):
        log_event(self.parentQueue, "Autobidder started")
        self.startButton.config(state="disabled", style="Accent.TButton", text="RUNNING")

        self.thread = ThreadedClient(self.parentQueue, "autobidder", self.driver)
        self.thread.start()
        self.periodiccall()

class ThreadedClient(threading.Thread):

    def __init__(self, queue, action, driver):
        threading.Thread.__init__(self)
        self.queue = queue
        self.action = action
        self.driver = driver

    def run(self):
        if (self.action == "autobidder"):
            importlib.reload(autobidder)
            from autobidder import Autobidder

            autobidder_obj = Autobidder(self.driver, self.queue)
            autobidder_obj.run()
      
        if (self.action == "login"):
            time.sleep(5)
            
            self.config = configparser.ConfigParser()
            self.config.read("./data/settings.ini")

            USER = {
                "email": self.config.get("Logins", "email"),
                "password": self.config.get("Logins", "password"),
            }

            login(self.queue, self.driver, USER)