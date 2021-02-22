import thread_runner
# import function_runner
import mainhelpers
import helpers
import newhelpers
# import autobidder_any
import autobidder
import autobuyer
# import autobidder_list

from config import create_driver, URL
from thread_runner import RunThread
# from function_runner import RunFunction
from helpers import *
from mainhelpers import *
from newhelpers import *

from selenium.webdriver.common.action_chains import ActionChains

from importlib import reload
import importlib
import queue

from tkinter import *
import tkinter as tk
from tkinter.ttk import Treeview
from tkinter import ttk

import os.path
from os import path
import json

LARGE_FONT= ("Verdana", 12)
SMALL_FONT = ("Verdana", 8)
NORM_FONT = ("Helvetica", 10)
HEADER_FONT = ("Helvetica", 12, "bold")


class GUI(tk.Tk):

    def __init__(self, *args, **kwargs):

        tk.Tk.__init__(self, *args, **kwargs)
        self.container = tk.Frame(self)

        self.container.pack(side="top", fill="both", expand=True)

        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # self.logins = Logins(self.container, self)
        self.playerfilters = PlayerFilters(self.container, self)
        self.table = Table(self.container, self)
        self.mainbuttons = MainButtons(self.container, self)
        self.displaylogs = DisplayLogs(self.container, self)

        # self.logins.grid(row=1, column=0, sticky="nsew", padx="10", pady="10")

        # TOP LEFT Add players box
        self.playerfilters.grid(row=0, column=0, sticky="nsew", padx="10", pady="10")

        # TOP RIGHT Player targets table
        self.table.grid(row=0, column=1, sticky="nsew", padx="10", pady="10")

        # BOTTOM LEFT Login / start bot / etc buttons
        self.mainbuttons.grid(row=1, column=0, sticky="nsew", padx="10", pady="10")

        # BOTTOM RIGHT Log displayer
        self.displaylogs.grid(row=1, column=1, sticky="nsew", padx="10", pady="10")

# Top left 
class PlayerFilters(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        self.parent = parent
        self.controller = controller
        self.playerlist = []

        app_title = tk.Label(self, text=' FIFA 21 Autobidder + Autobuyer ', font=HEADER_FONT)
        app_title.grid(row=1, column=0, columnspan=2, pady=15)

        futbinlink_label = tk.Label(self, text='Player Futbin URL: ', font=NORM_FONT)
        futbinlink_text = tk.StringVar()
        futbin_entry = tk.Entry(self, textvariable=futbinlink_text)

        futbinlink_label.grid(row=2, column=0)
        futbin_entry.grid(row=2, column=1)

        
        self.add_btn_futbin = tk.Button(self, text='Add Player', width=12, command=self.add_player_futbin)
        self.add_btn_futbin.grid(row=3, column=0, pady=10)

        self.remove_btn = tk.Button(self, text='Remove Player', width=12, command=self.remove_player)
        self.remove_btn.grid(row=3, column=1, pady=10)


        disclaimer2 = tk.StringVar()
        disclaimer_text2 = tk.Label(self, text='Futbin price will be used as truth in initial searches, during which market data will be collected to find real-time market price', font=SMALL_FONT, wraplength=400)
        disclaimer_text2.grid(row=4, column=0, columnspan=2)

        self.futbinlink_text = futbinlink_text

        self.login = tk.Button(self, text='LOGIN', width=30, command=self.login).grid(row=5, column=0, columnspan = 2, pady=25)
        self.reloadFunctions = tk.Button(self, text='Developer - reload functions', width=30, command=self.reloadfunctions).grid(row=6, column=0, columnspan=2)



    def add_player_futbin(self):
        futbin_url = self.futbinlink_text.get()

        self.queue = queue.Queue()
        thread_runner.RunThread(self.queue, self.controller.mainbuttons.driver, "getFutbinDataFromURL", futbin_url).start()
        log_event("Added player to player list")
        self.update_list()

    def update_list(self):
        for i in self.controller.table.router_tree_view.get_children():
            self.controller.table.router_tree_view.delete(i)

        txt = open("./data/player_list.txt", "r", encoding="utf8")

        self.playerlist = []
        for aline in txt:
            values2 = aline.strip("\n").split(",")
            self.playerlist.append(values2)
            self.controller.table.router_tree_view.insert('', 'end', values=values2)
        txt.close()
        self.after(1000, self.update_list)

    def remove_player(self):
        index = self.controller.table.router_tree_view.selection()[0]
        selected_item = self.controller.table.router_tree_view.item(index)['values']

        item_to_remove = ""
        for word in selected_item:
            item_to_remove = item_to_remove + str(word) + ","

        item_to_remove = item_to_remove[:-1]

        with open("./data/player_list.txt", "r", encoding="utf8") as f:
            lines = f.readlines()
        with open("./data/player_list.txt", "w", encoding="utf8") as f:
            for line in lines:
                if line.strip("\n") != item_to_remove.strip("\n"):
                    f.write(line)
        self.update_list()

    def login(self):
        # self.progress()
        # self.prog_bar.start()
        self.queue = queue.Queue()

        login_exists = path.exists("./data/logins.txt")
        if login_exists:
            log_event("Auto logging in using credentials")
            thread_runner.RunThread(self.queue, self.controller.mainbuttons.driver, "login", self.controller.playerfilters.playerlist).start()
        else:
            log_event("Auto login credentials not found, login manually!")
            self.popupmsg("Logins.txt not found, login manually!")
   
        self.after(100, self.process_queue)

    def popupmsg(self, msg):
        popup = tk.Tk()
        popup.wm_title("Auto login error")
        label = ttk.Label(popup, text=msg, font=NORM_FONT)
        label.pack(side="top", fill="x", pady=10)
        B1 = ttk.Button(popup, text="Okay", command = popup.destroy)
        B1.pack()
        popup.mainloop()

    def reloadfunctions(self):
            # self.progress()
            # self.prog_bar.start()
            self.queue = queue.Queue()
            importlib.reload(thread_runner)
            importlib.reload(autobidder)
            importlib.reload(helpers)
            importlib.reload(mainhelpers)
            importlib.reload(newhelpers)
            # importlib.reload(autobidder_any)
            # importlib.reload(autobidder_list)
            # importlib.reload(function_runner)


# Top right
class Table(tk.Frame):

    def __init__(self, parent, controller):

        self.parent = parent
        self.controller = controller

        tk.Frame.__init__(self, parent)

        self.status = tk.Label(self, text="Status Displayed Here", font=LARGE_FONT)
        self.status.grid(row = 0, column = 0)

        # Player list table
        # columns = ['id', 'Playername', 'Overall', 'Buy price', 'Sell price']
        columns = ["Name", "Card name", "Rating", "Team", "Nation", "Type", "Position", "Internal ID", "Futbin ID", "Futbin Price", "Futbin LastUpdated", "Actual Market Price", "Buy %", "Max Price to pay"]

        self.router_tree_view = Treeview(self, columns=columns, show="headings")
        # self.router_tree_view.column("id", width=30)

        for col in columns[1:]:
            self.router_tree_view.column(col, width=40)
            self.router_tree_view.heading(col, text=col)

        #router_tree_view.bind('<<TreeviewSelect>>', select_router)
        self.router_tree_view.grid(row=1,column=0)

        # LOAD IN TABLE
        txt = open("./data/player_list.txt", "r", encoding="utf8")

        self.playerlist = self.controller.playerfilters.playerlist

        #self.playerlist = []
        for aline in txt:
            values2 = aline.strip("\n").split(",")
            self.playerlist.append(values2)
            self.router_tree_view.insert('', 'end', values=values2)
        txt.close()

# Bottom left
class MainButtons(tk.Frame):

    def __init__(self, parent, controller):

        self.parent = parent
        self.controller = controller

        # ~ ~ ~ ~ INITIATE BOT ~ ~ ~ ~ ~
        log_event(" - - - - Bot started - - - - ")
        self.driver = create_driver()
        self.action = ActionChains(self.driver)
        self.driver.get(URL)

        tk.Frame.__init__(self, parent)
        self.playerlist = self.controller.playerfilters.playerlist

        # Create frame for autobidder and autobuyer within mainbots frame
        self.autobidder = tk.LabelFrame(self, text="Autobidder")
        self.autobuyer = tk.LabelFrame(self, text="Autobuyer")

        self.autobidder.grid(row=0, column=0)
        self.autobuyer.grid(row=0, column=1)

        # Load Autobidder stats
        autobidderstats_json = open('./data/autobidder_stats.json')
        json1_str = autobidderstats_json.read()
        autobidder_data = json.loads(json1_str)[0]
        
        self.autobidder_labels = []
        count = 0
        for key, value in autobidder_data.items():
            key = str(key) + ":"
            value = str(value)
            valuevar = tk.StringVar()
            valuevar.set('first')
            tk.Label(self.autobidder, text=key).grid(row=count, column=0, sticky = W)
            tk.Label(self.autobidder, textvariable=valuevar).grid(row=count, column=1)
            self.autobidder_labels.append(valuevar)
            count+=1

        # Load Autobuyer stats
        autobuyerstats_json = open('./data/autobuyer_stats.json')
        json2_str = autobuyerstats_json.read()
        autobuyer_data = json.loads(json2_str)[0]
        
        self.autobuyer_labels = []
        count = 0
        for key, value in autobuyer_data.items():
            key = str(key) + ":"
            value = str(value)
            valuevar = tk.StringVar()
            valuevar.set('yup')
            tk.Label(self.autobuyer, text=key).grid(row=count, column=0, sticky = W)
            tk.Label(self.autobuyer, textvariable=valuevar).grid(row=count, column=1)
            self.autobuyer_labels.append(valuevar)
            count+=1

        num_autobidder_labels = len(autobidder_data)
        num_autobuyer_labels = len(autobuyer_data)


        self.test2 = tk.Button(self.autobidder, text='Start Autobidder', width=15, command=self.startAutobidder).grid(row=num_autobidder_labels+1, column=0, columnspan = 2)
        self.test3 = tk.Button(self.autobuyer, text='Start Autobuyer', width=15, command=self.startAutobuyer).grid(row=num_autobuyer_labels+1, column=0, columnspan = 2)

        self.update_stat_labels()

    # Continuously updates log table, inefficient but it works
    def update_stat_labels(self):
        # Load Autobidder stats
        autobidderstats_json = open('./data/autobidder_stats.json')
        json1_str = autobidderstats_json.read()
        autobidder_data = json.loads(json1_str)[0]
        
        autobiddervals = []
        for key, value in autobidder_data.items():
            autobiddervals.append(value)

        # Load Autobuyer stats
        autobuyerstats_json = open('./data/autobuyer_stats.json')
        json2_str = autobuyerstats_json.read()
        autobuyer_data = json.loads(json2_str)[0]
        
        autobuyervals = []
        for key, value in autobuyer_data.items():
            autobuyervals.append(value)

        count = 0
        for label in self.autobidder_labels:
            val = label.get()
            label.set(autobiddervals[count])
            count+=1
        
        count = 0
        for label in self.autobuyer_labels:
            val = label.get()
            label.set(autobuyervals[count])
            count+=1

        self.after(100, self.update_stat_labels)

    # These functions are called on button press
    def testfunc(self):
        # self.progress()
        # self.prog_bar.start()
        self.queue = queue.Queue()
        thread_runner.RunThread(self.queue, self.driver, "test", self.controller.playerfilters.playerlist).start()
        self.after(100, self.process_queue)

    def startAutobidder(self):
            # self.progress()
            # self.prog_bar.start()
            self.queue = queue.Queue()
            thread_runner.RunThread(self.queue, self.driver, "autobidder", self.controller.playerfilters.playerlist).start()
            self.after(100, self.process_queue)

    def startAutobuyer(self):
            # self.progress()
            # self.prog_bar.start()
            self.queue = queue.Queue()
            thread_runner.RunThread(self.queue, self.driver, "autobuyer", self.controller.playerfilters.playerlist).start()
            self.after(100, self.process_queue)

    def reloadfunctions(self):
        # self.progress()
        # self.prog_bar.start()
        self.queue = queue.Queue()
        importlib.reload(thread_runner)
        importlib.reload(autobidder)
        importlib.reload(helpers)
        importlib.reload(mainhelpers)
        importlib.reload(newhelpers)
        # importlib.reload(autobidder_any)
        # importlib.reload(autobidder_list)
        # importlib.reload(function_runner)

        self.after(100, self.process_queue)

    def process_queue(self):
        try:
            msg = self.queue.get(0)
            # print("QUEUE MESSAGE IS!!!:  " + str(msg))
            self.controller.table.status["text"] = str(msg)
            # Show result of the task if needed
            # self.prog_bar.stop()
        except queue.Empty:
            self.after(100, self.process_queue)

    # def login(self):
    #     self.progress()
    #     self.prog_bar.start()
    #     self.queue = queue.Queue()

    #     login_exists = path.exists("./data/logins.txt")
    #     if login_exists:
    #         log_event("Auto logging in using credentials")
    #         thread_runner.RunThread(self.queue, self.driver, "login", self.controller.playerfilters.playerlist).start()
    #     else:
    #         log_event("Auto login credentials not found, login manually!")
    #         self.popupmsg("Logins.txt not found, login manually!")
   
    #     self.after(100, self.process_queue)

    # def popupmsg(self, msg):
    #     popup = tk.Tk()
    #     popup.wm_title("!")
    #     label = ttk.Label(popup, text=msg, font=NORM_FONT)
    #     label.pack(side="top", fill="x", pady=10)
    #     B1 = ttk.Button(popup, text="Okay", command = popup.destroy)
    #     B1.pack()
    #     popup.mainloop()

    # def bidUsingList(self):
    #     self.progress()
    #     self.prog_bar.start()
    #     self.queue = queue.Queue()
    #     thread_runner.RunThread(self.queue, self.driver, "bidusinglist", self.controller.playerfilters.playerlist).start()
    #     self.after(100, self.process_queue)

    # def bidAnyone(self):
    #     self.progress()
    #     self.prog_bar.start()
    #     self.queue = queue.Queue()
    #     thread_runner.RunThread(self.queue, self.driver, "bidanyone", self.controller.playerfilters.playerlist).start()
    #     self.after(100, self.process_queue)

    # def progress(self):
    #     self.prog_bar = ttk.Progressbar(
    #         self, orient="horizontal",
    #         length=200, mode="indeterminate"
    #         )
    #     self.prog_bar.grid(row = 8, column = 3)

# Bottom right
class DisplayLogs(tk.Frame):

    def __init__(self, parent, controller):

        self.parent = parent
        self.controller = controller

        tk.Frame.__init__(self, parent)

        self.status2 = tk.Label(self, text="Logs", font=LARGE_FONT)
        self.status2.grid(row = 0, column = 0)

        # Player list table
        columns = ['log']
        self.loggings = Treeview(self, columns=columns, show="headings")
        self.loggings.column("log", width=640)

        for col in columns[1:]:
            self.loggings.column(col, width=400)
            self.loggings.heading(col, text=col)

        #loggings.bind('<<TreeviewSelect>>', select_router)
        self.loggings.grid(row=1,column=0)

        # LOAD IN TABLE
        txt = open("./data/logs.txt", "r")

        #self.playerlist = []
        for aline in txt:
            values2 = aline.strip("\n").split(",")
            self.loggings.insert('', 'end', values=values2)

        self.update_logs()

    # Continuously updates log table
    def update_logs(self):
        for i in self.loggings.get_children():
            self.loggings.delete(i)

        txt = open("./data/logs.txt", "r")

        self.playerlist = []
        for aline in txt:
            values2 = aline.strip("\n").split(",")
            self.loggings.insert('', 'end', values=values2)
        txt.close()
        self.loggings.yview_moveto(1)
        self.after(100, self.update_logs)


# - - - - - - Deprecated - - - - - -
class Logins(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self,parent)

        self.controller = controller
        self.parent = parent

        # GET LOGIN CREDENTIALS
        txt = open("logins.txt", "r")
        counter = 0

        credentials = []
        for aline in txt:
            counter+=1
            line = aline.strip("\n")
            credentials.append(str(line))
        txt.close()

        # Email
        email_text = tk.StringVar()
        email_label = tk.Label(self, text='EA Login', font=LARGE_FONT)
        email_entry = tk.Entry(self, textvariable=email_text, show="*")

        email_label.grid(row=1, column = 0)
        email_entry.grid(row=1, column = 1)

        # Password
        ea_password_text = tk.StringVar()
        ea_password_label = tk.Label(self, text='EA Password', font=LARGE_FONT)
        ea_password_entry = tk.Entry(self, textvariable=ea_password_text, show="*")

        ea_password_label.grid(row=2, column = 0)
        ea_password_entry.grid(row=2, column = 1)

        # BLANK space
        blankspace = tk.Label(self, text='', font=LARGE_FONT).grid(row=3, column = 0)

        # Gmail Login
        gmail_text = tk.StringVar()
        gmail_label = tk.Label(self, text='Gmail Login (2FA)', font=LARGE_FONT)
        gmail_entry = tk.Entry(self, textvariable=gmail_text, show="*")

        gmail_label.grid(row=4, column = 0)
        gmail_entry.grid(row=4, column = 1)

        # Gmail Password
        gmail_password_text = tk.StringVar()
        gmail_password_label = tk.Label(self, text='Gmail Password', font=LARGE_FONT)
        gmail_password_entry = tk.Entry(self, textvariable=gmail_password_text, show="*")

        gmail_password_label.grid(row=5, column = 0)
        gmail_password_entry.grid(row=5, column = 1)

        # BLANK space
        blankspace2 = tk.Label(self, text='', font=LARGE_FONT).grid(row=6, column = 0)

        email_entry.insert(END, credentials[0])
        ea_password_entry.insert(END, credentials[1])
        gmail_entry.insert(END, credentials[2])
        gmail_password_entry.insert(END, credentials[3])

        # Save changes to passwords.txt
        self.savelogins = tk.Button(self, text='Save Logins', width=12, command=self.updatelogins).grid(row=6, column=1)
        blankspace2 = tk.Label(self, text='', font=LARGE_FONT).grid(row=7, column = 0)
        blankspace3 = tk.Label(self, text='', font=LARGE_FONT).grid(row=8, column = 0)


    def updatelogins(self):
        print("too lazy to do this, go into passwords.txt and manually do it")
        msg = "this doesn't work lol"
        self.controller.table.status["text"] = str(msg)


app = GUI()
app.mainloop()
