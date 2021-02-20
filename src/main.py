import thread_runner
# import function_runner
import mainhelpers
import helpers
import newhelpers
import autobidder_any
import autobidder
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

LARGE_FONT= ("Verdana", 12)
SMALL_FONT = ("Verdana", 8)
NORM_FONT = ("Helvetica", 10)


class SeaofBTCapp(tk.Tk):

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

        # Add players box
        self.playerfilters.grid(row=0, column=0, sticky="nsew", padx="10", pady="10")

        # Player input list box
        self.table.grid(row=0, column=1, sticky="nsew", padx="10", pady="10")

        # Login / start bot / etc buttons
        self.mainbuttons.grid(row=1, column=0, sticky="nsew", padx="10", pady="10")

        # Log displayer
        self.displaylogs.grid(row=1, column=1, sticky="nsew", padx="10", pady="10")


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


class PlayerFilters(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        self.parent = parent
        self.controller = controller
        self.playerlist = []

        blankspacelabel = tk.Label(self, text=' - - - - ', font=LARGE_FONT)
        blankspacelabel.grid(row=13, column=0)

        futbinlink_text = tk.StringVar()
        futbinlink_label = tk.Label(self, text='Player Futbin URL: ', font=LARGE_FONT)
        futbin_entry = tk.Entry(self, textvariable=futbinlink_text)

        futbinlink_label.grid(row=14, column=0)
        futbin_entry.grid(row=14, column=1)

        
        self.add_btn_futbin = tk.Button(self, text='Add Player', width=12, command=self.add_player_futbin)
        self.add_btn_futbin.grid(row=15, column=0)

        self.remove_btn = tk.Button(self, text='Remove Player', width=12, command=self.remove_player)
        self.remove_btn.grid(row=15, column=1)


        disclaimer2 = tk.StringVar()
        disclaimer_text2 = tk.Label(self, text='Futbin price will be used as truth in initial searches, during which market data will be collected and analyzed to find accurate market price!', font=SMALL_FONT, wraplength=400)
        disclaimer_text2.grid(row=16, column=0, columnspan=2)

        autobid_pct_text = tk.StringVar()
        autobid_pct_label = tk.Label(self, text='Autobid up to %: ', font=SMALL_FONT)
        autobid_pct_entry = tk.Entry(self, textvariable=autobid_pct_text)

        autobid_pct_label.grid(row=18, column=0)
        autobid_pct_entry.grid(row=18, column=1)


        autobuy_pct_text = tk.StringVar()
        autobuy_pct_label = tk.Label(self, text='Autobuy up to %: ', font=SMALL_FONT)
        autobuy_pct_entry = tk.Entry(self, textvariable=autobuy_pct_text)

        autobuy_pct_label.grid(row=19, column=0)
        autobuy_pct_entry.grid(row=19, column=1)

        self.futbinlink_text = futbinlink_text


    # def add_player(self):
    #     val = [0, ",", self.player_text.get(), ",", self.overall_text.get(), ",", self.buyprice_text.get(), ",", self.sellprice_text.get()]

    #     full_entry = ""
    #     for word in val:
    #         full_entry += str(word)
    #     hs = open("./data/player_list.txt", "a", encoding="utf8")
    #     hs.write(full_entry + "\n")
    #     hs.close()
    #     self.update_list()

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


class Table(tk.Frame):

    def __init__(self, parent, controller):

        self.parent = parent
        self.controller = controller

        tk.Frame.__init__(self, parent)

        self.status = tk.Label(self, text="Status Displayed Here", font=LARGE_FONT)
        self.status.grid(row = 0, column = 0)

        # Player list table
        # columns = ['id', 'Playername', 'Overall', 'Buy price', 'Sell price']
        columns = ["Name", "Name on Card", "Rating", "Team", "Nation", "Type", "Position", "Internal ID", "Futbin ID", "Futbin Price", "Futbin LastUpdated", "Actual Market Price", "Buy %", "Max Price to pay"]

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


class MainButtons(tk.Frame):

    def __init__(self, parent, controller):

        self.parent = parent
        self.controller = controller

        # ~ ~ ~ ~ INITIATE BOT ~ ~ ~ ~ ~
        log_event(" - - - - Bot started - - - - ")
        self.driver = create_driver()
        self.action = ActionChains(self.driver)
        self.driver.get(URL)

        self.masterlist = []

        tk.Frame.__init__(self, parent)

        self.login = tk.Button(self, text='LOGIN', width=30, command=self.login).grid(row=3, column=1)
        self.blankspace6 = tk.Label(self, text=' ', font=LARGE_FONT).grid(row=4, column=1)
        self.bidlist = tk.Button(self, text='Autobidder [input list]', width=30, command=self.bidUsingList).grid(row=5, column=1)
        self.bidanyone = tk.Button(self, text='Autobidder [any golds]', width=30, command=self.bidAnyone).grid(row=6, column=1)
        self.blankspace7 = tk.Label(self, text=' - - - ', font=LARGE_FONT).grid(row=7, column=1)

        self.reloadFunctions = tk.Button(self, text='Developer - reload functions', width=30, command=self.reloadfunctions).grid(row=8, column=1)
        self.test2 = tk.Button(self, text='Developer - Test Function', width=30, command=self.testfunc).grid(row=9, column=1)

        # # Blank space
        self.blankspace3 = tk.Label(self, text='', font=LARGE_FONT).grid(row=0, column=1)

        self.playerlist = self.controller.playerfilters.playerlist

    def login(self):
        self.progress()
        self.prog_bar.start()
        self.queue = queue.Queue()

        login_exists = path.exists("./data/logins.txt")
        if login_exists:
            log_event("Auto logging in using credentials")
            thread_runner.RunThread(self.queue, self.driver, "login", self.controller.playerfilters.playerlist).start()
        else:
            log_event("Auto login credentials not found, login manually!")
            self.popupmsg("Logins.txt not found, login manually!")
   
        self.after(100, self.process_queue)

    def popupmsg(self, msg):
        popup = tk.Tk()
        popup.wm_title("!")
        label = ttk.Label(popup, text=msg, font=NORM_FONT)
        label.pack(side="top", fill="x", pady=10)
        B1 = ttk.Button(popup, text="Okay", command = popup.destroy)
        B1.pack()
        popup.mainloop()

    def bidUsingList(self):
        self.progress()
        self.prog_bar.start()
        self.queue = queue.Queue()
        thread_runner.RunThread(self.queue, self.driver, "bidusinglist", self.controller.playerfilters.playerlist).start()
        self.after(100, self.process_queue)

    def bidAnyone(self):
        self.progress()
        self.prog_bar.start()
        self.queue = queue.Queue()
        thread_runner.RunThread(self.queue, self.driver, "bidanyone", self.controller.playerfilters.playerlist).start()
        self.after(100, self.process_queue)

    # These functions are called on button press
    def testfunc(self):
        self.progress()
        self.prog_bar.start()
        self.queue = queue.Queue()
        thread_runner.RunThread(self.queue, self.driver, "test", self.controller.playerfilters.playerlist).start()
        self.after(100, self.process_queue)

    def reloadfunctions(self):
        self.progress()
        self.prog_bar.start()
        self.queue = queue.Queue()
        importlib.reload(thread_runner)
        importlib.reload(autobidder)
        # importlib.reload(function_runner)

        importlib.reload(helpers)
        importlib.reload(mainhelpers)
        importlib.reload(newhelpers)
        importlib.reload(autobidder_any)
        # importlib.reload(autobidder_list)

        self.after(100, self.process_queue)




    def process_queue(self):
        try:
            msg = self.queue.get(0)
            print("QUEUE MESSAGE IS!!!:  " + str(msg))
            self.controller.table.status["text"] = str(msg)
            # Show result of the task if needed
            self.prog_bar.stop()
        except queue.Empty:
            self.after(100, self.process_queue)

    def progress(self):
        self.prog_bar = ttk.Progressbar(
            self, orient="horizontal",
            length=200, mode="indeterminate"
            )
        self.prog_bar.grid(row = 8, column = 3)

app = SeaofBTCapp()
app.mainloop()
