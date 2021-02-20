import mainhelpers
import helpers
import autobidder_any
import autobidder

from helpers import *
from mainhelpers import *

from autobidder import Autobidder
from autobidder_any import AutobidderAny

from config import USER
import threading
import os.path
from os import path

# from autobidder_list import AutobidderPlayerlist
# import function_runner
# import autobidder_list



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
            self.queue.put("Test button")
            log_event("Test function")

            autobidder = Autobidder(self.driver)
            autobidder.start()














        if self.action == "login":
            self.queue.put("Logging in")
            log_event("AutoLogin...")

            login(self.driver, USER)


        if self.action == "getFutbinDataFromURL":
            self.queue.put("Fetching player info")
            log_event("Fetching player info")

            futbin_url = self.searchdata
            getFutbinDataAndPopulateTable(self.driver, futbin_url)


        if self.action == "bidusinglist":
            self.queue.put("Bidding using player list")
            log_event("Starting autobidder")

            autobidder = AutobidderAny(self.driver, self.searchdata)
            autobidder.run("playerlist")

        if self.action == "bidanyone":
            self.queue.put("Bidding on Common Golds")
            autobidder = AutobidderAny(self.driver, self.searchdata)
            autobidder.run("playerlist")
