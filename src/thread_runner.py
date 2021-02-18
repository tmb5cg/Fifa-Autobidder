import function_runner
import mainhelpers
import helpers

from helpers import *
from mainhelpers import *
from function_runner import RunFunction
import threading
import os.path
from os import path


# Each button starts a new thread
class RunThread(threading.Thread):
    def __init__(self, queue, driver, action, searchdata):
        threading.Thread.__init__(self)
        self.action = action
        self.queue = queue
        self.searchdata = searchdata
        self.driver = driver
        self.runner = RunFunction(self.driver, self.searchdata)

    def run(self):
        if self.action == "login":
            self.queue.put("Logging in")

            print("AutoLogin credentials exist. Not guaranteed they are formatted correctly, but they exist")
            log_event("AutoLogin credentials exist. Not guaranteed they are formatted correctly, but they exist")
            self.runner.login()



        if self.action == "getFutbinDataFromURL":
            self.queue.put("Fetching player info")
            # self.searchdata in this case is actually the futbin URL, this entire structure needs to be rewritten!
            # too convoluted going from thread funner --> function runner. 
            # This thread runner does the work that is needed and can dispatch functions on its own
            self.runner.getFutbinInfo()


        if self.action == "bidusinglist":
            self.queue.put("Bidding using player list")
            self.runner.bidAnyone("playerlist")

        if self.action == "bidanyone":
            self.queue.put("Bidding on Common Golds")
            self.runner.bidAnyone("GUIfilters")

        if self.action == "test":
            self.queue.put("Test button")
            self.runner.test()
