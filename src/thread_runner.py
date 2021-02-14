import function_runner
import mainhelpers
import helpers

from function_runner import RunFunction
import threading


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
            self.runner.login()

        if self.action == "bidusinglist":
            self.queue.put("Bidding using player list")
            self.runner.bidAnyone("playerlist")

        if self.action == "bidanyone":
            self.queue.put("Bidding on Common Golds")
            self.runner.bidAnyone("GUIfilters")

        if self.action == "test":
            self.queue.put("Test button")
            self.runner.test()
