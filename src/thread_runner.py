import os.path
import threading
from os import path

import autobidder
import autobuyer
import helpers
from autobidder import Autobidder
from autobuyer import Autobuyer
from helpers import *


# Each button starts a new thread
class RunThread(threading.Thread):
    def __init__(self, queue, driver, action, auxiliary, futbinurl):
        threading.Thread.__init__(self)
        self.action = action
        self.queue = queue

        # auxiliary = parent autobidder object
        self.auxiliary = auxiliary
        self.driver = driver
        self.futbinurl = futbinurl

        self.parentAutobidder = auxiliary

        self.firstStart = futbinurl
        # put all threads in try except and on exception, have it remember the gui logs..
        # simply add a variable to autobidder True or False whether it is the bots first start
        # on start of GUI, make the variable True. once Start autobidder is clicked, it is False 

        # maybe create Helper object in GUI class 
        # if object throws exception does it lose its class variables?
        # if not, helper obj created on init 


    def run(self):
        if self.action == "autobidder":
            self.queue.put("Starting autobidder")

            if self.firstStart:
                self.parentAutobidder.initializeBot()

            else:
                self.parentAutobidder.start()
            # try:
            #     self.parentAutobidder.start()
            # except:
            #     log_event(self.queue, "THREAD KILLED!")
            #     # If user intereferes etc., kill thread
            #     self.prog_bar.stop()
            # # autobidder = Autobidder(self.driver, self.queue)
            # autobidder.initializeBot()

        if self.action == "autobidder_devmode":
            self.queue.put("Starting autobidder - dev mode")
            autobidder = Autobidder(self.driver, self.queue)
            autobidder.checkTransferlist()

        if self.action == "watchlist":
            self.queue.put("Managing watchlist")
            self.auxiliary.manageWatchlist()

        if self.action == "autobuyer":
            self.queue.put("Starting autobuyer")

        if self.action == "login":
            self.queue.put("Logging in")
            
            txt = open("./data/logins.txt", "r")
            counter = 0
            credentials = []
            for aline in txt:
                counter += 1
                line = aline.strip("\n")
                credentials.append(str(line))
            txt.close()

            USER = {
                "email": credentials[0],
                "password": credentials[1],
            }

            EMAIL_CREDENTIALS = {
                "email": credentials[2],
                "password": credentials[3],
            }

            login(self.driver, USER, EMAIL_CREDENTIALS)
            # Set user's starting coins
            # self.auxiliary.helper.setStartingCoins()

        if self.action == "getFutbinDataFromURL":
            self.queue.put("Fetching player info")
            log_event(self.queue, "Fetching player info...")

            # helper = Helper(self.driver)
            helper.getFutbinDataAndPopulateTable(self.futbinurl)

        if self.action == "test":
            self.queue.put("Running test function")

            autobidder.manageWatchlist()
