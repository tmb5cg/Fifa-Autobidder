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
    def __init__(self, queue, driver, action, searchdata):
        threading.Thread.__init__(self)
        self.action = action
        self.queue = queue
        self.searchdata = searchdata
        self.driver = driver
        # self.runner = RunFunction(self.driver, self.searchdata)

    def run(self):
        if self.action == "test":
            self.queue.put("Running test function")
            # log_event("Test function")

            autobidder = Autobidder(self.driver, self.queue)
            autobidder.manageWatchlist()

        if self.action == "autobidder":
            self.queue.put("Starting autobidder")
            log_event("Test function")
            
            # testhelper = Helper(self.driver)

            # testhelper.start()
            autobidder = Autobidder(self.driver, self.queue)
            autobidder.manageWatchlist()

        if self.action == "autobuyer":
            self.queue.put("Starting autobuyer")
            # log_event("Test function")

            autobuyer = Autobuyer(self.driver, self.queue)
            autobuyer.start()

        if self.action == "login":
            self.queue.put("Logging in")
            # log_event("AutoLogin...")
            
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


        if self.action == "getFutbinDataFromURL":
            self.queue.put("Fetching player info")
            log_event("Fetching player info...")

            futbin_url = self.searchdata
            self.helper = Helper(self.driver)
            self.helper.getFutbinDataAndPopulateTable(futbin_url)

















        if self.action == "bidusinglist":
            self.queue.put("Bidding using player list")
            # log_event("Starting autobidder")

            # autobidder = AutobidderAny(self.driver, self.searchdata)
            # autobidder.run("playerlist")

        if self.action == "bidanyone":
            self.queue.put("Bidding on Common Golds")
            # autobidder = AutobidderAny(self.driver, self.searchdata)
            # autobidder.run("playerlist")
