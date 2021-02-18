import thread_runner
import function_runner
import mainhelpers
import helpers
import autobidder_any
import autobidder_list

from config import create_driver, URL
from thread_runner import RunThread
from function_runner import RunFunction
from helpers import *
from mainhelpers import *

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

        self.logins = Logins(self.container, self)
        self.playerfilters = PlayerFilters(self.container, self)
        self.table = Table(self.container, self)
        self.mainbuttons = MainButtons(self.container, self)
        self.displaylogs = DisplayLogs(self.container, self)

        self.logins.grid(row=1, column=0, sticky="nsew", padx="10", pady="10")
        self.playerfilters.grid(row=0, column=0, sticky="nsew", padx="10", pady="10")
        self.table.grid(row=0, column=1, sticky="nsew", padx="10", pady="10")
        self.mainbuttons.grid(row=1, column=1, sticky="nsew", padx="10", pady="10")

        self.displaylogs.grid(row=2, column=0, sticky="nsew", padx="10", pady="10")


class DisplayLogs(tk.Frame):

    def __init__(self, parent, controller):

        self.parent = parent
        self.controller = controller

        tk.Frame.__init__(self, parent)

        self.status2 = tk.Label(self, text="Bot Logs", font=LARGE_FONT)
        self.status2.grid(row = 0, column = 0)

        # Player list table
        columns = ['log']
        self.loggings = Treeview(self, columns=columns, show="headings")
        self.loggings.column("log", width=200)

        for col in columns[1:]:
            self.loggings.column(col, width=200)
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


        # self.parent = parent
        # self.controller = controller

        # tk.Frame.__init__(self, parent)

        # self.logs = tk.Label(self, text="Logs", font=LARGE_FONT)
        # self.logs.grid(row = 0, column = 0)

        # self.text = Text(self, height=20, setgrid=True, wrap=WORD, undo=True, pady=2, padx=3)
        # xscroll = ttk.Scrollbar(self, command=self.text.xview, orient=HORIZONTAL)
        # yscroll = ttk.Scrollbar(self, command=self.text.yview, orient=VERTICAL)
        # self.text.configure(xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)

        # self.text.grid(row=0, column=0, sticky=NSEW)
        # yscroll.grid(row=0, column=1, sticky=NSEW)
        # self.rowconfigure(0, weight=1)
        # self.columnconfigure(0, weight=1)
        

        # # Player list table
        # # columns = ['id', 'Playername', 'Overall', 'Buy price', 'Sell price']
        # # self.router_tree_view = Treeview(self, columns=columns, show="headings")
        # # self.router_tree_view.column("id", width=30)

        # # for col in columns[1:]:
        # #     self.router_tree_view.column(col, width=80)
        # #     self.router_tree_view.heading(col, text=col)

        # # #router_tree_view.bind('<<TreeviewSelect>>', select_router)
        # # self.router_tree_view.grid(row=1,column=0)

        # # LOAD IN TABLE
        # txt = open("./data/logs.txt", "r")
        # self.text = txt
        # # for aline in txt:
        # #     values2 = aline.strip("\n").split(",")
        # #     # self.text.insert('', 'end', values=values2)
        # #     self.text.insert(END, ''.join(txt))
        # txt.close()




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

        # # FUTBIN Link
        # futbin_text = tk.StringVar()
        # futbin_label = tk.Label(self, text='Futbin link: ', font=LARGE_FONT)
        # futbin_entry = tk.Entry(self, textvariable=futbin_text)

        # futbin_label.grid(row=7, column=0)
        # futbin_entry.grid(row=7, column=1)

        # Player name
        # player_text = tk.StringVar()
        # player_label = tk.Label(self, text='Player name', font=LARGE_FONT)
        # player_entry = tk.Entry(self, textvariable=player_text)

        # player_label.grid(row=8, column=0)
        # player_entry.grid(row=8, column=1)

        # # Buy price
        # overall_text = tk.StringVar()
        # overall_label = tk.Label(self, text='Player Overall', font=LARGE_FONT)
        # overall_entry = tk.Entry(self, textvariable=overall_text)

        # overall_label.grid(row=9, column=0)
        # overall_entry.grid(row=9, column=1)

        # # Buy price
        # buyprice_text = tk.StringVar()
        # buyprice_label = tk.Label(self, text='Buy Price', font=LARGE_FONT)
        # buyprice_entry = tk.Entry(self, textvariable=buyprice_text)

        # buyprice_label.grid(row=10, column=0)
        # buyprice_entry.grid(row=10, column=1)

        # # Sell price
        # sellprice_text = tk.StringVar()
        # sellprice_label = tk.Label(self, text='Sell Price', font=LARGE_FONT)
        # sellprice_entry = tk.Entry(self, textvariable=sellprice_text)

        # sellprice_label.grid(row=11, column=0)
        # sellprice_entry.grid(row=11, column=1)


        # BUTTONS
        # self.add_btn = tk.Button(self, text='Add Player', width=12, command=self.add_player)
        # self.add_btn.grid(row=12, column=0)
        # self.remove_btn = tk.Button(self, text='Remove Player', width=12, command=self.remove_player)
        # self.remove_btn.grid(row=12, column=1)

        # self.overall_text = overall_text
        # self.player_text = player_text
        # self.buyprice_text = buyprice_text
        # self.sellprice_text = sellprice_text



        # FUTBIN Link entry -- new UI simplified 
        # blank space


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


        # disclaimer1 = tk.StringVar()
        # disclaimer_text1 = tk.Label(self, text='Enter Futbin URL to gather player data', font=SMALL_FONT)
        # disclaimer_text1.grid(row=12, column=0)

        # disclaimer2 = tk.StringVar()
        # disclaimer_text2 = tk.Label(self, text='Note: Futbin price will be used as truth in initial searches, during which market data will be collected and analyzed to find accurate market price!', font=SMALL_FONT, wraplength=400)
        # disclaimer_text2.grid(row=16, column=0)

        self.futbinlink_text = futbinlink_text


    def add_player(self):
        val = [0, ",", self.player_text.get(), ",", self.overall_text.get(), ",", self.buyprice_text.get(), ",", self.sellprice_text.get()]

        full_entry = ""
        for word in val:
            full_entry += str(word)
        hs = open("./data/user_playerlist_GUI.txt", "a", encoding="utf8")
        hs.write(full_entry + "\n")
        hs.close()
        self.update_list()

    def add_player_futbin(self):
        futbin_url = self.futbinlink_text.get()

        self.queue = queue.Queue()
        thread_runner.RunThread(self.queue, self.controller.mainbuttons.driver, "getFutbinDataFromURL", futbin_url).start()
        self.update_list()


    def update_list(self):
        for i in self.controller.table.router_tree_view.get_children():
            self.controller.table.router_tree_view.delete(i)

        txt = open("./data/user_playerlist_GUI.txt", "r", encoding="utf8")

        self.playerlist = []
        for aline in txt:
            values2 = aline.strip("\n").split(",")
            self.playerlist.append(values2)
            self.controller.table.router_tree_view.insert('', 'end', values=values2)
        txt.close()
        self.after(100, self.update_list)


    def remove_player(self):
        index = self.controller.table.router_tree_view.selection()[0]
        selected_item = self.controller.table.router_tree_view.item(index)['values']

        item_to_remove = ""
        for word in selected_item:
            item_to_remove = item_to_remove + str(word) + ","

        item_to_remove = item_to_remove[:-1]

        with open("./data/user_playerlist_GUI.txt", "r", encoding="utf8") as f:
            lines = f.readlines()
        with open("./data/user_playerlist_GUI.txt", "w", encoding="utf8") as f:
            for line in lines:
                if line.strip("\n") != item_to_remove.strip("\n"):
                    f.write(line)
        self.update_list()


class Table(tk.Frame):

    def __init__(self, parent, controller):

        self.parent = parent
        self.controller = controller

        tk.Frame.__init__(self, parent)

        self.status = tk.Label(self, text="Bot Status Displayed Here", font=LARGE_FONT)
        self.status.grid(row = 0, column = 0)

        # Player list table
        # columns = ['id', 'Playername', 'Overall', 'Buy price', 'Sell price']
        columns = ["Name", "Card name", "Rating", "Team", "Nation", "Type", "Position", "Internal ID", "Futbin ID", "Futbin Price", "Futbin LastUpdated", "Actual Market Price"]

        self.router_tree_view = Treeview(self, columns=columns, show="headings")
        # self.router_tree_view.column("id", width=30)

        for col in columns[1:]:
            self.router_tree_view.column(col, width=80)
            self.router_tree_view.heading(col, text=col)

        #router_tree_view.bind('<<TreeviewSelect>>', select_router)
        self.router_tree_view.grid(row=1,column=0)

        # LOAD IN TABLE
        txt = open("./data/user_playerlist_GUI.txt", "r", encoding="utf8")

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
            print("login file exists!")
            log_event("Auto logging in using credentials")
            thread_runner.RunThread(self.queue, self.driver, "login", self.controller.playerfilters.playerlist).start()
        else:
            print("Login file does NOT exists!")
            log_event("Auto login credentials not found, login manually!")
            self.popupmsg("Logins.txt not found, login manually!")
        # autologin_status = thread_runner.RunThread(self.queue, self.driver, "checkCredentials", self.controller.playerfilters.playerlist).start()

        # if autologin_status == "True":
        #     thread_runner.RunThread(self.queue, self.driver, "login", self.controller.playerfilters.playerlist).start()
        # elif autologin_status == "False":
        #     print("login manually. create message box saying must login manually")

        # result = thread_runner.RunThread(self.queue, self.driver, "login", self.controller.playerfilters.playerlist).start()
        # if (result == True):
        #     print("success")
        # if (result == False):
        #     print("credentials not listed")
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
        importlib.reload(function_runner)

        importlib.reload(helpers)
        importlib.reload(mainhelpers)

        importlib.reload(autobidder_any)
        importlib.reload(autobidder_list)

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
